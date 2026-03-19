"""
OCR 识别模块
🔍 龙二【技术】负责实现
⚙️ 紫影【研发】负责评审

使用 OCRmyPDF 进行扫描版 PDF 转可搜索 PDF
"""

import subprocess
from pathlib import Path
from typing import Optional


class OCREngine:
    """OCR 引擎"""
    
    def __init__(self, language: str = "chi_sim+eng"):
        """
        Args:
            language: OCR 语言，默认中英文混合
        """
        self.language = language
    
    def convert_to_searchable_pdf(
        self,
        input_pdf: Path,
        output_pdf: Path,
        force_ocr: bool = True
    ) -> bool:
        """
        将扫描版 PDF 转为可搜索 PDF
        
        Args:
            input_pdf: 输入 PDF
            output_pdf: 输出 PDF
            force_ocr: 是否强制 OCR
            
        Returns:
            bool: 是否成功
        """
        try:
            cmd = [
                "ocrmypdf",
                "-l", self.language,
                "--output-type", "pdf",
            ]
            
            if force_ocr:
                cmd.append("--force-ocr")
            
            cmd.extend([str(input_pdf), str(output_pdf)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 分钟超时
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"OCR 失败：{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("OCR 超时")
            return False
        except Exception as e:
            print(f"OCR 异常：{e}")
            return False
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        提取 PDF 中的文本
        
        Args:
            pdf_path: PDF 路径
            
        Returns:
            str: 提取的文本
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(str(pdf_path))
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text
        except Exception as e:
            print(f"提取文本失败：{e}")
            return ""


def batch_ocr(
    input_dir: Path,
    output_dir: Path,
    language: str = "chi_sim+eng"
) -> tuple:
    """
    批量 OCR 处理
    
    Returns:
        (成功数，失败数)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    engine = OCREngine(language=language)
    success_count = 0
    fail_count = 0
    
    for pdf_path in input_dir.glob("*.pdf"):
        output_path = output_dir / f"searchable_{pdf_path.name}"
        if engine.convert_to_searchable_pdf(pdf_path, output_path):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count
