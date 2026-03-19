"""
PDF 转 WORD 转换模块测试
🧪 青影【测试】负责验证

测试覆盖：
- 基本转换功能
- PaddleOCR 版面恢复
- pdf2docx 备选方案
- 批量转换
- 进度追踪
- 错误处理
- 边界情况
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import tempfile
import json
from datetime import datetime

# 添加 core 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from converter import (
    PDF2WordConverter,
    batch_convert,
    ConvertMethod,
    ConvertError,
    ConvertProgress,
    BatchConvertResult,
    LayoutElement,
    convert_with_layout_recovery
)


class TestConvertMethod:
    """转换方法枚举测试"""
    
    def test_enum_values(self):
        """测试枚举值"""
        assert ConvertMethod.PADDLEOCR.value == "paddleocr"
        assert ConvertMethod.PDF2DOCX.value == "pdf2docx"
        assert ConvertMethod.FREEP2W.value == "freep2w"
    
    def test_enum_from_string(self):
        """测试从字符串创建枚举"""
        assert ConvertMethod("paddleocr") == ConvertMethod.PADDLEOCR
        assert ConvertMethod("pdf2docx") == ConvertMethod.PDF2DOCX
        assert ConvertMethod("freep2w") == ConvertMethod.FREEP2W


class TestPDF2WordConverter:
    """PDF2WordConverter 类测试"""
    
    def test_init_default_method(self):
        """测试初始化默认方法"""
        with patch('converter.subprocess.run'):
            converter = PDF2WordConverter()
            assert converter.method == ConvertMethod.PADDLEOCR
    
    def test_init_custom_method(self):
        """测试初始化自定义方法"""
        with patch('converter.subprocess.run'):
            converter = PDF2WordConverter(method=ConvertMethod.PDF2DOCX)
            assert converter.method == ConvertMethod.PDF2DOCX
            
            converter2 = PDF2WordConverter(method=ConvertMethod.FREEP2W)
            assert converter2.method == ConvertMethod.FREEP2W
    
    def test_init_with_fallback_methods(self):
        """测试初始化备选方法"""
        with patch('converter.subprocess.run'):
            fallbacks = [ConvertMethod.PDF2DOCX, ConvertMethod.FREEP2W]
            converter = PDF2WordConverter(fallback_methods=fallbacks)
            assert converter.fallback_methods == fallbacks
    
    def test_init_with_progress_callback(self):
        """测试初始化进度回调"""
        with patch('converter.subprocess.run'):
            callback = MagicMock()
            converter = PDF2WordConverter(progress_callback=callback)
            assert converter.progress_callback == callback
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('converter.shutil.copy2')
    def test_convert_paddleocr_success(self, mock_copy, mock_exists, mock_run):
        """测试 PaddleOCR 成功转换"""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Mock temp_dir.glob to return a DOCX file
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            output_docx = temp_path / "result.docx"
            output_docx.touch()  # Create the file
            
            mock_glob = MagicMock()
            mock_glob.return_value = [output_docx]
            
            with patch.object(Path, 'glob', mock_glob):
                converter = PDF2WordConverter()
                # Override _create_temp_dir to use our temp dir
                converter._temp_dir = temp_path
                
                result = converter.convert(
                    temp_path / "input.pdf",
                    temp_path / "output.docx"
                )
                
                assert result is True
                # 验证转换命令被调用（忽略 validate 调用）
                assert mock_run.call_count >= 1
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    def test_convert_paddleocr_failure(self, mock_exists, mock_run):
        """测试 PaddleOCR 转换失败"""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Conversion error"
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = PDF2WordConverter()
            result = converter.convert(
                Path(tmpdir) / "input.pdf",
                Path(tmpdir) / "output.docx"
            )
            
            assert result is False
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    def test_convert_paddleocr_timeout(self, mock_exists, mock_run):
        """测试转换超时"""
        import subprocess
        mock_exists.return_value = True
        # 只在第二次调用时超时（第一次是 validate）
        mock_run.side_effect = [MagicMock(returncode=0), subprocess.TimeoutExpired(cmd="paddleocr", timeout=600)]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = PDF2WordConverter()
            result = converter.convert(
                Path(tmpdir) / "input.pdf",
                Path(tmpdir) / "output.docx"
            )
            
            assert result is False
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    def test_convert_file_not_found(self, mock_exists, mock_run):
        """测试文件不存在"""
        mock_exists.return_value = False
        
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = PDF2WordConverter()
            
            with pytest.raises(ConvertError, match="输入文件不存在"):
                converter.convert(
                    Path(tmpdir) / "nonexistent.pdf",
                    Path(tmpdir) / "output.docx"
                )
    
    @patch('converter.subprocess.run')
    def test_convert_pdf2docx_success(self, mock_run, tmp_path):
        """测试 pdf2docx 成功转换"""
        # Mock subprocess for validation (return success)
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock pdf2docx 模块
        mock_pdf2docx_module = MagicMock()
        mock_converter_obj = MagicMock()
        
        # Create input file
        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_bytes(b'%PDF fake input')
        output_docx = tmp_path / "output.docx"
        
        def mock_convert(output_path):
            # Create the output file when convert is called
            Path(output_path).write_bytes(b'%PDF fake docx content')
        
        mock_converter_obj.convert.side_effect = mock_convert
        mock_pdf2docx_module.Converter.return_value = mock_converter_obj
        
        with patch.dict('sys.modules', {'pdf2docx': mock_pdf2docx_module}):
            converter = PDF2WordConverter(method=ConvertMethod.PDF2DOCX)
            result = converter.convert(
                input_pdf,
                output_docx
            )
            
            assert result is True
            mock_pdf2docx_module.Converter.assert_called()
            mock_converter_obj.convert.assert_called()
            mock_converter_obj.close.assert_called()
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    def test_convert_freep2w_not_installed(self, mock_exists, mock_run):
        """测试 FreeP2W 未安装"""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=1)
        
        with patch.dict('sys.modules', {'freep2w': None}):
            with tempfile.TemporaryDirectory() as tmpdir:
                converter = PDF2WordConverter(method=ConvertMethod.FREEP2W)
                result = converter.convert(
                    Path(tmpdir) / "input.pdf",
                    Path(tmpdir) / "output.docx"
                )
                
                assert result is False
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('converter.shutil.copy2')
    def test_convert_with_progress_callback(self, mock_copy, mock_exists, mock_run, tmp_path):
        """测试进度回调"""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        callback = MagicMock()
        
        output_docx = tmp_path / "result.docx"
        output_docx.touch()
        
        mock_glob = MagicMock()
        mock_glob.return_value = [output_docx]
        
        with patch.object(Path, 'glob', mock_glob):
            converter = PDF2WordConverter(progress_callback=callback)
            converter._temp_dir = tmp_path
            
            converter.convert(
                tmp_path / "input.pdf",
                output_docx
            )
            
            # 验证回调被调用
            assert callback.call_count > 0
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('converter.shutil.copy2')
    def test_convert_preserve_format_option(self, mock_copy, mock_exists, mock_run):
        """测试保持格式选项"""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            output_docx = temp_path / "result.docx"
            output_docx.touch()
            
            mock_glob = MagicMock()
            mock_glob.return_value = [output_docx]
            
            with patch.object(Path, 'glob', mock_glob):
                converter = PDF2WordConverter(
                    preserve_format=True,
                    layout_analysis=True,
                    table_detection=True
                )
                converter._temp_dir = temp_path
                
                converter.convert(
                    temp_path / "input.pdf",
                    temp_path / "output.docx"
                )
                
                # 验证命令包含版面分析参数
                if mock_run.call_args:
                    call_args = mock_run.call_args[0][0]
                    assert "--layout" in call_args
                    assert "--table" in call_args


class TestConvertProgress:
    """转换进度类测试"""
    
    def test_init_default(self):
        """测试初始化默认值"""
        progress = ConvertProgress()
        assert progress.current_page == 0
        assert progress.total_pages == 0
        assert progress.status == "pending"
    
    def test_init_with_total(self):
        """测试初始化总页数"""
        progress = ConvertProgress(total_pages=10)
        assert progress.total_pages == 10
    
    def test_update(self):
        """测试更新进度"""
        progress = ConvertProgress()
        progress.update(page=5, status="processing", message="Converting", method="paddleocr")
        
        assert progress.current_page == 5
        assert progress.status == "processing"
        assert progress.message == "Converting"
        assert progress.current_method == "paddleocr"


class TestBatchConvert:
    """批量转换函数测试"""
    
    @patch('converter.PDF2WordConverter')
    def test_batch_success(self, mock_converter_class, tmp_path):
        """测试批量转换成功"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # 创建测试 PDF 文件
        (input_dir / "test1.pdf").touch()
        (input_dir / "test2.pdf").touch()
        
        # Mock converter
        mock_converter = MagicMock()
        mock_converter.convert.return_value = True
        mock_converter_class.return_value = mock_converter
        
        result = batch_convert(input_dir, output_dir)
        
        assert isinstance(result, BatchConvertResult)
        assert result.total_files == 2
        assert result.success_count == 2
        assert result.fail_count == 0
        assert len(result.results) == 2
        assert mock_converter.convert.call_count == 2
    
    @patch('converter.PDF2WordConverter')
    def test_batch_partial_failure(self, mock_converter_class, tmp_path):
        """测试批量转换部分失败"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        (input_dir / "test1.pdf").touch()
        (input_dir / "test2.pdf").touch()
        (input_dir / "test3.pdf").touch()
        
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = [True, False, True]
        mock_converter_class.return_value = mock_converter
        
        result = batch_convert(input_dir, output_dir)
        
        assert isinstance(result, BatchConvertResult)
        assert result.total_files == 3
        assert result.success_count == 2
        assert result.fail_count == 1
        assert len(result.results) == 3
    
    @patch('converter.PDF2WordConverter')
    def test_batch_empty_directory(self, mock_converter_class, tmp_path):
        """测试空目录"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        result = batch_convert(input_dir, output_dir)
        
        assert isinstance(result, BatchConvertResult)
        assert result.total_files == 0
        assert result.success_count == 0
        assert result.fail_count == 0
        assert result.results == []
    
    @patch('converter.PDF2WordConverter')
    @patch('converter.ConvertProgress')
    def test_batch_with_progress_callback(self, mock_progress_class, mock_converter_class, tmp_path):
        """测试批量转换带进度回调"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        (input_dir / "test.pdf").touch()
        
        # Mock ConvertProgress
        mock_progress_instance = MagicMock()
        mock_progress_class.return_value = mock_progress_instance
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = True
        mock_converter_class.return_value = mock_converter
        
        callback = MagicMock()
        result = batch_convert(
            input_dir, output_dir,
            progress_callback=callback
        )
        
        assert isinstance(result, BatchConvertResult)
        assert result.success_count == 1
        # Callback is called by batch_convert directly
        assert callback.call_count > 0


class TestConverterIntegration:
    """集成测试"""
    
    def test_sample_directory_exists(self):
        """测试样本目录存在"""
        sample_dir = Path(__file__).parent / "sample"
        assert sample_dir.exists()
        assert sample_dir.is_dir()


class TestEdgeCases:
    """边界情况测试"""
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('converter.shutil.copy2')
    def test_convert_with_special_characters_in_path(self, mock_copy, mock_exists, mock_run, tmp_path):
        """测试包含特殊字符的路径"""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # 创建包含空格的路径
        special_dir = tmp_path / "test dir"
        special_dir.mkdir()
        input_pdf = special_dir / "input file.pdf"
        input_pdf.touch()
        output_docx = special_dir / "output file.docx"
        
        result_docx = special_dir / "result.docx"
        result_docx.touch()
        
        mock_glob = MagicMock()
        mock_glob.return_value = [result_docx]
        
        with patch.object(Path, 'glob', mock_glob):
            converter = PDF2WordConverter()
            converter._temp_dir = special_dir
            
            result = converter.convert(input_pdf, output_docx)
            
            assert result is True
    
    @patch('converter.PDF2WordConverter')
    def test_batch_with_many_files(self, mock_converter_class, tmp_path):
        """测试大量文件批量处理"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # 创建 10 个测试文件
        for i in range(10):
            (input_dir / f"test{i}.pdf").touch()
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = True
        mock_converter_class.return_value = mock_converter
        
        result = batch_convert(input_dir, output_dir)
        
        assert isinstance(result, BatchConvertResult)
        assert result.success_count == 10
        assert result.fail_count == 0
        assert len(result.results) == 10
        assert mock_converter.convert.call_count == 10


class TestLayoutElement:
    """版面元素测试"""
    
    def test_layout_element_creation(self):
        """测试版面元素创建"""
        element = LayoutElement(
            type="text",
            bbox=(10, 20, 100, 200),
            content="Sample text",
            confidence=0.95,
            page=1
        )
        
        assert element.type == "text"
        assert element.bbox == (10, 20, 100, 200)
        assert element.content == "Sample text"
        assert element.confidence == 0.95
        assert element.page == 1
    
    def test_layout_element_default_values(self):
        """测试版面元素默认值"""
        element = LayoutElement(
            type="image",
            bbox=(0, 0, 50, 50)
        )
        
        assert element.content is None
        assert element.confidence == 0.0
        assert element.page == 0
    
    def test_layout_element_types(self):
        """测试不同版面元素类型"""
        types = ["text", "image", "table", "equation"]
        
        for elem_type in types:
            element = LayoutElement(type=elem_type, bbox=(0, 0, 10, 10))
            assert element.type == elem_type


class TestBatchConvertResult:
    """批量转换结果测试"""
    
    def test_result_init(self):
        """测试结果初始化"""
        result = BatchConvertResult()
        
        assert result.total_files == 0
        assert result.success_count == 0
        assert result.fail_count == 0
        assert result.results == []
        assert result.duration_seconds == 0.0
    
    def test_add_result_success(self):
        """测试添加成功结果"""
        result = BatchConvertResult()
        result.add_result("test1.pdf", True)
        
        assert result.success_count == 1
        assert result.fail_count == 0
        assert len(result.results) == 1
        assert result.results[0]["status"] == "success"
    
    def test_add_result_failure(self):
        """测试添加失败结果"""
        result = BatchConvertResult()
        result.add_result("test2.pdf", False, "Error message")
        
        assert result.success_count == 0
        assert result.fail_count == 1
        assert len(result.results) == 1
        assert result.results[0]["status"] == "failed"
        assert result.results[0]["error"] == "Error message"
    
    def test_to_dict(self):
        """测试转为字典"""
        result = BatchConvertResult()
        result.total_files = 10
        result.duration_seconds = 120.5
        result.start_time = datetime(2026, 3, 19, 10, 0, 0)
        result.end_time = datetime(2026, 3, 19, 10, 2, 0)
        
        # add_result 会自动更新 success_count 和 fail_count
        result.add_result("test1.pdf", True)
        result.add_result("test2.pdf", True)
        result.add_result("test3.pdf", True)
        result.add_result("test4.pdf", True)
        result.add_result("test5.pdf", True)
        result.add_result("test6.pdf", True)
        result.add_result("test7.pdf", True)
        result.add_result("test8.pdf", True)
        result.add_result("test9.pdf", False, "Failed 1")
        result.add_result("test10.pdf", False, "Failed 2")
        
        data = result.to_dict()
        
        assert data["total_files"] == 10
        assert data["success_count"] == 8
        assert data["fail_count"] == 2
        assert abs(data["success_rate"] - 80.0) < 0.01
        assert data["duration_seconds"] == 120.5
        assert "start_time" in data
        assert "end_time" in data
    
    def test_save_report(self, tmp_path):
        """测试保存报告"""
        result = BatchConvertResult()
        result.add_result("test.pdf", True)
        
        report_path = tmp_path / "report.json"
        result.save_report(report_path)
        
        assert report_path.exists()
        
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] == "success"


class TestConvertWithOptions:
    """带选项转换测试"""
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('converter.shutil.copy2')
    def test_convert_with_layout_analysis(self, mock_copy, mock_exists, mock_run, tmp_path):
        """测试启用版面分析"""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        output_docx = tmp_path / "result.docx"
        output_docx.touch()
        
        mock_glob = MagicMock()
        mock_glob.return_value = [output_docx]
        
        with patch.object(Path, 'glob', mock_glob):
            converter = PDF2WordConverter(layout_analysis=True)
            converter._temp_dir = tmp_path
            
            result = converter.convert(
                tmp_path / "input.pdf",
                tmp_path / "output.docx"
            )
            
            assert result is True
            # 验证命令包含版面分析参数
            if mock_run.call_args:
                call_args = mock_run.call_args[0][0]
                assert "--layout" in call_args
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('converter.shutil.copy2')
    def test_convert_with_table_detection(self, mock_copy, mock_exists, mock_run, tmp_path):
        """测试启用表格检测"""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        output_docx = tmp_path / "result.docx"
        output_docx.touch()
        
        mock_glob = MagicMock()
        mock_glob.return_value = [output_docx]
        
        with patch.object(Path, 'glob', mock_glob):
            converter = PDF2WordConverter(table_detection=True)
            converter._temp_dir = tmp_path
            
            result = converter.convert(
                tmp_path / "input.pdf",
                tmp_path / "output.docx"
            )
            
            assert result is True
            # 验证命令包含表格检测参数
            if mock_run.call_args:
                call_args = mock_run.call_args[0][0]
                assert "--table" in call_args
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('converter.shutil.copy2')
    def test_convert_with_image_extraction(self, mock_copy, mock_exists, mock_run, tmp_path):
        """测试启用图片提取"""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        output_docx = tmp_path / "result.docx"
        output_docx.touch()
        
        mock_glob = MagicMock()
        mock_glob.return_value = [output_docx]
        
        with patch.object(Path, 'glob', mock_glob):
            converter = PDF2WordConverter(image_extraction=True)
            converter._temp_dir = tmp_path
            
            result = converter.convert(
                tmp_path / "input.pdf",
                tmp_path / "output.docx"
            )
            
            assert result is True
            # 验证命令包含图片提取参数
            if mock_run.call_args:
                call_args = mock_run.call_args[0][0]
                assert "--extract_img" in call_args


class TestConvertProgressEnhanced:
    """增强版进度追踪测试"""
    
    def test_progress_with_percentage(self):
        """测试带百分比的进度"""
        progress = ConvertProgress()
        progress.update(page=5, percentage=50.0)
        
        assert progress.current_page == 5
        assert progress.percentage == 50.0
    
    def test_progress_with_eta(self):
        """测试带预估时间的进度"""
        progress = ConvertProgress()
        progress.update(page=3, eta=120.5)
        
        assert progress.current_page == 3
        assert progress.eta_seconds == 120.5
    
    def test_progress_complete_update(self):
        """测试完整进度更新"""
        progress = ConvertProgress()
        progress.update(
            page=10,
            status="completed",
            message="转换完成",
            method="paddleocr",
            percentage=100.0,
            eta=0.0
        )
        
        assert progress.current_page == 10
        assert progress.status == "completed"
        assert progress.message == "转换完成"
        assert progress.current_method == "paddleocr"
        assert progress.percentage == 100.0
        assert progress.eta_seconds == 0.0


class TestBatchConvertEnhanced:
    """增强版批量转换测试"""
    
    @patch('converter.PDF2WordConverter')
    def test_batch_with_parallel_option(self, mock_converter_class, tmp_path):
        """测试并行批量转换"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # 创建 5 个测试文件
        for i in range(5):
            (input_dir / f"test{i}.pdf").touch()
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = True
        mock_converter_class.return_value = mock_converter
        
        result = batch_convert(
            input_dir,
            output_dir,
            parallel=True,
            max_workers=2
        )
        
        assert result.total_files == 5
        assert result.success_count == 5
        assert result.fail_count == 0
        assert result.duration_seconds >= 0
    
    @patch('converter.PDF2WordConverter')
    def test_batch_with_custom_options(self, mock_converter_class, tmp_path):
        """测试带自定义选项的批量转换"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        (input_dir / "test.pdf").touch()
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = True
        mock_converter_class.return_value = mock_converter
        
        result = batch_convert(
            input_dir,
            output_dir,
            method=ConvertMethod.PDF2DOCX,
            preserve_format=True,
            layout_analysis=True,
            table_detection=True,
            image_extraction=True
        )
        
        assert result.total_files == 1
        assert result.success_count == 1
        
        # 验证转换器使用正确的参数初始化
        init_call = mock_converter_class.call_args
        assert init_call[1]['method'] == ConvertMethod.PDF2DOCX
        assert init_call[1]['preserve_format'] is True
        assert init_call[1]['layout_analysis'] is True


class TestLayoutRecovery:
    """版面恢复功能测试"""
    
    @patch('converter.PDF2WordConverter')
    @patch('converter.subprocess.run')
    def test_convert_with_layout_recovery(self, mock_run, mock_converter_class, tmp_path):
        """测试带版面恢复的转换"""
        mock_run.return_value = MagicMock(returncode=0)
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = True
        mock_converter.analyze_layout.return_value = []
        mock_converter_class.return_value = mock_converter
        
        input_pdf = tmp_path / "input.pdf"
        input_pdf.touch()
        output_docx = tmp_path / "output.docx"
        
        result = convert_with_layout_recovery(input_pdf, output_docx)
        
        assert result is True
        mock_converter.analyze_layout.assert_called_once()
        mock_converter.convert.assert_called_once()
    
    def test_analyze_layout_interface(self, tmp_path):
        """测试版面分析接口"""
        # 这个测试需要 PyMuPDF，这里只测试接口存在性
        converter = PDF2WordConverter()
        
        # 验证方法存在
        assert hasattr(converter, 'analyze_layout')
        assert callable(converter.analyze_layout)
        
        # 对于不存在的文件，应该返回空列表
        elements = converter.analyze_layout(tmp_path / "nonexistent.pdf")
        assert isinstance(elements, list)


class TestFallbackMechanism:
    """备选方案机制测试"""
    
    @patch('converter.subprocess.run')
    def test_fallback_to_pdf2docx(self, mock_run, tmp_path):
        """测试自动降级到 pdf2docx"""
        # 主方法失败
        paddleocr_result = MagicMock()
        paddleocr_result.returncode = 1
        paddleocr_result.stderr = "PaddleOCR error"
        mock_run.return_value = paddleocr_result
        
        # Mock pdf2docx 模块 - 让它成功创建文件
        mock_pdf2docx_module = MagicMock()
        mock_converter_obj = MagicMock()
        
        # Create input file
        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_bytes(b'%PDF fake input')
        output_docx = tmp_path / "output.docx"
        
        def mock_convert(output_path):
            # Create the output file when convert is called
            Path(output_path).write_bytes(b'%PDF fake docx content')
        
        mock_converter_obj.convert.side_effect = mock_convert
        mock_pdf2docx_module.Converter.return_value = mock_converter_obj
        
        with patch.dict('sys.modules', {'pdf2docx': mock_pdf2docx_module}):
            converter = PDF2WordConverter(
                method=ConvertMethod.PADDLEOCR,
                fallback_methods=[ConvertMethod.PDF2DOCX]
            )
            result = converter.convert(
                input_pdf,
                output_docx
            )
            
            assert result is True
            # 验证尝试了备选方法
            mock_pdf2docx_module.Converter.assert_called()
    
    @patch('converter.subprocess.run')
    @patch('pathlib.Path.exists')
    def test_all_methods_fail(self, mock_exists, mock_run, tmp_path):
        """测试所有方法都失败"""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")
        
        # Mock pdf2docx 也失败
        mock_pdf2docx_module = MagicMock()
        mock_converter_obj = MagicMock()
        mock_converter_obj.convert.side_effect = Exception("pdf2docx error")
        mock_pdf2docx_module.Converter.return_value = mock_converter_obj
        
        with patch.dict('sys.modules', {'pdf2docx': mock_pdf2docx_module}):
            converter = PDF2WordConverter(
                method=ConvertMethod.PADDLEOCR,
                fallback_methods=[ConvertMethod.PDF2DOCX]
            )
            result = converter.convert(
                tmp_path / "input.pdf",
                tmp_path / "output.docx"
            )
            
            assert result is False
