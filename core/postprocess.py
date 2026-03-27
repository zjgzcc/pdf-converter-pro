# -*- coding: utf-8 -*-
"""
OCR 后处理模块：修复断行、合并碎片文字，重建文字层
用于改善 OCR 后 PDF 的可搜索性
"""
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def merge_broken_lines(text: str) -> str:
    """
    合并 OCR 产生的断行文字
    """
    if not text or not text.strip():
        return text
    
    lines = text.split('\n')
    merged = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if not line.strip():
            merged.append(line)
            i += 1
            continue
        
        current = line.rstrip()
        
        while i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            if not next_line:
                break
            
            if current and current[-1] in '。！？':
                break
            
            should_merge = False
            separator = ''
            
            if current:
                last_char = current[-1]
                first_char = next_line[0] if next_line else ''
                
                if _is_cjk(last_char) and _is_cjk(first_char):
                    should_merge = True
                    separator = ''
                elif _is_cjk(last_char) and (first_char in '，。；：、！？）》】"' or first_char.isdigit()):
                    should_merge = True
                    separator = ''
                elif last_char in '，；：、（《【"' and _is_cjk(first_char):
                    should_merge = True
                    separator = ''
                elif (last_char.isalnum() and first_char.isalnum() 
                      and not _is_cjk(last_char) and not _is_cjk(first_char)):
                    should_merge = True
                    separator = ' '
                elif _is_cjk(last_char) and first_char.isalnum():
                    should_merge = True
                    separator = ''
                elif last_char.isalnum() and _is_cjk(first_char):
                    should_merge = True
                    separator = ''
                elif len(current.strip()) < 5 and len(next_line.strip()) < 20:
                    should_merge = True
                    separator = ''
            
            if should_merge:
                current = current + separator + next_line
                i += 1
            else:
                break
        
        merged.append(current)
        i += 1
    
    return '\n'.join(merged)


def _is_cjk(char: str) -> bool:
    """判断是否为 CJK 字符"""
    if not char:
        return False
    cp = ord(char)
    return (
        (0x4E00 <= cp <= 0x9FFF) or
        (0x3400 <= cp <= 0x4DBF) or
        (0xF900 <= cp <= 0xFAFF) or
        (0x2F800 <= cp <= 0x2FA1F)
    )


def rebuild_text_layer(input_pdf: Path, output_pdf: Path = None) -> bool:
    """
    重建 OCR PDF 的文字层：
    1. 提取每页 OCR 文字
    2. 合并断行
    3. 保留原始图片，用合并后的文字创建新的不可见文字层
    
    这样搜索 "试验" 就能搜到（不再是 "试\n验"）
    """
    try:
        import fitz
        
        if output_pdf is None:
            output_pdf = input_pdf
        
        src_doc = fitz.open(str(input_pdf))
        new_doc = fitz.open()  # 创建新文档
        
        for page_num in range(len(src_doc)):
            src_page = src_doc[page_num]
            
            # 提取原始 OCR 文字
            original_text = src_page.get_text()
            
            # 合并断行
            merged_text = merge_broken_lines(original_text)
            
            # 创建新页面（与原页面同尺寸）
            new_page = new_doc.new_page(
                width=src_page.rect.width,
                height=src_page.rect.height
            )
            
            # 1. 先复制原始页面的图片内容
            # 获取原始页面渲染成图片
            zoom = 1.0  # 保持原始分辨率
            mat = fitz.Matrix(zoom, zoom)
            pix = src_page.get_pixmap(matrix=mat)
            new_page.insert_image(new_page.rect, pixmap=pix)
            
            # 2. 添加不可见的合并文字层（用于搜索）
            if merged_text.strip():
                # 用极小的透明文字覆盖整个页面
                # 这些文字不可见，但可以被搜索到
                tw = fitz.TextWriter(new_page.rect)
                
                # 使用内置字体（支持中文）
                try:
                    font = fitz.Font("cjk")  # CJK 字体
                except:
                    font = fitz.Font("helv")  # 后备字体
                
                # 将合并后的文字分段放置在页面上
                y_pos = 10
                line_height = 12
                margin = 10
                max_width = new_page.rect.width - 2 * margin
                
                for line in merged_text.split('\n'):
                    line = line.strip()
                    if not line:
                        y_pos += line_height
                        continue
                    
                    if y_pos > new_page.rect.height - margin:
                        break
                    
                    try:
                        tw.append(
                            pos=(margin, y_pos),
                            text=line,
                            font=font,
                            fontsize=1  # 极小字体，不可见
                        )
                    except Exception:
                        pass  # 跳过无法写入的字符
                    
                    y_pos += line_height
                
                # 写入页面（透明色，不可见）
                tw.write_text(new_page, color=(1, 1, 1), render_mode=3)
                # render_mode=3 = invisible (不渲染但可搜索)
        
        src_doc.close()
        
        # 保存
        new_doc.save(str(output_pdf), garbage=4, deflate=True)
        new_doc.close()
        
        logger.info(f"文字层重建完成: {output_pdf.name}")
        return True
        
    except Exception as e:
        logger.error(f"文字层重建失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    test_text = """电磁兼容 " 试
验和测
量技术
抗扰度试验总论
1 " 范图
本部分涵
盖
了电气
和电子设
备 ( 装置和系
统 ) 在
其电磁环境中的试验和测量技术。"""
    
    print("=== 原始 ===")
    print(test_text)
    print("\n=== 合并后 ===")
    print(merge_broken_lines(test_text))
