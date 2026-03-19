"""
PDF 转 WORD 转换模块
🔍 龙二【技术】负责实现
⚙️ 紫影【研发】负责评审

使用 PaddleOCR 版面恢复保持原格式和布局
"""

import subprocess
from pathlib import Path
from typing import Optional


class PDF2WordConverter:
    """PDF 转 WORD 转换器"""
    
    def __init__(self, method: str = "paddleocr"):
        """
        Args:
            method: "paddleocr" | "freep2w" | "pdf2docx"
        """
        self.method = method
    
    def convert(self, input_pdf: Path, output_docx: Path) -> bool:
        """
        转换 PDF 为 WORD
        
        Args:
            input_pdf: 输入 PDF
            output_docx: 输出 DOCX
            
        Returns:
            bool: 是否成功
        """
        if self.method == "paddleocr":
            return self._convert_paddleocr(input_pdf, output_docx)
        elif self.method == "freep2w":
            return self._convert_freep2w(input_pdf, output_docx)
        else:
            return self._convert_paddleocr(input_pdf, output_docx)
    
    def _convert_paddleocr(self, input_pdf: Path, output_docx: Path) -> bool:
        """
        使用 PaddleOCR 版面恢复
        
        适合：图文混排、表格、复杂布局
        """
        try:
            # 使用 paddleocr 命令行工具
            cmd = [
                "paddleocr",
                "--image_dir", str(input_pdf),
                "--type", "structure",
                "--recovery", "true",
                "--lang", "ch",
                "--output", str(output_docx.parent)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                # PaddleOCR 输出文件名可能不同，需要重命名
                output_dir = output_docx.parent
                for f in output_dir.glob("*.docx"):
                    if f.name.startswith("result"):
                        f.rename(output_docx)
                        break
                return True
            else:
                print(f"PaddleOCR 失败：{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("转换超时")
            return False
        except Exception as e:
            print(f"转换异常：{e}")
            return False
    
    def _convert_freep2w(self, input_pdf: Path, output_docx: Path) -> bool:
        """
        使用 FreeP2W 转换
        
        适合：包含大量数学公式的文档
        """
        try:
            from freep2w.cli import convert_pdf_to_docx
            
            success = convert_pdf_to_docx(
                pdf_path=str(input_pdf),
                output_path=str(output_docx)
            )
            
            return success
        except ImportError:
            print("FreeP2W 未安装，请运行：pip install freep2w")
            return False
        except Exception as e:
            print(f"FreeP2W 转换异常：{e}")
            return False


def batch_convert(
    input_dir: Path,
    output_dir: Path,
    method: str = "paddleocr"
) -> tuple:
    """
    批量转换 PDF 为 WORD
    
    Returns:
        (成功数，失败数)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converter = PDF2WordConverter(method=method)
    success_count = 0
    fail_count = 0
    
    for pdf_path in input_dir.glob("*.pdf"):
        output_path = output_dir / f"{pdf_path.stem}.docx"
        if converter.convert(pdf_path, output_path):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count
