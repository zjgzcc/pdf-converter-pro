# -*- coding: utf-8 -*-
"""
PaddleOCR + PP-DocLayoutV3 方案
先分析文档布局，再对每个区域进行精准 OCR
"""
import logging
from pathlib import Path
from typing import List, Tuple, Dict
from PIL import Image

logger = logging.getLogger(__name__)

_layout_model = None
_ocr_engine = None


def get_layout_model():
    """获取 PP-DocLayoutV3 模型"""
    global _layout_model
    if _layout_model is not None:
        return _layout_model
    
    try:
        # PP-DocLayoutV3 需要从 paddlex 导入
        from paddlex import PaddleOCR as PPStructure
        _layout_model = PPStructure(
            layout=True,      # 启用布局分析
            ocr=False,        # 不启用 OCR（我们单独做）
            show_log=False,
        )
        logger.info("PP-DocLayoutV3 已加载")
        return _layout_model
    except Exception as e:
        logger.error(f"PP-DocLayoutV3 加载失败: {e}")
        return None


def get_ocr_engine():
    """获取 PaddleOCR 引擎"""
    global _ocr_engine
    if _ocr_engine is not None:
        return _ocr_engine
    
    try:
        from paddleocr import PaddleOCR
        _ocr_engine = PaddleOCR(
            use_textline_orientation=True,
            lang='ch',
            show_log=False,
            # 优化参数，减少漏检
            det_db_thresh=0.15,
            det_db_box_thresh=0.25,
            det_db_unclip_ratio=2.5,
            det_limit_side_len=960,
        )
        logger.info("PaddleOCR 已加载")
        return _ocr_engine
    except Exception as e:
        logger.error(f"PaddleOCR 加载失败: {e}")
        return None


def analyze_layout(img_path: Path) -> List[Dict]:
    """
    分析图片布局
    
    Returns:
        [{'type': str, 'bbox': [x1,y1,x2,y2], 'confidence': float}, ...]
    """
    model = get_layout_model()
    if model is None:
        return []
    
    try:
        result = model(str(img_path))
        regions = []
        
        for item in result:
            if 'layout' in item:
                for layout_item in item['layout']:
                    regions.append({
                        'type': layout_item.get('type', 'text'),
                        'bbox': layout_item.get('bbox', [0, 0, 0, 0]),
                        'confidence': layout_item.get('confidence', 0.5)
                    })
        
        return regions
    except Exception as e:
        logger.error(f"布局分析失败: {e}")
        return []


def crop_region(img_path: Path, bbox: List[int], temp_dir: Path) -> Path:
    """裁剪图片区域"""
    try:
        img = Image.open(str(img_path))
        x1, y1, x2, y2 = bbox
        
        width, height = img.size
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)
        
        if x2 <= x1 or y2 <= y1:
            return img_path
        
        cropped = img.crop((x1, y1, x2, y2))
        output_path = temp_dir / f"crop_{x1}_{y1}_{x2}_{y2}.png"
        cropped.save(str(output_path))
        
        return output_path
    except Exception as e:
        logger.warning(f"裁剪失败: {e}")
        return img_path


def ocr_region(region_img: Path) -> List[Tuple]:
    """
    对区域进行 OCR
    
    Returns:
        [(box, text), ...]
    """
    engine = get_ocr_engine()
    if engine is None:
        return []
    
    try:
        result = engine.ocr(str(region_img), cls=True)
        
        if not result or not result[0]:
            return []
        
        output = []
        for line in result[0]:
            box = line[0]
            text = line[1][0]
            output.append((box, text))
        
        return output
    except Exception as e:
        logger.error(f"OCR 失败: {e}")
        return []


def paddle_layout_ocr(img_path: Path, temp_dir: Path) -> List[Tuple]:
    """
    PaddleOCR + PP-DocLayoutV3 完整流程
    
    1. 分析布局，获取文字区域
    2. 对每个区域进行 OCR
    3. 合并结果
    """
    logger.info("  开始 PP-DocLayoutV3 + PaddleOCR...")
    
    # 步骤 1: 布局分析
    regions = analyze_layout(img_path)
    
    if not regions:
        logger.info("  布局分析未返回结果，使用整页 OCR")
        # 回退到整页 OCR
        return ocr_region(img_path)
    
    logger.info(f"  布局分析发现 {len(regions)} 个区域")
    
    # 步骤 2: 对每个区域进行 OCR
    all_results = []
    
    for i, region in enumerate(regions):
        region_type = region.get('type', 'text')
        bbox = region.get('bbox', [0, 0, 0, 0])
        
        # 裁剪区域
        region_img = crop_region(img_path, bbox, temp_dir)
        
        # OCR 识别
        region_results = ocr_region(region_img)
        
        if region_results:
            # 转换坐标回原图
            x1, y1 = bbox[0], bbox[1]
            for box, text in region_results:
                adjusted_box = [[p[0] + x1, p[1] + y1] for p in box]
                all_results.append((adjusted_box, text))
            
            logger.info(f"    区域 {i+1} ({region_type}): {len(region_results)} 行")
    
    logger.info(f"  总共识别到 {len(all_results)} 行")
    return all_results
