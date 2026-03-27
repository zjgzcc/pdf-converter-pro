"""
水印去除模块
🧪 青影【测试】负责验证
🔍 龙二【技术】负责实现

支持两种模式：
1. OpenCV 传统方法（颜色单一水印）
2. IOPaint AI 方法（复杂水印，LaMa 模型）

功能：
- 水印自动检测（颜色分析 + 边缘检测）
- 批量图片去水印
- IOPaint 完整集成
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from PIL import Image


class WatermarkDetector:
    """水印检测器 - 自动识别水印区域"""
    
    def __init__(self):
        pass
    
    def detect(self, img: np.ndarray) -> np.ndarray:
        """
        检测水印区域，返回二值掩码
        
        Args:
            img: BGR 图像
            
        Returns:
            二值掩码（水印区域为白色）
        """
        # 方法 1: 颜色分析（检测浅色/白色水印）
        color_mask = self._detect_by_color(img)
        
        # 方法 2: 边缘检测（检测文本边缘）
        edge_mask = self._detect_by_edge(img)
        
        # 合并两个掩码
        combined_mask = cv2.bitwise_or(color_mask, edge_mask)
        
        # 形态学操作，连接相邻区域
        kernel = np.ones((3, 3), np.uint8)
        dilated_mask = cv2.dilate(combined_mask, kernel, iterations=2)
        cleaned_mask = cv2.erode(dilated_mask, kernel, iterations=1)
        
        return cleaned_mask
    
    def _detect_by_color(self, img: np.ndarray) -> np.ndarray:
        """基于颜色分析检测水印"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 检测浅色/白色区域
        lower_white1 = np.array([0, 0, 200])
        upper_white1 = np.array([180, 20, 255])
        mask1 = cv2.inRange(hsv, lower_white1, upper_white1)
        
        # 检测浅灰色区域
        lower_white2 = np.array([0, 0, 180])
        upper_white2 = np.array([180, 30, 230])
        mask2 = cv2.inRange(hsv, lower_white2, upper_white2)
        
        # 合并
        mask = cv2.bitwise_or(mask1, mask2)
        return mask
    
    def _detect_by_edge(self, img: np.ndarray) -> np.ndarray:
        """基于边缘检测检测水印"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Canny 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 膨胀边缘
        kernel = np.ones((3, 3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=2)
        
        return dilated_edges


class WatermarkRemover:
    """水印去除器"""
    
    def __init__(self, method: str = "auto", confidence_threshold: float = 0.5):
        """
        Args:
            method: "opencv" | "iopaint" | "auto"
            confidence_threshold: 自动检测的置信度阈值
        """
        self.method = method
        self.confidence_threshold = confidence_threshold
        self.detector = WatermarkDetector()
        self._iopaint_model = None
    
    def remove(self, image_path: Path, output_path: Path) -> bool:
        """
        去除水印
        
        Args:
            image_path: 输入图片路径
            output_path: 输出图片路径
            
        Returns:
            bool: 是否成功
        """
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                print(f"无法读取图像：{image_path}")
                return False
            
            # 自动选择方法
            if self.method == "auto":
                # 检测水印复杂度，决定使用哪种方法
                complexity = self._analyze_complexity(img)
                if complexity > 0.6:
                    actual_method = "iopaint"
                else:
                    actual_method = "opencv"
            else:
                actual_method = self.method
            
            # 执行去水印
            if actual_method == "iopaint":
                result = self._remove_iopaint(img)
            else:
                result = self._remove_opencv(img)
            
            cv2.imwrite(str(output_path), result)
            return True
        except Exception as e:
            print(f"去水印失败：{e}")
            return False
    
    def _analyze_complexity(self, img: np.ndarray) -> float:
        """
        分析图像复杂度（0-1）
        复杂度高 -> 使用 IOPaint
        复杂度低 -> 使用 OpenCV
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 计算梯度（边缘密度）
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 归一化到 0-1
        complexity = np.mean(gradient_magnitude) / 255.0
        return min(1.0, complexity)
    
    def _remove_opencv(self, img: np.ndarray) -> np.ndarray:
        """
        OpenCV 传统方法 - 基于颜色阈值 + 修复算法
        
        适合：颜色单一的浅色水印
        """
        # 检测水印区域
        mask = self.detector.detect(img)
        
        # 使用修复算法（inpaint）
        result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
        
        return result
    
    def _remove_iopaint(self, img: np.ndarray) -> np.ndarray:
        """
        IOPaint AI 方法 - 使用 LaMa 模型
        
        适合：复杂背景、半透明水印、大面积水印
        """
        try:
            # 延迟导入，避免不必要的依赖
            from iopaint import ModelManager
            
            # 初始化模型（单例模式）
            if self._iopaint_model is None:
                self._iopaint_model = ModelManager().get_model("lama")
            
            # 检测水印区域
            mask = self.detector.detect(img)
            
            # 转换格式：BGR -> RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 使用 IOPaint 进行修复
            # IOPaint 输入：RGB 图像 + 二值掩码
            result_rgb = self._iopaint_model(img_rgb, mask)
            
            # 转换回 BGR
            result = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
            
            return result
        except ImportError:
            print("⚠️  IOPaint 未安装，回退到 OpenCV 模式")
            print("   安装命令：pip install iopaint")
            return self._remove_opencv(img)
        except Exception as e:
            print(f"⚠️  IOPaint 处理失败：{e}，回退到 OpenCV 模式")
            return self._remove_opencv(img)


def batch_remove_watermarks(
    input_dir: Path,
    output_dir: Path,
    method: str = "auto",
    recursive: bool = False
) -> Tuple[int, int, List[Dict]]:
    """
    批量去除水印
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        method: 去水印方法 ("opencv" | "iopaint" | "auto")
        recursive: 是否递归处理子目录
        
    Returns:
        (成功数，失败数，详细结果列表)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    results = []
    
    # 获取所有图片
    if recursive:
        patterns = ["**/*.png", "**/*.jpg", "**/*.jpeg", "**/*.bmp", "**/*.webp"]
    else:
        patterns = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp"]
    
    image_files = []
    for pattern in patterns:
        image_files.extend(input_dir.glob(pattern))
    
    # 去重
    image_files = list(set(image_files))
    
    remover = WatermarkRemover(method=method)
    
    for img_path in image_files:
        # 保持目录结构
        if recursive:
            rel_path = img_path.relative_to(input_dir)
            output_path = output_dir / rel_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = output_dir / img_path.name
        
        success = remover.remove(img_path, output_path)
        
        results.append({
            "input": str(img_path),
            "output": str(output_path),
            "success": success
        })
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {img_path.name}")
    
    print(f"\n批量处理完成：成功 {success_count} 个，失败 {fail_count} 个")
    
    return success_count, fail_count, results


def process_pdf_images(
    pdf_path: Path,
    output_dir: Path,
    method: str = "auto",
    dpi: int = 300
) -> Tuple[int, int]:
    """
    处理 PDF 中的图片（提取 -> 去水印 -> 合并）
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        method: 去水印方法
        dpi: 转换 DPI
        
    Returns:
        (成功页数，失败页数)
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("⚠️  PyMuPDF 未安装，请运行：pip install PyMuPDF")
        return 0, 0
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 打开 PDF
    doc = fitz.open(str(pdf_path))
    success_count = 0
    fail_count = 0
    
    remover = WatermarkRemover(method=method)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 将页面转换为图片
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        
        # 保存临时图片
        temp_img_path = output_dir / f"temp_page_{page_num:04d}.png"
        pix.save(str(temp_img_path))
        
        # 去水印
        output_img_path = output_dir / f"page_{page_num:04d}.png"
        success = remover.remove(temp_img_path, output_img_path)
        
        # 删除临时文件
        temp_img_path.unlink()
        
        if success:
            success_count += 1
            print(f"✓ 第 {page_num + 1}/{len(doc)} 页处理完成")
        else:
            fail_count += 1
            print(f"✗ 第 {page_num + 1}/{len(doc)} 页处理失败")
    
    doc.close()
    
    print(f"\nPDF 处理完成：成功 {success_count} 页，失败 {fail_count} 页")
    return success_count, fail_count


def images_to_pdf(
    image_dir: Path,
    output_pdf: Path,
    page_size: str = "A4"
) -> bool:
    """
    将图片合并为 PDF
    
    Args:
        image_dir: 图片目录
        output_pdf: 输出 PDF 路径
        page_size: 页面大小 ("A4", "Letter", 或自定义元组)
        
    Returns:
        bool: 是否成功
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("⚠️  PyMuPDF 未安装，请运行：pip install PyMuPDF")
        return False
    
    # 定义页面大小
    page_sizes = {
        "A4": (595, 842),
        "Letter": (612, 792),
        "A3": (842, 1190),
    }
    
    if isinstance(page_size, str):
        width, height = page_sizes.get(page_size, page_sizes["A4"])
    else:
        width, height = page_size
    
    # 获取所有图片
    image_files = sorted([
        f for f in image_dir.glob("*")
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]
    ])
    
    if not image_files:
        print(f"目录中没有找到图片：{image_dir}")
        return False
    
    # 创建 PDF
    doc = fitz.open()
    
    for img_path in image_files:
        # 打开图片
        img = Image.open(str(img_path))
        img_width, img_height = img.size
        
        # 计算缩放比例（适应页面）
        scale = min(width / img_width, height / img_height)
        new_width = img_width * scale
        new_height = img_height * scale
        
        # 创建新页面
        page = doc.new_page(width=width, height=height)
        
        # 插入图片（居中）
        x = (width - new_width) / 2
        y = (height - new_height) / 2
        rect = fitz.Rect(x, y, x + new_width, y + new_height)
        
        page.insert_image(rect, filename=str(img_path))
    
    # 保存 PDF
    doc.save(str(output_pdf))
    doc.close()
    
    print(f"✓ PDF 已保存：{output_pdf}")
    return True


def process_pdf_with_watermark_removal(
    input_pdf: Path,
    output_pdf: Path,
    method: str = "auto",
    dpi: int = 300,
    temp_dir: Optional[Path] = None
) -> bool:
    """
    完整流程：PDF -> 图片 -> 去水印 -> PDF
    
    Args:
        input_pdf: 输入 PDF
        output_pdf: 输出 PDF
        method: 去水印方法
        dpi: 转换 DPI
        temp_dir: 临时目录（可选）
        
    Returns:
        bool: 是否成功
    """
    import tempfile
    import shutil
    
    # 创建临时目录
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="pdf_watermark_"))
        cleanup = True
    else:
        temp_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    
    try:
        # 步骤 1: PDF 转图片 + 去水印
        success, fail = process_pdf_images(input_pdf, temp_dir, method, dpi)
        
        if success == 0:
            print("没有成功处理任何页面")
            return False
        
        # 步骤 2: 图片合并为 PDF
        result = images_to_pdf(temp_dir, output_pdf)
        
        return result
    finally:
        # 清理临时文件
        if cleanup:
            shutil.rmtree(temp_dir, ignore_errors=True)
