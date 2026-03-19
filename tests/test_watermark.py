"""
水印去除模块测试
🧪 青影【测试】负责验证
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import cv2

# 添加 core 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from watermark import (
    WatermarkRemover,
    WatermarkDetector,
    batch_remove_watermarks,
    process_pdf_images,
    images_to_pdf,
    process_pdf_with_watermark_removal
)


class TestWatermarkRemover:
    """WatermarkRemover 类测试"""
    
    def test_init_default_method(self):
        """测试初始化默认方法"""
        remover = WatermarkRemover()
        assert remover.method == "auto"
    
    def test_init_custom_method(self):
        """测试初始化自定义方法"""
        remover = WatermarkRemover(method="opencv")
        assert remover.method == "opencv"
        
        remover_iopaint = WatermarkRemover(method="iopaint")
        assert remover_iopaint.method == "iopaint"
    
    @patch('watermark.cv2')
    def test_remove_success(self, mock_cv2):
        """测试成功去除水印"""
        # Mock cv2.imread 返回一个有效的图像
        mock_img = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.imread.return_value = mock_img
        mock_cv2.inRange.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.dilate.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.inpaint.return_value = mock_img
        
        remover = WatermarkRemover(method="opencv")
        result = remover.remove(Path("input.png"), Path("output.png"))
        
        assert result is True
        mock_cv2.imread.assert_called_once()
        mock_cv2.imwrite.assert_called_once()
    
    @patch('watermark.cv2')
    def test_remove_file_not_found(self, mock_cv2):
        """测试文件不存在时返回 False"""
        mock_cv2.imread.return_value = None
        
        remover = WatermarkRemover()
        result = remover.remove(Path("nonexistent.png"), Path("output.png"))
        
        assert result is False
    
    @patch('watermark.cv2')
    def test_remove_exception_handling(self, mock_cv2):
        """测试异常处理"""
        mock_cv2.imread.side_effect = Exception("Test exception")
        
        remover = WatermarkRemover()
        result = remover.remove(Path("input.png"), Path("output.png"))
        
        assert result is False
    
    @patch('watermark.cv2')
    def test_remove_opencv_method(self, mock_cv2):
        """测试 OpenCV 方法"""
        mock_img = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.imread.return_value = mock_img
        mock_cv2.inRange.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.dilate.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.inpaint.return_value = mock_img
        
        remover = WatermarkRemover(method="opencv")
        result = remover.remove(Path("input.png"), Path("output.png"))
        
        assert result is True
        # 验证调用了 OpenCV 相关的函数
        mock_cv2.cvtColor.assert_called()
    
    @patch('builtins.__import__')
    @patch('watermark.cv2')
    def test_remove_iopaint_method(self, mock_cv2, mock_import):
        """测试 IOPaint 方法（mock）"""
        mock_img = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.imread.return_value = mock_img
        mock_cv2.imwrite.return_value = None
        
        # Mock IOPaint ModelManager
        mock_model = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_model.return_value = mock_model
        
        # Mock iopaint import
        mock_iopaint = MagicMock()
        mock_iopaint.ModelManager = MagicMock(return_value=mock_manager)
        
        def import_side_effect(name, *args, **kwargs):
            if name == 'iopaint':
                return mock_iopaint
            if name == 'cv2':
                return mock_cv2
            if name == 'numpy' or name.endswith('numpy'):
                return np
            raise ImportError(f"No module named '{name}'")
        
        mock_import.side_effect = import_side_effect
        
        remover = WatermarkRemover(method="iopaint")
        result = remover.remove(Path("input.png"), Path("output.png"))
        
        # IOPaint 模式当前返回原图，但仍应返回 True（因为 write 成功）
        assert result is True


class TestBatchRemoveWatermarks:
    """批量去水印函数测试"""
    
    @patch('watermark.WatermarkRemover')
    def test_batch_success(self, mock_remover_class, tmp_path):
        """测试批量处理成功"""
        # 创建测试目录
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # 创建测试文件
        (input_dir / "test1.png").touch()
        (input_dir / "test2.png").touch()
        
        # Mock remover
        mock_remover = MagicMock()
        mock_remover.remove.return_value = True
        mock_remover_class.return_value = mock_remover
        
        success, fail, results = batch_remove_watermarks(input_dir, output_dir)
        
        assert success == 2
        assert fail == 0
        assert len(results) == 2
        assert mock_remover.remove.call_count == 2
    
    @patch('watermark.WatermarkRemover')
    def test_batch_partial_failure(self, mock_remover_class, tmp_path):
        """测试批量处理部分失败"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        (input_dir / "test1.png").touch()
        (input_dir / "test2.png").touch()
        (input_dir / "test3.png").touch()
        
        mock_remover = MagicMock()
        mock_remover.remove.side_effect = [True, False, True]
        mock_remover_class.return_value = mock_remover
        
        success, fail, results = batch_remove_watermarks(input_dir, output_dir)
        
        assert success == 2
        assert fail == 1
        assert len(results) == 3
    
    @patch('watermark.WatermarkRemover')
    def test_batch_empty_directory(self, mock_remover_class, tmp_path):
        """测试空目录处理"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        success, fail, results = batch_remove_watermarks(input_dir, output_dir)
        
        assert success == 0
        assert fail == 0
        assert len(results) == 0


class TestWatermarkDetector:
    """水印检测器测试"""
    
    def test_init(self):
        """测试初始化"""
        detector = WatermarkDetector()
        assert detector is not None
    
    @patch('watermark.cv2')
    def test_detect_returns_mask(self, mock_cv2):
        """测试检测返回掩码"""
        # Mock 输入图像
        mock_img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Mock 输出掩码
        mock_mask = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.inRange.return_value = mock_mask
        mock_cv2.cvtColor.return_value = mock_img
        mock_cv2.Canny.return_value = mock_mask
        mock_cv2.dilate.return_value = mock_mask
        mock_cv2.erode.return_value = mock_mask
        mock_cv2.bitwise_or.return_value = mock_mask
        
        detector = WatermarkDetector()
        result = detector.detect(mock_img)
        
        assert result is not None
        assert mock_cv2.inRange.called
        assert mock_cv2.Canny.called


class TestWatermarkRemoverAdvanced:
    """WatermarkRemover 高级功能测试"""
    
    @patch('watermark.cv2')
    def test_auto_method_selection(self, mock_cv2):
        """测试自动方法选择"""
        mock_img = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.imread.return_value = mock_img
        mock_cv2.inRange.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.dilate.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.inpaint.return_value = mock_img
        mock_cv2.cvtColor.return_value = mock_img
        mock_cv2.Sobel.return_value = np.zeros((100, 100))
        
        remover = WatermarkRemover(method="auto")
        result = remover.remove(Path("input.png"), Path("output.png"))
        
        assert result is True
    
    @patch('watermark.cv2')
    def test_analyze_complexity(self, mock_cv2):
        """测试复杂度分析"""
        mock_img = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.cvtColor.return_value = np.zeros((100, 100))
        mock_cv2.Sobel.return_value = np.zeros((100, 100))
        
        remover = WatermarkRemover()
        complexity = remover._analyze_complexity(mock_img)
        
        assert 0 <= complexity <= 1


class TestPDFWatermarkFunctions:
    """PDF 水印处理函数测试（集成测试，需要实际依赖）"""
    
    def test_pdf_functions_exist(self):
        """测试 PDF 相关函数存在"""
        # 这些函数需要 fitz (PyMuPDF) 才能正常运行
        # 这里只测试它们存在且可导入
        assert callable(process_pdf_images)
        assert callable(images_to_pdf)
        assert callable(process_pdf_with_watermark_removal)


class TestWatermarkRemoverIntegration:
    """集成测试（需要实际文件）"""
    
    def test_sample_directory_exists(self):
        """测试样本目录存在"""
        sample_dir = Path(__file__).parent / "sample"
        assert sample_dir.exists()
        assert sample_dir.is_dir()
    
    def test_sample_watermark_exists(self):
        """测试水印样本图片存在"""
        sample_img = Path(__file__).parent / "sample_watermark.png"
        assert sample_img.exists()
