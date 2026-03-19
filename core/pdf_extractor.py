"""
PDF 图片提取模块
🔍 龙二【技术】负责实现
🧪 青影【测试】负责验证

功能：
- PDF 每页转图片（PyMuPDF）
- 提取 PDF 中的嵌入图片
- 处理后的图片合并回 PDF
- 支持批量处理
"""

import fitz  # PyMuPDF
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Union
from PIL import Image
import tempfile
import shutil
import io


class PDFExtractor:
    """PDF 提取器"""
    
    def __init__(self, dpi: int = 300):
        """
        Args:
            dpi: 转换 DPI（默认 300）
        """
        self.dpi = dpi
    
    def pdf_to_images(
        self,
        pdf_path: Path,
        output_dir: Path,
        pages: Optional[List[int]] = None,
        image_format: str = "png"
    ) -> Tuple[int, int, List[Dict]]:
        """
        将 PDF 每页转换为图片
        
        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
            pages: 要转换的页码列表（None=全部）
            image_format: 输出格式 ("png", "jpg", "jpeg")
            
        Returns:
            (成功数，失败数，详细结果列表)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            print(f"无法打开 PDF：{e}")
            return 0, 0, []
        
        # 确定要转换的页码
        if pages is None:
            page_range = range(len(doc))
        else:
            page_range = [p - 1 for p in pages if 1 <= p <= len(doc)]  # 转为 0-indexed
        
        success_count = 0
        fail_count = 0
        results = []
        
        for page_num in page_range:
            page = doc[page_num]
            
            # 计算缩放矩阵
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            
            try:
                # 渲染页面
                pix = page.get_pixmap(matrix=mat)
                
                # 生成输出文件名
                output_filename = f"page_{page_num + 1:04d}.{image_format}"
                output_path = output_dir / output_filename
                
                # 保存图片
                if image_format.lower() in ["jpg", "jpeg"]:
                    # JPG 需要 RGB 格式
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    img = img.convert("RGB")
                    img.save(str(output_path), "JPEG", quality=95)
                else:
                    pix.save(str(output_path))
                
                results.append({
                    "page": page_num + 1,
                    "output": str(output_path),
                    "success": True,
                    "width": pix.width,
                    "height": pix.height
                })
                
                success_count += 1
                print(f"[OK] 第 {page_num + 1}/{len(doc)} 页 -> {output_filename}")
                
            except Exception as e:
                results.append({
                    "page": page_num + 1,
                    "output": None,
                    "success": False,
                    "error": str(e)
                })
                fail_count += 1
                print(f"[FAIL] 第 {page_num + 1}/{len(doc)} 页失败：{e}")
        
        doc.close()
        
        print(f"\nPDF 转图片完成：成功 {success_count} 页，失败 {fail_count} 页")
        return success_count, fail_count, results
    
    def extract_embedded_images(
        self,
        pdf_path: Path,
        output_dir: Path
    ) -> Tuple[int, int, List[Dict]]:
        """
        提取 PDF 中嵌入的所有图片
        
        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
            
        Returns:
            (成功数，失败数，详细结果列表)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            print(f"无法打开 PDF：{e}")
            return 0, 0, []
        
        success_count = 0
        fail_count = 0
        results = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                
                try:
                    # 提取图片
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # 生成输出文件名
                    output_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                    output_path = output_dir / output_filename
                    
                    # 保存图片
                    with open(output_path, "wb") as f:
                        f.write(image_bytes)
                    
                    results.append({
                        "page": page_num + 1,
                        "image_index": img_index + 1,
                        "output": str(output_path),
                        "success": True,
                        "format": image_ext
                    })
                    
                    success_count += 1
                    
                except Exception as e:
                    results.append({
                        "page": page_num + 1,
                        "image_index": img_index + 1,
                        "output": None,
                        "success": False,
                        "error": str(e)
                    })
                    fail_count += 1
        
        doc.close()
        
        print(f"提取嵌入图片完成：成功 {success_count} 个，失败 {fail_count} 个")
        return success_count, fail_count, results


class PDFMerger:
    """PDF 合并器 - 将图片合并为 PDF"""
    
    def __init__(self, page_size: str = "A4"):
        """
        Args:
            page_size: 页面大小 ("A4", "Letter", "A3", 或自定义元组)
        """
        self.page_sizes = {
            "A4": (595, 842),
            "Letter": (612, 792),
            "A3": (842, 1190),
            "A5": (420, 595),
        }
        
        if isinstance(page_size, str):
            self.width, self.height = self.page_sizes.get(page_size, self.page_sizes["A4"])
        else:
            self.width, self.height = page_size
    
    def images_to_pdf(
        self,
        image_dir: Path,
        output_pdf: Path,
        pattern: str = "*.png",
        sort: bool = True,
        fit_page: bool = True
    ) -> bool:
        """
        将目录中的图片合并为 PDF
        
        Args:
            image_dir: 图片目录
            output_pdf: 输出 PDF 路径
            pattern: 文件匹配模式
            sort: 是否排序
            fit_page: 是否适应页面（保持宽高比）
            
        Returns:
            bool: 是否成功
        """
        # 获取所有图片
        image_files = list(image_dir.glob(pattern))
        
        # 扩展匹配更多格式
        for ext in ["*.jpg", "*.jpeg", "*.bmp", "*.webp"]:
            if ext != pattern:
                image_files.extend(image_dir.glob(ext))
        
        # 去重
        image_files = list(set(image_files))
        
        if sort:
            image_files = sorted(image_files, key=lambda x: x.name)
        
        if not image_files:
            print(f"目录中没有找到图片：{image_dir}")
            return False
        
        # 创建 PDF
        doc = fitz.open()
        
        for img_path in image_files:
            try:
                # 打开图片
                img = Image.open(str(img_path))
                img_width, img_height = img.size
                
                if fit_page:
                    # 计算缩放比例（适应页面）
                    scale = min(self.width / img_width, self.height / img_height)
                    new_width = img_width * scale
                    new_height = img_height * scale
                    
                    # 居中位置
                    x = (self.width - new_width) / 2
                    y = (self.height - new_height) / 2
                else:
                    # 使用原始尺寸（可能超出页面）
                    new_width = img_width
                    new_height = img_height
                    x = 0
                    y = 0
                
                # 创建新页面
                page = doc.new_page(width=self.width, height=self.height)
                
                # 插入图片
                rect = fitz.Rect(x, y, x + new_width, y + new_height)
                page.insert_image(rect, filename=str(img_path))
                
                print(f"[OK] 添加：{img_path.name}")
                
            except Exception as e:
                print(f"[FAIL] 添加失败 {img_path.name}: {e}")
        
        # 保存 PDF
        try:
            doc.save(str(output_pdf))
            doc.close()
            print(f"[OK] PDF 已保存：{output_pdf}")
            return True
        except Exception as e:
            print(f"[FAIL] 保存 PDF 失败：{e}")
            doc.close()
            return False
    
    def images_list_to_pdf(
        self,
        image_paths: List[Path],
        output_pdf: Path,
        fit_page: bool = True
    ) -> bool:
        """
        将图片列表合并为 PDF
        
        Args:
            image_paths: 图片路径列表
            output_pdf: 输出 PDF 路径
            fit_page: 是否适应页面
            
        Returns:
            bool: 是否成功
        """
        if not image_paths:
            print("图片列表为空")
            return False
        
        # 创建 PDF
        doc = fitz.open()
        
        for img_path in image_paths:
            try:
                img = Image.open(str(img_path))
                img_width, img_height = img.size
                
                if fit_page:
                    scale = min(self.width / img_width, self.height / img_height)
                    new_width = img_width * scale
                    new_height = img_height * scale
                    x = (self.width - new_width) / 2
                    y = (self.height - new_height) / 2
                else:
                    new_width = img_width
                    new_height = img_height
                    x = 0
                    y = 0
                
                page = doc.new_page(width=self.width, height=self.height)
                rect = fitz.Rect(x, y, x + new_width, y + new_height)
                page.insert_image(rect, filename=str(img_path))
                
                print(f"[OK] 添加：{img_path.name}")
                
            except Exception as e:
                print(f"[FAIL] 添加失败 {img_path.name}: {e}")
        
        try:
            doc.save(str(output_pdf))
            doc.close()
            print(f"[OK] PDF 已保存：{output_pdf}")
            return True
        except Exception as e:
            print(f"[FAIL] 保存 PDF 失败：{e}")
            doc.close()
            return False


class PDFProcessor:
    """PDF 完整处理器 - 整合提取、处理、合并流程"""
    
    def __init__(self, dpi: int = 300, page_size: str = "A4"):
        """
        Args:
            dpi: 转换 DPI
            page_size: 输出 PDF 页面大小
        """
        self.extractor = PDFExtractor(dpi=dpi)
        self.merger = PDFMerger(page_size=page_size)
    
    def process_with_callback(
        self,
        input_pdf: Path,
        output_pdf: Path,
        process_callback=None,
        temp_dir: Optional[Path] = None
    ) -> bool:
        """
        处理 PDF，支持自定义处理回调
        
        Args:
            input_pdf: 输入 PDF
            output_pdf: 输出 PDF
            process_callback: 处理回调函数 (image_path) -> modified_image_path
            temp_dir: 临时目录（可选）
            
        Returns:
            bool: 是否成功
        """
        # 创建临时目录
        if temp_dir is None:
            temp_dir = Path(tempfile.mkdtemp(prefix="pdf_process_"))
            cleanup = True
        else:
            temp_dir.mkdir(parents=True, exist_ok=True)
            cleanup = False
        
        try:
            # 步骤 1: PDF 转图片
            print("步骤 1: PDF 转图片...")
            success, fail, results = self.extractor.pdf_to_images(input_pdf, temp_dir)
            
            if success == 0:
                print("没有成功转换任何页面")
                return False
            
            # 步骤 2: 自定义处理（如果有回调）
            if process_callback:
                print("步骤 2: 自定义处理...")
                processed_images = []
                
                for result in results:
                    if result["success"]:
                        img_path = Path(result["output"])
                        try:
                            processed_path = process_callback(img_path)
                            if processed_path:
                                processed_images.append(processed_path)
                                print(f"✓ 处理：{img_path.name}")
                        except Exception as e:
                            print(f"✗ 处理失败 {img_path.name}: {e}")
                            processed_images.append(img_path)  # 使用原图
                    else:
                        print(f"✗ 跳过失败的页面")
            else:
                # 没有回调，使用原图
                processed_images = [Path(r["output"]) for r in results if r["success"]]
            
            # 步骤 3: 图片合并为 PDF
            print("步骤 3: 图片合并为 PDF...")
            result = self.merger.images_list_to_pdf(processed_images, output_pdf)
            
            return result
            
        finally:
            # 清理临时文件
            if cleanup:
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def batch_process(
        self,
        input_dir: Path,
        output_dir: Path,
        process_callback=None
    ) -> Tuple[int, int]:
        """
        批量处理 PDF 文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            process_callback: 处理回调函数
            
        Returns:
            (成功数，失败数)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_files = list(input_dir.glob("*.pdf"))
        
        success_count = 0
        fail_count = 0
        
        for pdf_path in pdf_files:
            output_pdf = output_dir / pdf_path.name
            
            print(f"\n处理：{pdf_path.name}")
            if self.process_with_callback(pdf_path, output_pdf, process_callback):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\n批量处理完成：成功 {success_count} 个，失败 {fail_count} 个")
        return success_count, fail_count


# 便捷函数
def pdf_to_images(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 300,
    pages: Optional[List[int]] = None
) -> Tuple[int, int]:
    """便捷函数：PDF 转图片"""
    extractor = PDFExtractor(dpi=dpi)
    success, fail, _ = extractor.pdf_to_images(pdf_path, output_dir, pages)
    return success, fail


def images_to_pdf(
    image_dir: Path,
    output_pdf: Path,
    page_size: str = "A4"
) -> bool:
    """便捷函数：图片合并为 PDF"""
    merger = PDFMerger(page_size=page_size)
    return merger.images_to_pdf(image_dir, output_pdf)


def extract_images_from_pdf(
    pdf_path: Path,
    output_dir: Path
) -> Tuple[int, int]:
    """便捷函数：提取 PDF 中的嵌入图片"""
    extractor = PDFExtractor()
    success, fail, _ = extractor.extract_embedded_images(pdf_path, output_dir)
    return success, fail
