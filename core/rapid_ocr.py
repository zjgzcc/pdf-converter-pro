# -*- coding: utf-8 -*-
"""
RapidOCR 引擎模块 v2
使用 ONNX Runtime 跑 PaddleOCR 模型，精度远超 Tesseract
修复：文字层与原图位置精确对齐
"""
import logging
import time
import tempfile
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_rapid_ocr_instance = None


def get_rapid_ocr():
    """获取 RapidOCR 单例"""
    global _rapid_ocr_instance
    if _rapid_ocr_instance is None:
        from rapidocr_onnxruntime import RapidOCR
        _rapid_ocr_instance = RapidOCR()
        logger.info("RapidOCR 引擎已加载")
    return _rapid_ocr_instance


def rapid_ocr_pdf(input_pdf: Path, output_pdf: Path, dpi: int = 300) -> dict:
    """
    用 RapidOCR 处理 PDF，生成可搜索 PDF。
    文字层精确对齐原始图像位置。
    """
    start_time = time.time()

    try:
        import fitz
        import numpy as np

        engine = get_rapid_ocr()
        src_doc = fitz.open(str(input_pdf))
        total_pages = len(src_doc)

        logger.info(f"RapidOCR 开始处理: {input_pdf.name}, {total_pages} 页, DPI={dpi}")

        new_doc = fitz.open()
        temp_dir = Path(tempfile.mkdtemp())

        try:
            for page_num in range(total_pages):
                page = src_doc[page_num]
                page_w = page.rect.width   # PDF 点
                page_h = page.rect.height

                # 渲染为图片供 OCR
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_path = temp_dir / f"page_{page_num}.png"
                pix.save(str(img_path))
                img_w = pix.width
                img_h = pix.height

                # OCR 识别
                result, elapse = engine(str(img_path))

                # 创建新页面
                new_page = new_doc.new_page(width=page_w, height=page_h)

                # 复制原始图像（用 OCR 同分辨率的图，保证清晰）
                new_page.insert_image(new_page.rect, pixmap=pix)

                if not result:
                    logger.info(f"  第 {page_num+1}/{total_pages} 页: 无文字")
                    continue

                # 坐标缩放：OCR 图片像素 → PDF 点
                sx = page_w / img_w
                sy = page_h / img_h

                try:
                    font = fitz.Font("cjk")
                except Exception:
                    font = fitz.Font("helv")

                tw = fitz.TextWriter(new_page.rect)

                for item in result:
                    box = item[0]   # 4 个角点 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    text = item[1]
                    if not text.strip():
                        continue

                    # box 四角转 PDF 坐标
                    x0 = box[0][0] * sx
                    y0 = box[0][1] * sy
                    x1 = box[1][0] * sx
                    y1 = box[1][1] * sy
                    x2 = box[2][0] * sx
                    y2 = box[2][1] * sy
                    x3 = box[3][0] * sx
                    y3 = box[3][1] * sy

                    # 文字块宽高（取上边和左边）
                    box_w = ((x1 - x0)**2 + (y1 - y0)**2) ** 0.5
                    box_h = ((x3 - x0)**2 + (y3 - y0)**2) ** 0.5

                    if box_h < 1 or box_w < 1:
                        continue

                    # 根据文字块宽度反算 fontsize
                    # 先用 box 高度作为初始 fontsize
                    fontsize = box_h * 0.85
                    if fontsize < 1:
                        fontsize = 1

                    # 测量文字在当前 fontsize 下的实际宽度
                    try:
                        text_width = font.text_length(text, fontsize=fontsize)
                    except Exception:
                        text_width = len(text) * fontsize * 0.6

                    # 如果文字宽度与 box 宽度差距大，调整 fontsize
                    if text_width > 0:
                        ratio = box_w / text_width
                        fontsize = fontsize * ratio
                        # 限制合理范围
                        fontsize = max(0.5, min(fontsize, box_h * 1.2))

                    # 写入位置：左下角（PDF 文字基线）
                    # y 坐标 = box 顶部 + fontsize（基线在字体底部上方一点）
                    baseline_y = y0 + fontsize * 0.9

                    try:
                        tw.append(
                            pos=(x0, baseline_y),
                            text=text,
                            font=font,
                            fontsize=fontsize,
                        )
                    except Exception:
                        pass

                # render_mode=3 = 不可见文字（可搜索可复制）
                tw.write_text(new_page, render_mode=3)

                logger.info(f"  第 {page_num+1}/{total_pages} 页: {len(result)} 行文字")

            src_doc.close()

            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            new_doc.save(str(output_pdf), garbage=4, deflate=True)
            new_doc.close()

            elapsed = time.time() - start_time
            logger.info(f"RapidOCR 完成: {total_pages} 页, {elapsed:.1f}秒")

            return {"success": True, "pages": total_pages, "time": elapsed, "error": ""}

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"RapidOCR 处理失败: {e}", exc_info=True)
        return {"success": False, "pages": 0, "time": time.time() - start_time, "error": str(e)}
