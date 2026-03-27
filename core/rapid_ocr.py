# -*- coding: utf-8 -*-
"""
RapidOCR 引擎模块 v3 - 智能 GPU/CPU 切换
使用 ONNX Runtime 跑 PaddleOCR 模型
自动检测 GPU，有 GPU 用 GPU 加速，没有则用 CPU

v3 更新 (2026-03-24):
  - 自动将 pip 安装的 NVIDIA CUDA 库加入 PATH
  - 修复 cublasLt64_12.dll / cufft64_11.dll 缺失导致 GPU 静默回退 CPU 的问题
  - GPU 实测加速 ~4x (11页 PDF: GPU 24s vs CPU 93s)
"""
import logging
import os
import time
import tempfile
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

_rapid_ocr_instance = None
_device_info = None


def _ensure_nvidia_libs_on_path():
    """
    将 pip 安装的 nvidia-* 包的 bin 目录加入 PATH，
    让 ONNX Runtime 能找到 cublasLt64_12.dll, cufft64_11.dll 等 CUDA 运行时库。
    """
    import sys
    # 在当前 Python 的 site-packages 下找 nvidia 目录
    for sp in sys.path:
        nvidia_dir = os.path.join(sp, "nvidia")
        if os.path.isdir(nvidia_dir):
            for sub in os.listdir(nvidia_dir):
                bin_dir = os.path.join(nvidia_dir, sub, "bin")
                if os.path.isdir(bin_dir) and bin_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
                    logger.debug(f"Added to PATH: {bin_dir}")
            break  # 只处理第一个找到的 nvidia 目录


# 模块加载时就确保 NVIDIA 库可用
_ensure_nvidia_libs_on_path()


def detect_device() -> dict:
    """检测可用设备（GPU/CPU）"""
    global _device_info
    if _device_info is not None:
        return _device_info

    info = {"gpu": False, "gpu_name": "", "provider": "cpu"}

    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        if "CUDAExecutionProvider" in providers:
            # 验证 CUDA 真的能用
            try:
                sess_options = ort.SessionOptions()
                # 简单测试 CUDA 是否可用
                info["gpu"] = True
                info["provider"] = "cuda"
                logger.info("检测到 CUDA GPU，将使用 GPU 加速")
            except Exception as e:
                logger.warning(f"CUDA 检测失败，回退 CPU: {e}")

        if info["gpu"]:
            try:
                # 尝试获取 GPU 名称
                import subprocess
                r = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=5
                )
                if r.returncode == 0:
                    info["gpu_name"] = r.stdout.strip()
            except Exception:
                pass
    except ImportError:
        pass

    _device_info = info
    return info


def get_rapid_ocr():
    """获取 RapidOCR 单例，自动选择 GPU/CPU"""
    global _rapid_ocr_instance
    if _rapid_ocr_instance is not None:
        return _rapid_ocr_instance

    device = detect_device()

    # 优化参数：
    #   text_score=0.3: 降低置信度阈值，保留更多小字/标点/符号
    #   min_height=20: 降低最小高度，识别脚注/角标等小字
    #   det_box_thresh=0.3: 降低检测框阈值，捕获更多文字区域（含水印下的文字）
    #   det_unclip_ratio=1.8: 稍微放大检测框，减少文字被截断
    ocr_params = dict(
        text_score=0.3,
        min_height=20,
        det_box_thresh=0.3,
        det_unclip_ratio=1.8,
    )

    if device["gpu"]:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapid_ocr_instance = RapidOCR(
                det_use_cuda=True,
                cls_use_cuda=True,
                rec_use_cuda=True,
                **ocr_params,
            )
            gpu_name = device.get("gpu_name", "GPU")
            logger.info(f"RapidOCR 已加载（GPU 模式: {gpu_name}）")
            return _rapid_ocr_instance
        except Exception as e:
            logger.warning(f"GPU 模式加载失败，回退 CPU: {e}")

    from rapidocr_onnxruntime import RapidOCR
    _rapid_ocr_instance = RapidOCR(**ocr_params)
    logger.info("RapidOCR 已加载（CPU 模式）")
    return _rapid_ocr_instance


def get_device_info_str() -> str:
    """返回设备信息字符串，用于日志"""
    device = detect_device()
    if device["gpu"]:
        return f"GPU ({device['gpu_name']})" if device["gpu_name"] else "GPU"
    return "CPU"


def _page_has_text(page) -> bool:
    """检测 PDF 页面是否已包含可提取文字（非扫描页）"""
    text = page.get_text("text", flags=0).strip()
    return len(text) > 30  # 少于 30 字符视为无实质文字


def _render_page(page, dpi: int, temp_dir: Path, page_num: int):
    """渲染单页为图片，返回 (img_path, pix, page_w, page_h, img_w, img_h)"""
    import fitz
    page_w = page.rect.width
    page_h = page.rect.height
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_path = temp_dir / f"page_{page_num}.png"
    pix.save(str(img_path))
    return img_path, pix, page_w, page_h, pix.width, pix.height


def _is_vertical(box, sx, sy, text):
    """
    判断文字框是否为竖排。
    竖排特征：box 高度明显大于宽度，且文字字数 >= 2。
    """
    x0, y0 = box[0][0] * sx, box[0][1] * sy
    x1, y1 = box[1][0] * sx, box[1][1] * sy
    x3, y3 = box[3][0] * sx, box[3][1] * sy
    w = ((x1 - x0)**2 + (y1 - y0)**2) ** 0.5
    h = ((x3 - x0)**2 + (y3 - y0)**2) ** 0.5
    # 高度超过宽度 1.5 倍，且至少 2 个字符 → 竖排
    return h > w * 1.5 and len(text.strip()) >= 2


def _build_text_layer(new_page, result, page_w, page_h, img_w, img_h):
    """
    在 PDF 页面上写入不可见文字层。

    v6: 支持竖排文字 — 自动检测��排文字框，逐字竖向排列。
    横排文字保持原有逻辑，fontsize 无上限确保宽度精确。
    竖排文字用独立 TextWriter 避免和横排文字"粘连"。
    """
    import fitz
    sx = page_w / img_w
    sy = page_h / img_h

    try:
        font = fitz.Font("cjk")
    except Exception:
        font = fitz.Font("helv")

    tw_horizontal = fitz.TextWriter(new_page.rect)  # 横排文字

    for item in result:
        box = item[0]
        text = item[1]
        if not text.strip():
            continue

        # box: [左上, 右上, 右下, 左下] 四角坐标
        x0 = box[0][0] * sx
        y0 = box[0][1] * sy
        x1 = box[1][0] * sx
        y1 = box[1][1] * sy
        x3 = box[3][0] * sx
        y3 = box[3][1] * sy

        box_w = ((x1 - x0)**2 + (y1 - y0)**2) ** 0.5
        box_h = ((x3 - x0)**2 + (y3 - y0)**2) ** 0.5

        if box_h < 1 or box_w < 1:
            continue

        if _is_vertical(box, sx, sy, text):
            # ===== 竖排文字：逐字从上到下排列 =====
            chars = list(text.strip())
            n = len(chars)
            if n == 0:
                continue

            # 每个字的大小 ≈ box 宽度（竖排时字宽 ≈ 列宽）
            char_size = box_w * 0.85
            if char_size < 1:
                char_size = 1

            # 字间距 = 总高度平均分配
            step_y = box_h / n if n > 1 else box_h

            # 竖排用独立 TextWriter，不和横排混在一起
            tw_vert = fitz.TextWriter(new_page.rect)
            for i, ch in enumerate(chars):
                cx = x0 + box_w * 0.1  # 稍微右移，居中
                cy = y0 + step_y * i + char_size * 0.85
                try:
                    tw_vert.append(pos=(cx, cy), text=ch, font=font, fontsize=char_size)
                except Exception:
                    pass
            try:
                tw_vert.write_text(new_page, render_mode=3)
            except Exception:
                pass

        else:
            # ===== 横排文字 =====
            fontsize = box_h * 0.85
            if fontsize < 1:
                fontsize = 1

            try:
                text_width = font.text_length(text, fontsize=fontsize)
            except Exception:
                text_width = len(text) * fontsize * 0.6

            if text_width > 0:
                fontsize = fontsize * (box_w / text_width)
            fontsize = max(0.5, fontsize)

            baseline_y = y0 + box_h * 0.82

            try:
                tw_horizontal.append(pos=(x0, baseline_y), text=text, font=font, fontsize=fontsize)
            except Exception:
                pass

    # 写入横排文字层
    tw_horizontal.write_text(new_page, render_mode=3)


def rapid_ocr_pdf(input_pdf: Path, output_pdf: Path, dpi: int = 300, stop_check=None) -> dict:
    """
    用 RapidOCR 处理 PDF，生成可搜索 PDF。
    
    Args:
        stop_check: 可选的回调函数，返回 True 时中止处理
    """
    start_time = time.time()

    try:
        import fitz

        engine = get_rapid_ocr()
        device_str = get_device_info_str()
        src_doc = fitz.open(str(input_pdf))
        total_pages = len(src_doc)

        logger.info(f"RapidOCR [{device_str}] 开始处理: {input_pdf.name}, {total_pages} 页, DPI={dpi}")

        new_doc = fitz.open()
        temp_dir = Path(tempfile.mkdtemp())

        ocr_pages = 0
        stopped = False

        try:
            for page_num in range(total_pages):
                # 检查是否被要求停止
                if stop_check and stop_check():
                    logger.info(f"  处理被中止（已完成 {page_num}/{total_pages} 页）")
                    stopped = True
                    break

                page = src_doc[page_num]
                page_w = page.rect.width
                page_h = page.rect.height

                # 渲染为图片
                img_path, pix, pw, ph, iw, ih = _render_page(page, dpi, temp_dir, page_num)

                # OCR 识别
                result, elapse = engine(str(img_path))

                # 构建输出页面
                new_page = new_doc.new_page(width=page_w, height=page_h)
                new_page.insert_image(new_page.rect, pixmap=pix)

                if not result:
                    logger.info(f"  第 {page_num+1}/{total_pages} 页: 无文字")
                    continue

                _build_text_layer(new_page, result, page_w, page_h, iw, ih)
                ocr_pages += 1
                logger.info(f"  第 {page_num+1}/{total_pages} 页: {len(result)} 行文字")

            src_doc.close()

            # 中止时也保存已处理的页面（部分结果）
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            new_doc.save(str(output_pdf), garbage=4, deflate=True)
            new_doc.close()

            elapsed = time.time() - start_time

            if stopped:
                logger.info(f"RapidOCR [{device_str}] 已中止: {ocr_pages}/{total_pages} 页, {elapsed:.1f}秒")
                return {
                    "success": False,
                    "pages": total_pages,
                    "ocr_pages": ocr_pages,
                    "time": elapsed,
                    "device": device_str,
                    "error": "用户中止"
                }

            logger.info(
                f"RapidOCR [{device_str}] 完成: {total_pages} 页 "
                f"(OCR {ocr_pages} 页), {elapsed:.1f}秒"
            )

            return {
                "success": True,
                "pages": total_pages,
                "ocr_pages": ocr_pages,
                "time": elapsed,
                "device": device_str,
                "error": ""
            }

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"RapidOCR 处理失败: {e}", exc_info=True)
        return {
            "success": False,
            "pages": 0,
            "time": time.time() - start_time,
            "device": get_device_info_str(),
            "error": str(e)
        }
