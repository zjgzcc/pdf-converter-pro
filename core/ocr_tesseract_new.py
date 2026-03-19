# 新的 Tesseract 实现 - 使用 Tesseract 直接生成 PDF
import subprocess
from pathlib import Path
import fitz
import tempfile
import shutil
import logging

def tesseract_convert_direct(input_pdf: Path, output_pdf: Path, language='chi_sim+eng', dpi=300):
    """
    使用 Tesseract 直接生成可搜索 PDF
    Tesseract 4.0+ 支持 pdf 输出格式
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"使用 Tesseract 直接生成 PDF: {input_pdf}")
    
    # 打开 PDF
    doc = fitz.open(str(input_pdf))
    total_pages = len(doc)
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 为每一页生成 PDF
        page_pdfs = []
        
        for page_num in range(total_pages):
            logger.info(f"处理第 {page_num + 1}/{total_pages} 页")
            
            # 获取页面
            page = doc[page_num]
            
            # 渲染为图片
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # 保存临时图片
            temp_img = temp_dir / f"page_{page_num:04d}.png"
            pix.save(str(temp_img))
            
            # 使用 Tesseract 生成 PDF
            temp_pdf_base = temp_dir / f"page_{page_num:04d}"
            
            result = subprocess.run(
                [
                    "tesseract",
                    str(temp_img),
                    str(temp_pdf_base),
                    "-l", language.replace("+", "+"),
                    "pdf"  # 直接输出 PDF
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            temp_pdf = temp_dir / f"page_{page_num:04d}.pdf"
            
            if result.returncode == 0 and temp_pdf.exists():
                page_pdfs.append(temp_pdf)
                logger.info(f"第 {page_num + 1} 页 PDF 生成成功")
            else:
                logger.error(f"第 {page_num + 1} 页 PDF 生成失败: {result.stderr}")
                # 创建一个空白页面作为占位
                blank_doc = fitz.open()
                blank_doc.new_page(width=page.rect.width, height=page.rect.height)
                blank_pdf = temp_dir / f"blank_{page_num:04d}.pdf"
                blank_doc.save(str(blank_pdf))
                blank_doc.close()
                page_pdfs.append(blank_pdf)
        
        doc.close()
        
        # 合并所有页面
        logger.info("合并 PDF 页面...")
        output_doc = fitz.open()
        
        for page_pdf in page_pdfs:
            src = fitz.open(str(page_pdf))
            output_doc.insert_pdf(src)
            src.close()
        
        # 保存最终 PDF
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        output_doc.save(str(output_pdf))
        output_doc.close()
        
        logger.info(f"Tesseract PDF 创建成功: {output_pdf}")
        return True
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # 测试
    input_file = Path(r"C:\Users\50306\.openclaw\workspace\pdf-converter-pro\test_sample.pdf")
    output_file = Path(r"C:\Users\50306\Desktop\PDF_Converter_Output\test_tesseract_direct.pdf")
    
    logging.basicConfig(level=logging.INFO)
    success = tesseract_convert_direct(input_file, output_file)
    print(f"转换{'成功' if success else '失败'}")
