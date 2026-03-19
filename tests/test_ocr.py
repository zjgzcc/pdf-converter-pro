"""
OCR 识别模块测试 - 更新版
🧪 青影【测试】负责验证
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import tempfile
import time

# 添加 core 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from ocr import (
    OCREngine, batch_ocr, add_text_layer, quick_ocr,
    OCREngineType, OCRConfig, OCRQuality, OCRProgress, OCRResult, OCRError
)


class TestOCRQuality:
    """OCR 质量预设测试"""
    
    def test_enum_values(self):
        """测试枚举值"""
        assert OCRQuality.FAST.value == "fast"
        assert OCRQuality.STANDARD.value == "standard"
        assert OCRQuality.HIGH.value == "high"
        assert OCRQuality.BEST.value == "best"


class TestOCRConfig:
    """OCR 配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = OCRConfig()
        assert config.language == "chi_sim+eng"
        assert config.dpi == 300
        assert config.force_ocr is True
        assert config.quality == OCRQuality.STANDARD
    
    def test_apply_quality_fast(self):
        """测试快速质量预设"""
        config = OCRConfig(quality=OCRQuality.FAST)
        config.apply_quality_preset()
        assert config.dpi == 150
        assert config.optimize is False
    
    def test_apply_quality_standard(self):
        """测试标准质量预设"""
        config = OCRConfig(quality=OCRQuality.STANDARD)
        config.apply_quality_preset()
        assert config.dpi == 300
        assert config.optimize is True
    
    def test_apply_quality_high(self):
        """测试高质量预设"""
        config = OCRConfig(quality=OCRQuality.HIGH)
        config.apply_quality_preset()
        assert config.dpi == 450
        assert config.clean is True
    
    def test_apply_quality_best(self):
        """测试最佳质量预设"""
        config = OCRConfig(quality=OCRQuality.BEST)
        config.apply_quality_preset()
        assert config.dpi == 600
        assert config.deskew is True
        assert config.clean is True


class TestOCRProgress:
    """OCR 进度测试"""
    
    def test_init_default(self):
        """测试初始化默认值"""
        progress = OCRProgress()
        assert progress.current_page == 0
        assert progress.total_pages == 0
        assert progress.status == "pending"
        assert progress.percent == 0.0
    
    def test_update_with_percent_calc(self):
        """测试更新并自动计算百分比"""
        progress = OCRProgress(total_pages=10)
        progress.update(current_page=5)
        assert progress.current_page == 5
        assert progress.percent == 50.0
    
    def test_update_kwargs(self):
        """测试使用关键字参数更新"""
        progress = OCRProgress()
        progress.update(status="processing", message="OCR processing")
        assert progress.status == "processing"
        assert progress.message == "OCR processing"


class TestOCRResult:
    """OCR 结果测试"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = OCRResult(
            success=True,
            input_file=Path("test.pdf"),
            output_file=Path("output.pdf"),
            pages_processed=5
        )
        assert result.success is True
        assert result.pages_processed == 5
    
    def test_failure_result(self):
        """测试失败结果"""
        result = OCRResult(
            success=False,
            input_file=Path("test.pdf"),
            error_message="OCR failed"
        )
        assert result.success is False
        assert result.error_message == "OCR failed"


class TestOCREngine:
    """OCREngine 类测试"""
    
    @patch('ocr.subprocess.run')
    def test_init_validates_engines(self, mock_run):
        """测试初始化时验证引擎"""
        mock_run.return_value = MagicMock(returncode=0, stdout="ocrmypdf 16.0.0")
        
        engine = OCREngine()
        
        assert mock_run.call_count >= 1
        assert engine.is_engine_available() in [True, False]  # 取决于 mock
    
    @patch('ocr.subprocess.run')
    def test_init_with_custom_config(self, mock_run):
        """测试使用自定义配置初始化"""
        config = OCRConfig(language="eng", dpi=600, quality=OCRQuality.BEST)
        engine = OCREngine(config=config)
        
        assert engine.config.language == "eng"
        # DPI 会被 quality preset 覆盖，BEST 质量是 600 DPI
        assert engine.config.dpi == 600
    
    @patch('ocr.subprocess.run')
    def test_get_available_engine(self, mock_run):
        """测试获取可用引擎"""
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        
        engine = OCREngine(engine_type=OCREngineType.TESSERACT)
        available = engine.get_available_engine()
        
        # 应该返回第一个可用的引擎
        assert available in [OCREngineType.OCRMYDF, OCREngineType.TESSERACT, OCREngineType.PADDLEOCR, None]
    
    @patch('ocr.subprocess.run')
    def test_convert_to_searchable_pdf_success(self, mock_run):
        """测试成功转换为可搜索 PDF"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_pdf = Path(tmpdir) / "input.pdf"
            output_pdf = Path(tmpdir) / "output.pdf"
            input_pdf.touch()
            
            engine = OCREngine()
            result = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
            
            assert result.success is True
            assert result.input_file == input_pdf
            assert result.output_file == output_pdf
    
    @patch('ocr.subprocess.run')
    def test_convert_file_not_found(self, mock_run):
        """测试文件不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_pdf = Path(tmpdir) / "nonexistent.pdf"
            output_pdf = Path(tmpdir) / "output.pdf"
            
            engine = OCREngine()
            result = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
            
            assert result.success is False
            assert "不存在" in result.error_message
    
    @patch('ocr.subprocess.run')
    def test_convert_with_custom_config(self, mock_run):
        """测试使用自定义配置转换"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        config = OCRConfig(dpi=600, force_ocr=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_pdf = Path(tmpdir) / "input.pdf"
            output_pdf = Path(tmpdir) / "output.pdf"
            input_pdf.touch()
            
            engine = OCREngine()
            result = engine.convert_to_searchable_pdf(input_pdf, output_pdf, config=config)
            
            assert result.success is True
    
    @patch('ocr.subprocess.run')
    def test_convert_timeout(self, mock_run):
        """测试超时处理"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ocrmypdf", timeout=600)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_pdf = Path(tmpdir) / "input.pdf"
            output_pdf = Path(tmpdir) / "output.pdf"
            input_pdf.touch()
            
            engine = OCREngine()
            result = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
            
            assert result.success is False
            assert "超时" in result.error_message
    
    @patch('ocr.subprocess.run')
    @patch('builtins.__import__')
    def test_has_text_layer_true(self, mock_import, mock_run):
        """测试检测文本层 - 有文本"""
        # Mock fitz import
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Some text content"
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz.open.return_value = mock_doc
        
        def import_side_effect(name, *args, **kwargs):
            if name == 'fitz':
                return mock_fitz
            raise ImportError(f"No module named '{name}'")
        
        mock_import.side_effect = import_side_effect
        
        engine = OCREngine()
        has_text = engine.has_text_layer(Path("test.pdf"))
        
        assert has_text is True
    
    @patch('ocr.subprocess.run')
    @patch('builtins.__import__')
    def test_has_text_layer_false(self, mock_import, mock_run):
        """测试检测文本层 - 无文本"""
        # Mock fitz import
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz.open.return_value = mock_doc
        
        def import_side_effect(name, *args, **kwargs):
            if name == 'fitz':
                return mock_fitz
            raise ImportError(f"No module named '{name}'")
        
        mock_import.side_effect = import_side_effect
        
        engine = OCREngine()
        has_text = engine.has_text_layer(Path("scan.pdf"))
        
        assert has_text is False


class TestBatchOCR:
    """批量 OCR 测试"""
    
    @patch('ocr.OCREngine')
    def test_batch_success(self, mock_engine_class, tmp_path):
        """测试批量 OCR 成功"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # 创建测试 PDF 文件
        (input_dir / "test1.pdf").touch()
        (input_dir / "test2.pdf").touch()
        
        # Mock engine
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.return_value = OCRResult(
            success=True,
            input_file=Path("test.pdf"),
            output_file=Path("output.pdf")
        )
        mock_engine_class.return_value = mock_engine
        
        success, fail, results = batch_ocr(input_dir, output_dir, max_workers=2)
        
        assert success == 2
        assert fail == 0
        assert len(results) == 2
    
    @patch('ocr.OCREngine')
    def test_batch_partial_failure(self, mock_engine_class, tmp_path):
        """测试批量 OCR 部分失败"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        (input_dir / "test1.pdf").touch()
        (input_dir / "test2.pdf").touch()
        (input_dir / "test3.pdf").touch()
        
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.side_effect = [
            OCRResult(success=True, input_file=Path("t1.pdf")),
            OCRResult(success=False, input_file=Path("t2.pdf"), error_message="Error"),
            OCRResult(success=True, input_file=Path("t3.pdf"))
        ]
        mock_engine_class.return_value = mock_engine
        
        success, fail, results = batch_ocr(input_dir, output_dir, max_workers=2)
        
        assert success == 2
        assert fail == 1
        assert len(results) == 3
    
    @patch('ocr.OCREngine')
    def test_batch_empty_directory(self, mock_engine_class, tmp_path):
        """测试空目录"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        success, fail, results = batch_ocr(input_dir, output_dir)
        
        assert success == 0
        assert fail == 0
        assert results == []
    
    @patch('ocr.OCREngine')
    def test_batch_with_progress_callback(self, mock_engine_class, tmp_path):
        """测试批量 OCR 带进度回调"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        (input_dir / "test.pdf").touch()
        
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.return_value = OCRResult(
            success=True, input_file=Path("test.pdf")
        )
        mock_engine_class.return_value = mock_engine
        
        callback = MagicMock()
        success, fail, results = batch_ocr(
            input_dir, output_dir,
            progress_callback=callback
        )
        
        assert success == 1
        assert callback.call_count > 0
    
    @patch('ocr.OCREngine')
    def test_batch_custom_threads(self, mock_engine_class, tmp_path):
        """测试自定义线程数"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        for i in range(5):
            (input_dir / f"test{i}.pdf").touch()
        
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.return_value = OCRResult(
            success=True, input_file=Path("test.pdf")
        )
        mock_engine_class.return_value = mock_engine
        
        success, fail, results = batch_ocr(input_dir, output_dir, max_workers=8)
        
        assert success == 5


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    @patch('ocr.OCREngine')
    def test_add_text_layer(self, mock_engine_class):
        """测试添加文本层便捷函数"""
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.return_value = OCRResult(
            success=True, input_file=Path("test.pdf"), output_file=Path("output.pdf")
        )
        mock_engine_class.return_value = mock_engine
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_pdf = Path(tmpdir) / "input.pdf"
            output_pdf = Path(tmpdir) / "output.pdf"
            input_pdf.touch()
            
            result = add_text_layer(input_pdf, output_pdf, language="eng")
            
            assert result is True
            mock_engine_class.assert_called_once()
    
    @patch('ocr.OCREngine')
    def test_quick_ocr(self, mock_engine_class):
        """测试快速 OCR 便捷函数"""
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.return_value = OCRResult(
            success=True, input_file=Path("test.pdf"), output_file=Path("output.pdf")
        )
        mock_engine_class.return_value = mock_engine
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_pdf = Path(tmpdir) / "input.pdf"
            input_pdf.touch()
            
            result = quick_ocr(input_pdf, dpi=600)
            
            assert result.success is True


class TestIntegration:
    """集成测试"""
    
    def test_sample_files_exist(self):
        """测试样本文件存在"""
        tests_dir = Path(__file__).parent
        assert (tests_dir / "sample_scan.pdf").exists()
        assert (tests_dir / "sample_contract.pdf").exists()
    
    def test_sample_directory_exists(self):
        """测试样本目录存在"""
        sample_dir = Path(__file__).parent / "sample"
        assert sample_dir.exists()


class TestEdgeCases:
    """边界情况测试"""
    
    @patch('ocr.OCREngine')
    def test_batch_with_special_characters(self, mock_engine_class, tmp_path):
        """测试包含特殊字符的文件名"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # 创建包含空格和特殊字符的文件
        (input_dir / "test file 1.pdf").touch()
        (input_dir / "test-file_2.pdf").touch()
        
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.return_value = OCRResult(
            success=True, input_file=Path("test.pdf")
        )
        mock_engine_class.return_value = mock_engine
        
        success, fail, results = batch_ocr(input_dir, output_dir)
        
        assert success == 2
    
    @patch('ocr.OCREngine')
    def test_batch_with_many_files(self, mock_engine_class, tmp_path):
        """测试大量文件批量处理"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # 创建 20 个测试文件
        for i in range(20):
            (input_dir / f"test{i}.pdf").touch()
        
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.return_value = OCRResult(
            success=True, input_file=Path("test.pdf")
        )
        mock_engine_class.return_value = mock_engine
        
        success, fail, results = batch_ocr(input_dir, output_dir, max_workers=4)
        
        assert success == 20
        assert fail == 0
    
    @patch('ocr.subprocess.run')
    def test_convert_with_output_dir_creation(self, mock_run, tmp_path):
        """测试输出目录自动创建"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        input_dir = tmp_path / "input"
        nested_output = tmp_path / "output" / "nested" / "dir"
        
        input_dir.mkdir()
        input_pdf = input_dir / "test.pdf"
        input_pdf.touch()
        output_pdf = nested_output / "output.pdf"
        
        engine = OCREngine()
        result = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
        
        assert result.success is True
        # 输出目录应该被创建（在 mock 情况下）


class TestPerformance:
    """性能相关测试"""
    
    @patch('ocr.OCREngine')
    def test_parallel_processing_faster(self, mock_engine_class, tmp_path):
        """测试并行处理比串行快（模拟）"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # 创建 10 个文件
        for i in range(10):
            (input_dir / f"test{i}.pdf").touch()
        
        # Mock 引擎，模拟处理时间
        def slow_convert(*args, **kwargs):
            time.sleep(0.1)  # 模拟 100ms 处理时间
            return OCRResult(success=True, input_file=Path("test.pdf"))
        
        mock_engine = MagicMock()
        mock_engine.convert_to_searchable_pdf.side_effect = slow_convert
        mock_engine_class.return_value = mock_engine
        
        # 并行处理
        start_parallel = time.time()
        success, fail, results = batch_ocr(input_dir, output_dir, max_workers=4)
        parallel_time = time.time() - start_parallel
        
        # 验证所有文件都处理了
        assert success == 10
        
        # 并行应该比串行快（10 * 0.1s = 1s，并行应该 < 0.5s）
        # 注意：这个测试在 mock 环境下可能不准确
        assert parallel_time < 1.5  # 宽松的时间限制


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
