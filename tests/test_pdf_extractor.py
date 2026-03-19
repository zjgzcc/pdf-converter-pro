"""
PDF 提取模块测试
🧪 青影【测试】负责验证
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import tempfile
import shutil

# 添加 core 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from pdf_extractor import (
    PDFExtractor,
    PDFMerger,
    PDFProcessor,
    pdf_to_images,
    images_to_pdf,
    extract_images_from_pdf
)


class TestPDFExtractor:
    """PDFExtractor 类测试"""
    
    def test_init_default_dpi(self):
        """测试初始化默认 DPI"""
        extractor = PDFExtractor()
        assert extractor.dpi == 300
    
    def test_init_custom_dpi(self):
        """测试初始化自定义 DPI"""
        extractor = PDFExtractor(dpi=150)
        assert extractor.dpi == 150
    
    @patch('pdf_extractor.fitz')
    def test_pdf_to_images_success(self, mock_fitz, tmp_path):
        """测试 PDF 转图片成功"""
        # Mock PDF 文档
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        mock_page = MagicMock()
        mock_doc.__getitem__.return_value = mock_page
        
        mock_pixmap = MagicMock()
        mock_pixmap.width = 2480
        mock_pixmap.height = 3508
        mock_pixmap.save = MagicMock()
        mock_page.get_pixmap.return_value = mock_pixmap
        
        mock_fitz.open.return_value = mock_doc
        
        extractor = PDFExtractor(dpi=300)
        output_dir = tmp_path / "output"
        
        success, fail, results = extractor.pdf_to_images(
            Path("test.pdf"),
            output_dir
        )
        
        assert success == 3
        assert fail == 0
        assert len(results) == 3
        assert mock_fitz.open.called
        assert mock_pixmap.save.called
    
    @patch('pdf_extractor.fitz')
    def test_pdf_to_images_specific_pages(self, mock_fitz, tmp_path):
        """测试转换指定页码"""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        mock_page = MagicMock()
        mock_doc.__getitem__.return_value = mock_page
        
        mock_pixmap = MagicMock()
        mock_pixmap.save = MagicMock()
        mock_page.get_pixmap.return_value = mock_pixmap
        
        mock_fitz.open.return_value = mock_doc
        
        extractor = PDFExtractor()
        output_dir = tmp_path / "output"
        
        success, fail, results = extractor.pdf_to_images(
            Path("test.pdf"),
            output_dir,
            pages=[1, 3, 5]  # 只转换第 1、3、5 页
        )
        
        assert success == 3
        assert mock_doc.__getitem__.call_count == 3
    
    @patch('pdf_extractor.fitz')
    def test_pdf_to_images_invalid_pdf(self, mock_fitz, tmp_path):
        """测试无效 PDF 文件"""
        mock_fitz.open.side_effect = Exception("Invalid PDF")
        
        extractor = PDFExtractor()
        output_dir = tmp_path / "output"
        
        success, fail, results = extractor.pdf_to_images(
            Path("invalid.pdf"),
            output_dir
        )
        
        assert success == 0
        assert fail == 0
        assert results == []
    
    @patch('pdf_extractor.fitz')
    def test_extract_embedded_images_success(self, mock_fitz, tmp_path):
        """测试提取嵌入图片"""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        
        mock_page = MagicMock()
        # Mock 2 张图片
        mock_page.get_images.return_value = [
            (1, "img1", 100, 100, 8, "RGB"),
            (2, "img2", 200, 200, 8, "RGB"),
        ]
        mock_doc.__getitem__.return_value = mock_page
        
        mock_doc.extract_image.return_value = {
            "image": b"fake_image_data",
            "ext": "png"
        }
        
        mock_fitz.open.return_value = mock_doc
        
        extractor = PDFExtractor()
        output_dir = tmp_path / "output"
        
        success, fail, results = extractor.extract_embedded_images(
            Path("test.pdf"),
            output_dir
        )
        
        assert success == 4  # 2 页 x 2 张图片
        assert len(results) == 4


class TestPDFMerger:
    """PDFMerger 类测试"""
    
    def test_init_default_page_size(self):
        """测试初始化默认页面大小"""
        merger = PDFMerger()
        assert merger.width == 595
        assert merger.height == 842
    
    def test_init_custom_page_size(self):
        """测试初始化自定义页面大小"""
        merger = PDFMerger(page_size="Letter")
        assert merger.width == 612
        assert merger.height == 792
    
    def test_init_tuple_page_size(self):
        """测试初始化元组页面大小"""
        merger = PDFMerger(page_size=(500, 700))
        assert merger.width == 500
        assert merger.height == 700
    
    @patch('pdf_extractor.fitz')
    @patch('pdf_extractor.Image')
    def test_images_to_pdf_success(self, mock_image, mock_fitz, tmp_path):
        """测试图片合并为 PDF 成功"""
        # 创建测试图片
        img_path = tmp_path / "test.png"
        img_path.touch()
        
        mock_img = MagicMock()
        mock_img.size = (1000, 1500)
        mock_image.open.return_value = mock_img
        
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.new_page.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        merger = PDFMerger()
        output_pdf = tmp_path / "output.pdf"
        
        result = merger.images_to_pdf(tmp_path, output_pdf)
        
        assert result is True
        mock_fitz.open.called
        mock_doc.new_page.called
        mock_page.insert_image.called
    
    @patch('pdf_extractor.fitz')
    def test_images_to_pdf_empty_directory(self, mock_fitz, tmp_path):
        """测试空目录"""
        merger = PDFMerger()
        output_pdf = tmp_path / "output.pdf"
        
        result = merger.images_to_pdf(tmp_path, output_pdf)
        
        assert result is False
    
    @patch('pdf_extractor.fitz')
    @patch('pdf_extractor.Image')
    def test_images_list_to_pdf_success(self, mock_image, mock_fitz, tmp_path):
        """测试图片列表合并为 PDF"""
        img_path = tmp_path / "test.png"
        img_path.touch()
        
        mock_img = MagicMock()
        mock_img.size = (1000, 1500)
        mock_image.open.return_value = mock_img
        
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.new_page.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        merger = PDFMerger()
        output_pdf = tmp_path / "output.pdf"
        
        result = merger.images_list_to_pdf([img_path], output_pdf)
        
        assert result is True


class TestPDFProcessor:
    """PDFProcessor 类测试"""
    
    def test_init(self):
        """测试初始化"""
        processor = PDFProcessor(dpi=300, page_size="A4")
        assert processor.extractor.dpi == 300
        assert processor.merger.width == 595
        assert processor.merger.height == 842
    
    @patch('pdf_extractor.PDFExtractor')
    @patch('pdf_extractor.PDFMerger')
    def test_process_with_callback(self, mock_merger_class, mock_extractor_class, tmp_path):
        """测试带回调的处理流程"""
        # Mock extractor
        mock_extractor = MagicMock()
        mock_extractor.pdf_to_images.return_value = (3, 0, [
            {"success": True, "output": str(tmp_path / "page_0001.png")},
            {"success": True, "output": str(tmp_path / "page_0002.png")},
            {"success": True, "output": str(tmp_path / "page_0003.png")},
        ])
        mock_extractor_class.return_value = mock_extractor
        
        # Mock merger
        mock_merger = MagicMock()
        mock_merger.images_list_to_pdf.return_value = True
        mock_merger_class.return_value = mock_merger
        
        # 创建测试图片
        for i in range(1, 4):
            (tmp_path / f"page_{i:04d}.png").touch()
        
        # 定义回调
        def callback(img_path):
            return img_path  # 返回原图
        
        processor = PDFProcessor()
        result = processor.process_with_callback(
            Path("input.pdf"),
            Path("output.pdf"),
            process_callback=callback,
            temp_dir=tmp_path
        )
        
        assert result is True
        mock_extractor.pdf_to_images.called
        mock_merger.images_list_to_pdf.called
    
    @patch('pdf_extractor.PDFExtractor')
    @patch('pdf_extractor.PDFMerger')
    def test_batch_process(self, mock_merger_class, mock_extractor_class, tmp_path):
        """测试批量处理"""
        # 创建测试 PDF
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        (input_dir / "test1.pdf").touch()
        (input_dir / "test2.pdf").touch()
        
        mock_extractor = MagicMock()
        mock_extractor.pdf_to_images.return_value = (1, 0, [
            {"success": True, "output": str(tmp_path / "page.png")}
        ])
        mock_extractor_class.return_value = mock_extractor
        
        mock_merger = MagicMock()
        mock_merger.images_list_to_pdf.return_value = True
        mock_merger_class.return_value = mock_merger
        
        processor = PDFProcessor()
        success, fail = processor.batch_process(input_dir, output_dir)
        
        assert success == 2
        assert fail == 0


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    @patch('pdf_extractor.PDFExtractor')
    def test_pdf_to_images_function(self, mock_extractor_class, tmp_path):
        """测试 pdf_to_images 便捷函数"""
        mock_extractor = MagicMock()
        mock_extractor.pdf_to_images.return_value = (3, 0, [])
        mock_extractor_class.return_value = mock_extractor
        
        success, fail = pdf_to_images(
            Path("test.pdf"),
            tmp_path / "output",
            dpi=300
        )
        
        assert success == 3
        assert fail == 0
    
    @patch('pdf_extractor.PDFMerger')
    def test_images_to_pdf_function(self, mock_merger_class, tmp_path):
        """测试 images_to_pdf 便捷函数"""
        mock_merger = MagicMock()
        mock_merger.images_to_pdf.return_value = True
        mock_merger_class.return_value = mock_merger
        
        result = images_to_pdf(
            tmp_path / "images",
            tmp_path / "output.pdf",
            page_size="A4"
        )
        
        assert result is True
    
    @patch('pdf_extractor.PDFExtractor')
    def test_extract_images_from_pdf_function(self, mock_extractor_class, tmp_path):
        """测试 extract_images_from_pdf 便捷函数"""
        mock_extractor = MagicMock()
        mock_extractor.extract_embedded_images.return_value = (5, 0, [])
        mock_extractor_class.return_value = mock_extractor
        
        success, fail = extract_images_from_pdf(
            Path("test.pdf"),
            tmp_path / "output"
        )
        
        assert success == 5
        assert fail == 0


class TestIntegration:
    """集成测试"""
    
    def test_sample_pdf_exists(self):
        """测试样本 PDF 文件存在"""
        sample_pdf = Path(__file__).parent / "sample_contract.pdf"
        assert sample_pdf.exists()
    
    def test_sample_invoice_exists(self):
        """测试样本发票 PDF 存在"""
        sample_pdf = Path(__file__).parent / "sample_invoice.pdf"
        assert sample_pdf.exists()
    
    def test_sample_scan_exists(self):
        """测试样本扫描 PDF 存在"""
        sample_pdf = Path(__file__).parent / "sample_scan.pdf"
        assert sample_pdf.exists()
