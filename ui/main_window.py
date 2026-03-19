"""
主窗口 UI - 现代优化版 v2.0
🎨 橙影【设计】

PyQt6 界面 - 现代 UI 风格
功能：
1. 连接所有核心功能（去水印/OCR/WORD 转换）
2. 支持功能选项单独或组合使用
3. 实现拖拽文件处理和实时进度
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QGroupBox, QComboBox, QTextEdit, QCheckBox,
    QFrame, QScrollArea, QSplitter, QListWidget, QListWidgetItem,
    QStatusBar, QToolBar, QMenu, QMessageBox, QDialog,
    QRadioButton, QButtonGroup, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QPoint, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon, QFont, QPalette, QColor
from pathlib import Path
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

from .history_manager import HistoryManager
from .file_preview_widget import FilePreviewWidget


class WorkerThread(QThread):
    """后台工作线程 - 支持单文件和批量处理"""
    progress = pyqtSignal(int, str)  # 进度百分比，状态信息
    file_progress = pyqtSignal(str, int, str)  # 文件名，进度，状态
    finished = pyqtSignal(bool, str, int, int)  # 是否成功，结果信息，成功数，失败数
    
    def __init__(self, input_files: List[Path], output_dir: Path, options: Dict[str, Any]):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.options = options
        self._stopped = False
    
    def stop(self):
        """停止处理"""
        self._stopped = True
    
    def run(self):
        """执行处理任务"""
        try:
            from core.watermark import WatermarkRemover, batch_remove_watermarks
            from core.ocr import OCREngine, OCREngineType, batch_ocr
            from core.converter import PDF2WordConverter, ConvertMethod, batch_convert
            from core.pipeline import ProcessingPipeline, create_pipeline, PipelineProgress
            
            total_files = len(self.input_files)
            success_count = 0
            fail_count = 0
            
            # 检查是否启用了任何功能
            enable_watermark = self.options.get("remove_watermark", False)
            enable_ocr = self.options.get("do_ocr", False)
            enable_word = self.options.get("convert_to_word", False)
            
            if not any([enable_watermark, enable_ocr, enable_word]):
                self.progress.emit(100, "⚠️ 未选择任何处理功能")
                self.finished.emit(False, "请至少选择一个处理功能", 0, 0)
                return
            
            # 构建处理流程描述
            steps = []
            if enable_watermark:
                steps.append("🧹 去水印")
            if enable_ocr:
                steps.append("🔍 OCR")
            if enable_word:
                steps.append("📝 WORD")
            
            process_desc = " → ".join(steps)
            self.progress.emit(5, f"🚀 开始处理：{process_desc}")
            
            # 使用统一流水线处理
            pipeline = ProcessingPipeline(
                remove_watermark=enable_watermark,
                watermark_method=self.options.get("watermark_method", "auto"),
                ocr_enabled=enable_ocr,
                ocr_engine=OCREngineType(self.options.get("ocr_engine", "ocrmypdf")),
                ocr_language=self.options.get("ocr_lang", "chi_sim+eng"),
                convert_method=ConvertMethod(self.options.get("convert_method", "paddleocr")),
                preserve_format=self.options.get("preserve_format", True),
                progress_callback=lambda p: self._on_pipeline_progress(p, total_files)
            )
            
            # 创建输出子目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if enable_word:
                word_dir = self.output_dir / f"word_{timestamp}"
                word_dir.mkdir(parents=True, exist_ok=True)
            if enable_ocr:
                ocr_dir = self.output_dir / f"ocr_{timestamp}"
                ocr_dir.mkdir(parents=True, exist_ok=True)
            if enable_watermark:
                watermark_dir = self.output_dir / f"clean_{timestamp}"
                watermark_dir.mkdir(parents=True, exist_ok=True)
            
            # 逐个处理文件
            for idx, input_file in enumerate(self.input_files):
                if self._stopped:
                    self.progress.emit(100, "⚠️ 已停止处理")
                    self.finished.emit(False, "用户停止", success_count, fail_count)
                    return
                
                self.file_progress.emit(input_file.name, 0, "⏳ 处理中")
                
                try:
                    # 确定输出文件
                    if enable_word:
                        output_file = word_dir / f"{input_file.stem}.docx"
                    elif enable_ocr:
                        output_file = ocr_dir / f"searchable_{input_file.name}"
                    else:
                        output_file = watermark_dir / f"clean_{input_file.name}"
                    
                    # 处理单个文件
                    result = pipeline.process_single(input_file, output_file)
                    
                    if result.success:
                        success_count += 1
                        self.file_progress.emit(input_file.name, 100, "✅ 完成")
                    else:
                        fail_count += 1
                        self.file_progress.emit(input_file.name, 100, f"❌ {result.error_message}")
                    
                    # 更新总体进度
                    overall_progress = int(((idx + 1) / total_files) * 90) + 10
                    self.progress.emit(overall_progress, f"📊 已处理 {idx + 1}/{total_files} 个文件")
                    
                except Exception as e:
                    fail_count += 1
                    self.file_progress.emit(input_file.name, 100, f"❌ 错误：{str(e)}")
                    self.progress.emit(overall_progress, f"❌ {input_file.name}: {str(e)}")
            
            # 完成
            self.progress.emit(100, f"🎉 全部完成！成功：{success_count}, 失败：{fail_count}")
            self.finished.emit(True, "处理完成", success_count, fail_count)
            
        except Exception as e:
            self.progress.emit(100, f"❌ 错误：{str(e)}")
            self.finished.emit(False, str(e), 0, 0)
    
    def _on_pipeline_progress(self, progress: Any, total_files: int):
        """处理流水线进度回调"""
        try:
            msg = f"{progress.stage.value}: {progress.message}"
            pct = int(progress.overall_progress * 90) + 10
            self.progress.emit(pct, msg)
        except:
            pass


class DropArea(QFrame):
    """拖拽区域组件 - 增强版"""
    
    files_dropped = pyqtSignal(list)  # 文件路径列表
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._is_drag_over = False
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setObjectName("drop_area")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(180)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 拖拽图标
        icon_label = QLabel("📥")
        icon_label.setStyleSheet("font-size: 56px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 主提示文字
        text_label = QLabel("将文件拖拽到此处")
        text_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #6c5ce7;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        # 副提示文字
        subtext_label = QLabel("支持 PDF、PNG、JPG 等格式\n支持单个文件或整个目录")
        subtext_label.setStyleSheet("font-size: 14px; color: #636e72;")
        subtext_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtext_label)
        
        # 应用初始样式
        self._update_style(False)
    
    def _update_style(self, is_hover: bool):
        """更新样式"""
        if is_hover:
            self.setStyleSheet("""
                QFrame#drop_area {
                    background-color: #f0f0ff;
                    border: 3px dashed #6c5ce7;
                    border-radius: 15px;
                    padding: 30px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#drop_area {
                    background-color: #ffffff;
                    border: 3px dashed #dfe6e9;
                    border-radius: 15px;
                    padding: 30px;
                }
            """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._is_drag_over = True
            self._update_style(True)
        else:
            event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """拖拽移动"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """拖拽离开"""
        self._is_drag_over = False
        self._update_style(False)
    
    def dropEvent(self, event: QDropEvent):
        """文件放置"""
        self._is_drag_over = False
        self._update_style(False)
        
        urls = event.mimeData().urls()
        file_paths = []
        
        for url in urls:
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.is_file():
                    # 检查文件类型
                    if path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                        file_paths.append(path)
                elif path.is_dir():
                    # 目录：获取所有支持的文件
                    for ext in ['*.pdf', '*.PDF', '*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                        file_paths.extend(path.glob(ext))
        
        if file_paths:
            self.files_dropped.emit([str(p) for p in file_paths])


class ProcessingOptionsWidget(QWidget):
    """处理选项组件 - 独立功能选择"""
    
    options_changed = pyqtSignal()  # 选项变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # ===== 去水印选项 =====
        watermark_group = QGroupBox("🧹 去除水印")
        watermark_layout = QVBoxLayout()
        watermark_layout.setSpacing(10)
        
        self.chk_watermark = QCheckBox("启用去水印功能")
        self.chk_watermark.setChecked(False)
        self.chk_watermark.stateChanged.connect(self._on_option_changed)
        watermark_layout.addWidget(self.chk_watermark)
        
        # 去水印方法选择
        wm_method_layout = QHBoxLayout()
        wm_method_layout.addWidget(QLabel("方法:"))
        self.combo_watermark = QComboBox()
        self.combo_watermark.addItems([
            "🤖 auto - 自动选择",
            "🔧 opencv - 传统方法（适合浅色水印）",
            "✨ iopaint - AI 方法（适合复杂水印）"
        ])
        self.combo_watermark.setEnabled(False)
        self.combo_watermark.currentIndexChanged.connect(self._on_option_changed)
        wm_method_layout.addWidget(self.combo_watermark)
        wm_method_layout.addStretch()
        watermark_layout.addLayout(wm_method_layout)
        
        # 说明文字
        wm_hint = QLabel("💡 适合去除文档中的浅色水印、背景图案")
        wm_hint.setStyleSheet("color: #636e72; font-size: 12px;")
        watermark_layout.addWidget(wm_hint)
        
        watermark_group.setLayout(watermark_layout)
        layout.addWidget(watermark_group)
        
        # 连接复选框到方法启用
        self.chk_watermark.toggled.connect(self.combo_watermark.setEnabled)
        
        # ===== OCR 选项 =====
        ocr_group = QGroupBox("🔍 OCR 识别")
        ocr_layout = QVBoxLayout()
        ocr_layout.setSpacing(10)
        
        self.chk_ocr = QCheckBox("启用 OCR 识别（转可搜索 PDF）")
        self.chk_ocr.setChecked(True)
        self.chk_ocr.stateChanged.connect(self._on_option_changed)
        ocr_layout.addWidget(self.chk_ocr)
        
        # OCR 引擎选择
        ocr_engine_layout = QHBoxLayout()
        ocr_engine_layout.addWidget(QLabel("引擎:"))
        self.combo_ocr_engine = QComboBox()
        self.combo_ocr_engine.addItems([
            "🚀 ocrmypdf - OCRmyPDF（推荐）",
            "🔧 tesseract - Tesseract",
            "⚡ paddleocr - PaddleOCR"
        ])
        self.combo_ocr_engine.setEnabled(True)
        self.combo_ocr_engine.currentIndexChanged.connect(self._on_option_changed)
        ocr_engine_layout.addWidget(self.combo_ocr_engine)
        ocr_engine_layout.addStretch()
        ocr_layout.addLayout(ocr_engine_layout)
        
        # OCR 语言选择
        ocr_lang_layout = QHBoxLayout()
        ocr_lang_layout.addWidget(QLabel("语言:"))
        self.combo_ocr_lang = QComboBox()
        self.combo_ocr_lang.addItems([
            "🇨🇳 中英文混合",
            "🇨🇳 仅中文",
            "🇺🇸 仅英文",
            "🌍 多语言"
        ])
        self.combo_ocr_lang.setEnabled(True)
        self.combo_ocr_lang.currentIndexChanged.connect(self._on_option_changed)
        ocr_lang_layout.addWidget(self.combo_ocr_lang)
        ocr_lang_layout.addStretch()
        ocr_layout.addLayout(ocr_lang_layout)
        
        # 说明文字
        ocr_hint = QLabel("💡 将扫描版 PDF 转为可搜索、可复制的 PDF")
        ocr_hint.setStyleSheet("color: #636e72; font-size: 12px;")
        ocr_layout.addWidget(ocr_hint)
        
        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)
        
        # ===== WORD 转换选项 =====
        word_group = QGroupBox("📝 转换为 WORD")
        word_layout = QVBoxLayout()
        word_layout.setSpacing(10)
        
        self.chk_word = QCheckBox("启用 WORD 转换（PDF → DOCX）")
        self.chk_word.setChecked(True)
        self.chk_word.stateChanged.connect(self._on_option_changed)
        word_layout.addWidget(self.chk_word)
        
        # 转换方法选择
        word_method_layout = QHBoxLayout()
        word_method_layout.addWidget(QLabel("方法:"))
        self.combo_convert = QComboBox()
        self.combo_convert.addItems([
            "⚡ pdf2docx - pdf2docx（推荐，稳定）",
            "🚀 paddleocr - PaddleOCR 版面恢复（复杂布局）",
            "✨ freep2w - FreeP2W（适合公式）"
        ])
        self.combo_convert.setEnabled(True)
        self.combo_convert.currentIndexChanged.connect(self._on_option_changed)
        word_method_layout.addWidget(self.combo_convert)
        word_method_layout.addStretch()
        word_layout.addLayout(word_method_layout)
        
        # 格式保持选项
        format_layout = QHBoxLayout()
        self.chk_preserve_format = QCheckBox("保持原始格式")
        self.chk_preserve_format.setChecked(True)
        self.chk_preserve_format.setEnabled(True)
        self.chk_preserve_format.stateChanged.connect(self._on_option_changed)
        format_layout.addWidget(self.chk_preserve_format)
        format_layout.addStretch()
        word_layout.addLayout(format_layout)
        
        # 说明文字
        word_hint = QLabel("💡 将 PDF 转换为可编辑的 WORD 文档")
        word_hint.setStyleSheet("color: #636e72; font-size: 12px;")
        word_layout.addWidget(word_hint)
        
        word_group.setLayout(word_layout)
        layout.addWidget(word_group)
        
        # 连接复选框到方法启用
        self.chk_word.toggled.connect(self.combo_convert.setEnabled)
        self.chk_word.toggled.connect(self.chk_preserve_format.setEnabled)
    
    def _on_option_changed(self):
        """选项变更"""
        self.options_changed.emit()
    
    def get_options(self) -> Dict[str, Any]:
        """获取当前选项"""
        # 解析 OCR 语言
        lang_map = {
            "🇨🇳 中英文混合": "chi_sim+eng",
            "🇨🇳 仅中文": "chi_sim",
            "🇺🇸 仅英文": "eng",
            "🌍 多语言": "chi_sim+eng+fra+deu+spa"
        }
        ocr_lang_text = self.combo_ocr_lang.currentText()
        ocr_lang = lang_map.get(ocr_lang_text, "chi_sim+eng")
        
        # 解析方法（从下拉框文本中提取引擎名称）
        wm_method_text = self.combo_watermark.currentText()
        # 从"🔧 auto - 自动选择（推荐）"中提取"auto"
        wm_method = wm_method_text.split()[1].lower().rstrip('-')
        
        ocr_engine_text = self.combo_ocr_engine.currentText()
        # 从"🚀 ocrmypdf - OCRmyPDF（推荐）"中提取"ocrmypdf"
        ocr_engine = ocr_engine_text.split()[1].lower().rstrip('-')
        
        convert_method_text = self.combo_convert.currentText()
        # 从"🚀 paddleocr - 版面恢复（推荐）"中提取"paddleocr"
        convert_method = convert_method_text.split()[1].lower().rstrip('-')
        
        return {
            "remove_watermark": self.chk_watermark.isChecked(),
            "watermark_method": wm_method,
            "do_ocr": self.chk_ocr.isChecked(),
            "ocr_engine": ocr_engine,
            "ocr_lang": ocr_lang,
            "convert_to_word": self.chk_word.isChecked(),
            "convert_method": convert_method,
            "preserve_format": self.chk_preserve_format.isChecked()
        }
    
    def reset_options(self):
        """重置选项到默认"""
        self.chk_watermark.setChecked(False)
        self.chk_ocr.setChecked(True)
        self.chk_word.setChecked(True)
        self.chk_preserve_format.setChecked(True)
        self.combo_watermark.setCurrentIndex(0)
        self.combo_ocr_engine.setCurrentIndex(0)
        self.combo_ocr_lang.setCurrentIndex(0)
        self.combo_convert.setCurrentIndex(0)


class MainWindow(QMainWindow):
    """主窗口 - 现代优化版 v2.0"""
    
    def __init__(self):
        super().__init__()
        self.history_manager = HistoryManager()
        self.worker: Optional[WorkerThread] = None
        self.input_files: List[Path] = []
        self.init_ui()
        self.load_theme()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("🦎 PDF Converter Pro")
        self.setMinimumSize(1100, 750)
        
        # 创建中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # ===== 标题栏 =====
        title_layout = QHBoxLayout()
        title = QLabel("🦎 PDF Converter Pro")
        title.setObjectName("title_label")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 版本信息
        version_label = QLabel("v2.0")
        version_label.setStyleSheet("color: #636e72; font-size: 12px; padding: 5px;")
        title_layout.addWidget(version_label)
        
        main_layout.addLayout(title_layout)
        
        # ===== 创建分割器 =====
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # ----- 上部区域（拖拽 + 选项）-----
        upper_widget = QWidget()
        upper_layout = QVBoxLayout(upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        upper_layout.setSpacing(15)
        
        # 拖拽区域
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.on_files_dropped)
        upper_layout.addWidget(self.drop_area)
        
        # 输入输出选择
        io_group = QGroupBox("📁 文件选择")
        io_layout = QHBoxLayout()
        io_layout.setSpacing(15)
        
        self.input_label = QLabel("未选择文件")
        self.input_label.setStyleSheet("color: #636e72;")
        self.input_label.setWordWrap(True)
        
        self.output_label = QLabel("未选择输出目录")
        self.output_label.setStyleSheet("color: #636e72;")
        
        btn_input = QPushButton("📂 选择文件")
        btn_input.setObjectName("btn_select")
        btn_input.clicked.connect(self.select_input)
        
        btn_output = QPushButton("📤 选择输出")
        btn_output.setObjectName("btn_select")
        btn_output.clicked.connect(self.select_output)
        
        io_layout.addWidget(QLabel("输入:"))
        io_layout.addWidget(self.input_label, 1)
        io_layout.addWidget(btn_input)
        io_layout.addWidget(QLabel("输出:"))
        io_layout.addWidget(self.output_label, 1)
        io_layout.addWidget(btn_output)
        
        io_group.setLayout(io_layout)
        upper_layout.addWidget(io_group)
        
        # 处理选项
        self.options_widget = ProcessingOptionsWidget()
        self.options_widget.options_changed.connect(self.on_options_changed)
        upper_layout.addWidget(self.options_widget)
        
        splitter.addWidget(upper_widget)
        
        # ----- 下部区域（文件预览 + 日志）-----
        lower_widget = QWidget()
        lower_layout = QVBoxLayout(lower_widget)
        lower_layout.setContentsMargins(0, 0, 0, 0)
        lower_layout.setSpacing(15)
        
        # 文件预览
        self.file_preview = FilePreviewWidget("待处理文件")
        self.file_preview.file_selected.connect(self.on_file_selected)
        lower_layout.addWidget(self.file_preview, 1)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        
        self.btn_start = QPushButton("▶️ 开始处理")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.clicked.connect(self.start_processing)
        control_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹️ 停止")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.setEnabled(False)
        control_layout.addWidget(self.btn_stop)
        
        self.btn_history = QPushButton("🕐 历史记录")
        self.btn_history.clicked.connect(self.show_history)
        control_layout.addWidget(self.btn_history)
        
        self.btn_clear = QPushButton("🗑️ 清空列表")
        self.btn_clear.clicked.connect(self.clear_files)
        control_layout.addWidget(self.btn_clear)
        
        control_layout.addStretch()
        
        lower_layout.addLayout(control_layout)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p% - 就绪")
        lower_layout.addWidget(self.progress)
        
        # 当前文件进度
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet("color: #636e72; font-size: 13px;")
        lower_layout.addWidget(self.current_file_label)
        
        # 日志区域
        log_group = QGroupBox("📋 处理日志")
        log_layout = QVBoxLayout()
        
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(180)
        self.log.append("👋 欢迎使用 PDF Converter Pro v2.0！")
        self.log.append("💡 提示：拖拽文件到上方区域快速开始")
        self.log.append("💡 提示：可单独或组合使用去水印/OCR/WORD 转换功能")
        log_layout.addWidget(self.log)
        
        log_group.setLayout(log_layout)
        lower_layout.addWidget(log_group)
        
        splitter.addWidget(lower_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter, 1)
        
        # ===== 状态栏 =====
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("✅ 就绪")
        
        # 添加统计信息到状态栏
        self.stats_label = QLabel("文件：0 | 成功：0 | 失败：0")
        self.stats_label.setStyleSheet("color: #636e72;")
        self.statusBar.addPermanentWidget(self.stats_label)
        
        # 初始化路径
        self.input_dir: Optional[Path] = None
        self.output_dir: Optional[Path] = None
        self.success_count = 0
        self.fail_count = 0
    
    def load_theme(self):
        """加载主题样式"""
        theme_path = Path(__file__).parent.parent / "assets" / "theme.qss"
        if theme_path.exists():
            with open(theme_path, 'r', encoding='utf-8') as f:
                theme = f.read()
                # 添加额外样式
                extra_style = """
                QPushButton#btn_stop {
                    background-color: #d63031;
                }
                QPushButton#btn_stop:hover {
                    background-color: #c0392b;
                }
                QPushButton#btn_clear {
                    background-color: #636e72;
                }
                QPushButton#btn_clear:hover {
                    background-color: #2d3436;
                }
                """
                self.setStyleSheet(theme + extra_style)
    
    def select_input(self):
        """选择输入文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "PDF 文件 (*.pdf);;图片文件 (*.png *.jpg *.jpeg);;所有文件 (*.*)"
        )
        if files:
            self.input_files = [Path(f) for f in files]
            self.input_dir = self.input_files[0].parent if self.input_files else None
            self._update_input_display()
            self.file_preview.load_files_from_list(self.input_files)
            self.statusBar.showMessage(f"✅ 已加载 {len(self.input_files)} 个文件")
            self._update_stats()
    
    def select_output(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir = Path(dir_path)
            self.output_label.setText(str(self.output_dir))
            self.output_label.setStyleSheet("color: #2d3436; font-weight: bold;")
            self.statusBar.showMessage(f"✅ 输出目录：{self.output_dir}")
            self.log.append(f"📁 输出目录：{self.output_dir}")
    
    def on_files_dropped(self, file_paths: List[str]):
        """处理文件拖拽"""
        if file_paths:
            self.input_files = [Path(p) for p in file_paths]
            self.input_dir = self.input_files[0].parent if self.input_files else None
            self._update_input_display()
            self.file_preview.load_files_from_list(self.input_files)
            self.statusBar.showMessage(f"✅ 已加载 {len(self.input_files)} 个文件")
            self._update_stats()
            self.log.append(f"📥 拖拽加载 {len(file_paths)} 个文件")
    
    def _update_input_display(self):
        """更新输入显示"""
        if len(self.input_files) == 0:
            self.input_label.setText("未选择文件")
            self.input_label.setStyleSheet("color: #636e72;")
        elif len(self.input_files) == 1:
            self.input_label.setText(self.input_files[0].name)
            self.input_label.setStyleSheet("color: #2d3436; font-weight: bold;")
        else:
            self.input_label.setText(f"{len(self.input_files)} 个文件")
            self.input_label.setStyleSheet("color: #2d3436; font-weight: bold;")
    
    def on_file_selected(self, file_path: str):
        """处理文件选择"""
        self.log.append(f"📄 选中文件：{Path(file_path).name}")
    
    def on_options_changed(self):
        """选项变更"""
        options = self.options_widget.get_options()
        enabled_features = []
        if options["remove_watermark"]:
            enabled_features.append("去水印")
        if options["do_ocr"]:
            enabled_features.append("OCR")
        if options["convert_to_word"]:
            enabled_features.append("WORD")
        
        if enabled_features:
            self.statusBar.showMessage(f"⚙️ 已选择：{' + '.join(enabled_features)}")
        else:
            self.statusBar.showMessage("⚠️ 请至少选择一个处理功能")
    
    def start_processing(self):
        """开始处理"""
        # 验证输入
        if not self.input_files:
            QMessageBox.warning(self, "警告", "❌ 请先选择要处理的文件")
            self.log.append("❌ 错误：请先选择要处理的文件")
            return
        
        # 验证输出
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "❌ 请先选择输出目录")
            self.log.append("❌ 错误：请先选择输出目录")
            return
        
        # 验证选项
        options = self.options_widget.get_options()
        if not any([options["remove_watermark"], options["do_ocr"], options["convert_to_word"]]):
            QMessageBox.warning(self, "警告", "❌ 请至少选择一个处理功能")
            self.log.append("❌ 错误：请至少选择一个处理功能")
            return
        
        # 重置计数
        self.success_count = 0
        self.fail_count = 0
        self._update_stats()
        
        # 禁用按钮
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_clear.setEnabled(False)
        
        self.log.append("🚀 开始处理...")
        self.log.append(f"📊 文件数：{len(self.input_files)}")
        
        # 记录选项
        features = []
        if options["remove_watermark"]:
            features.append(f"去水印 ({options['watermark_method']})")
        if options["do_ocr"]:
            features.append(f"OCR ({options['ocr_engine']})")
        if options["convert_to_word"]:
            features.append(f"WORD ({options['convert_method']})")
        self.log.append(f"⚙️ 处理选项：{' + '.join(features)}")
        
        # 创建工作线程
        self.worker = WorkerThread(self.input_files, self.output_dir, options)
        self.worker.progress.connect(self.on_progress)
        self.worker.file_progress.connect(self.on_file_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def stop_processing(self):
        """停止处理"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log.append("⏹️ 用户停止处理")
            self.statusBar.showMessage("⏹️ 已停止")
    
    def on_progress(self, value: int, message: str):
        """进度更新"""
        self.progress.setValue(value)
        self.progress.setFormat(f"%p% - {message}")
        self.log.append(f"📊 {message}")
        self.statusBar.showMessage(message)
    
    def on_file_progress(self, filename: str, progress: int, status: str):
        """单文件进度更新"""
        self.current_file_label.setText(f"当前文件：{filename} - {status}")
        
        if "✅" in status:
            self.success_count += 1
        elif "❌" in status:
            self.fail_count += 1
        
        self._update_stats()
    
    def on_finished(self, success: bool, message: str, success_count: int, fail_count: int):
        """处理完成"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_clear.setEnabled(True)
        self.current_file_label.setText("")
        
        if success:
            self.log.append(f"✅ {message}")
            self.log.append(f"📊 总计：成功 {success_count} 个，失败 {fail_count} 个")
            self.statusBar.showMessage(f"✅ 处理完成！成功：{success_count}, 失败：{fail_count}")
            
            # 记录到历史
            options = self.options_widget.get_options()
            self.history_manager.add_record(
                self.input_dir or Path(self.input_files[0]).parent,
                self.output_dir,
                options,
                success,
                success_count + fail_count
            )
        else:
            self.log.append(f"❌ {message}")
            self.statusBar.showMessage(f"❌ 处理失败：{message}")
        
        self._update_stats()
    
    def show_history(self):
        """显示历史记录"""
        history = self.history_manager.get_recent(10)
        
        if not history:
            QMessageBox.information(self, "历史记录", "📭 暂无历史记录")
            return
        
        # 创建历史对话框
        history_dialog = QDialog(self)
        history_dialog.setWindowTitle("🕐 处理历史记录")
        history_dialog.setMinimumSize(650, 450)
        
        layout = QVBoxLayout(history_dialog)
        
        # 统计信息
        stats = self.history_manager.get_statistics()
        stats_label = QLabel(
            f"📊 总记录：{stats['total_records']} | "
            f"成功率：{stats['success_rate']:.1f}% | "
            f"总文件：{stats['total_files_processed']}"
        )
        stats_label.setStyleSheet("font-weight: bold; color: #6c5ce7; padding: 10px;")
        layout.addWidget(stats_label)
        
        history_list = QListWidget()
        for record in history:
            status_icon = "✅" if record["success"] else "❌"
            timestamp = record["timestamp"][:16].replace("T", " ")
            
            # 获取选项摘要
            opts = record.get("options", {})
            features = []
            if opts.get("remove_watermark"):
                features.append("🧹")
            if opts.get("do_ocr"):
                features.append("🔍")
            if opts.get("convert_to_word"):
                features.append("📝")
            feature_str = " ".join(features) if features else "❓"
            
            text = f"{status_icon} {timestamp} - {feature_str} 处理 {record.get('files_processed', 0)} 个文件"
            item = QListWidgetItem(text)
            item.setToolTip(
                f"输入：{record['input_dir']}\n"
                f"输出：{record['output_dir']}\n"
                f"选项：{opts}"
            )
            history_list.addItem(item)
        
        layout.addWidget(history_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        btn_clear = QPushButton("🗑️ 清空历史")
        btn_clear.clicked.connect(lambda: self._clear_history_confirm(history_dialog))
        btn_layout.addWidget(btn_clear)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(history_dialog.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        history_dialog.exec()
    
    def _clear_history_confirm(self, dialog: QDialog):
        """确认清空历史"""
        reply = QMessageBox.question(
            dialog, "确认", "确定要清空所有历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_history()
            dialog.accept()
            self.log.append("🗑️ 历史记录已清空")
    
    def clear_files(self):
        """清空文件列表"""
        self.input_files = []
        self._update_input_display()
        self.file_preview.clear_files()
        self.progress.setValue(0)
        self.progress.setFormat("%p% - 就绪")
        self.current_file_label.setText("")
        self.statusBar.showMessage("✅ 已清空")
        self.log.append("🗑️ 已清空文件列表")
        self._update_stats()
    
    def _update_stats(self):
        """更新统计显示"""
        total = len(self.input_files)
        self.stats_label.setText(f"文件：{total} | 成功：{self.success_count} | 失败：{self.fail_count}")
