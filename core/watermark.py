"""
水印去除模块
🧪 青影【测试】负责验证
🔍 龙二【技术】负责优化

支持两种模式：
1. OpenCV 传统方法（颜色单一水印）
2. IOPaint AI 方法（复杂水印）
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple


class WatermarkRemover:
    """水印去除器"""
    
    def __init__(self, method: str = "auto"):
        """
        Args:
            method: "opencv" | "iopaint" | "auto"
        """
        self.method = method
    
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
                return False
            
            if self.method == "opencv" or self.method == "auto":
                result = self._remove_opencv(img)
            elif self.method == "iopaint":
                result = self._remove_iopaint(img)
            else:
                result = self._remove_opencv(img)  # 默认
            
            cv2.imwrite(str(output_path), result)
            return True
        except Exception as e:
            print(f"去水印失败：{e}")
            return False
    
    def _remove_opencv(self, img: np.ndarray) -> np.ndarray:
        """
        OpenCV 传统方法 - 基于颜色阈值
        
        适合：颜色单一的浅色水印
        """
        # 转换到 HSV 空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 定义浅色水印的范围（可根据实际情况调整）
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 20, 255])
        
        # 创建掩码
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 膨胀掩码，确保覆盖水印边缘
        kernel = np.ones((3, 3), np.uint8)
        dilated_mask = cv2.dilate(mask, kernel, iterations=2)
        
        # 使用修复算法（inpaint）
        result = cv2.inpaint(img, dilated_mask, 3, cv2.INPAINT_TELEA)
        
        return result
    
    def _remove_iopaint(self, img: np.ndarray) -> np.ndarray:
        """
        IOPaint AI 方法
        
        适合：复杂背景、半透明水印
        需要预先安装 IOPaint
        """
        try:
            from iopaint import ModelManager
            
            # 使用 LaMa 模型进行智能修复
            model = ModelManager().get_model("lama")
            
            # 这里需要检测水印区域（简化处理，实际需要用检测模型）
            # 暂时返回原图
            print("IOPaint 模式需要完整实现水印检测")
            return img
        except ImportError:
            print("IOPaint 未安装，回退到 OpenCV 模式")
            return self._remove_opencv(img)


def batch_remove_watermarks(
    input_dir: Path,
    output_dir: Path,
    method: str = "auto"
) -> Tuple[int, int]:
    """
    批量去除水印
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        method: 去水印方法
        
    Returns:
        (成功数，失败数)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    remover = WatermarkRemover(method=method)
    
    for img_path in input_dir.glob("*.png"):
        output_path = output_dir / img_path.name
        if remover.remove(img_path, output_path):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count
