"""
创建测试用 PDF 和图片占位符文件
🧪 青影【测试】工具脚本
"""

from pathlib import Path
import sys

def create_placeholder_files():
    """创建占位符测试文件"""
    sample_dir = Path(__file__).parent
    
    # 创建 PDF 占位符（简单的二进制内容）
    pdf_files = [
        "sample_invoice.pdf",
        "sample_contract.pdf", 
        "sample_scan.pdf"
    ]
    
    for pdf_name in pdf_files:
        pdf_path = sample_dir / pdf_name
        if not pdf_path.exists():
            # PDF 文件头（最小有效 PDF）
            pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n116\n%%EOF"
            pdf_path.write_bytes(pdf_content)
            print(f"[OK] 创建 PDF 占位符：{pdf_name}")
    
    # 创建 PNG 占位符（1x1 像素的透明 PNG）
    png_files = [
        "sample_watermark.png",
        "sample_clean.png"
    ]
    
    for png_name in png_files:
        png_path = sample_dir / png_name
        if not png_path.exists():
            # 最小 PNG 文件（1x1 透明像素）
            png_content = bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG 签名
                0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR 块
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 像素
                0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
                0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT 块
                0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
                0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
                0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND 块
                0x42, 0x60, 0x82
            ])
            png_path.write_bytes(png_content)
            print(f"[OK] 创建 PNG 占位符：{png_name}")
    
    print(f"\n[OK] 所有占位符文件已创建在：{sample_dir}")


if __name__ == "__main__":
    create_placeholder_files()
