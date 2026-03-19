"""
主窗口 UI
🎨 橙影【设计】负责优化

PyQt6 界面
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QGroupBox, QComboBox, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path


class WorkerThread(QThread):
    """后台工作线程"""
    progress = pyqtSignal(int, str)  # 进度百分比，状态信息
    finished = pyqtSignal(bool, str)  # 是否成功，结果信息
    
    def __init__(self, input_dir, output_dir, options):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.options = options
    
    def run(self):
        """执行处理任务"""
        try:
            from core.watermark import batch_remove_watermarks
            from core.ocr import batch_ocr
            from core.converter import batch_convert
            
            # 步骤 1: 去水印
            self.progress.emit(10, "正在去除水印...")
            if self.options.get("remove_watermark", False):
                temp_dir = self.output_dir / "temp_images"
                success, fail = batch_remove_watermarks(
                    self.input_dir, temp_dir,
                    method=self.options.get("watermark_method", "auto")
                )
                self.progress.emit(30, f"去水印完成：成功{success}，失败{fail}")
            
            # 步骤 2: OCR
            self.progress.emit(40, "正在 OCR 识别...")
            if self.options.get("do_ocr", True):
                ocr_dir = self.output_dir / "temp_ocr"
                success, fail = batch_ocr(
                    self.input_dir, ocr_dir,
                    language=self.options.get("ocr_lang", "chi_sim+eng")
                )
                self.progress.emit(60, f"OCR 完成：成功{success}，失败{fail}")
            
            # 步骤 3: 转 WORD
            self.progress.emit(70, "正在转换为 WORD...")
            if self.options.get("convert_to_word", True):
                word_dir = self.output_dir / "word"
                success, fail = batch_convert(
                    self.input_dir, word_dir,
                    method=self.options.get("convert_method", "paddleocr")
                )
                self.progress.emit(90, f"WORD 转换完成：成功{success}，失败{fail}")
            
            self.progress.emit(100, "全部完成！")
            self.finished.emit(True, "处理完成")
            
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("PDF Converter Pro 🦎")
        self.setMinimumSize(800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 标题
        title = QLabel("🦎 PDF Converter Pro")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # 输入输出选择
        io_group = QGroupBox("文件选择")
        io_layout = QHBoxLayout()
        
        self.input_label = QLabel("未选择输入目录")
        self.output_label = QLabel("未选择输出目录")
        
        btn_input = QPushButton("选择输入目录")
        btn_input.clicked.connect(self.select_input)
        
        btn_output = QPushButton("选择输出目录")
        btn_output.clicked.connect(self.select_output)
        
        io_layout.addWidget(QLabel("输入:"))
        io_layout.addWidget(self.input_label)
        io_layout.addWidget(btn_input)
        io_layout.addWidget(QLabel("输出:"))
        io_layout.addWidget(self.output_label)
        io_layout.addWidget(btn_output)
        
        io_group.setLayout(io_layout)
        layout.addWidget(io_group)
        
        # 选项
        options_group = QGroupBox("处理选项")
        options_layout = QVBoxLayout()
        
        # 去水印
        self.chk_watermark = QCheckBox("去除水印")
        self.chk_watermark.setChecked(True)
        options_layout.addWidget(self.chk_watermark)
        
        self.combo_watermark = QComboBox()
        self.combo_watermark.addItems(["auto", "opencv", "iopaint"])
        options_layout.addWidget(self.combo_watermark)
        
        # OCR
        self.chk_ocr = QCheckBox("OCR 识别（转可搜索 PDF）")
        self.chk_ocr.setChecked(True)
        options_layout.addWidget(self.chk_ocr)
        
        # 转 WORD
        self.chk_word = QCheckBox("转换为 WORD")
        self.chk_word.setChecked(True)
        options_layout.addWidget(self.chk_word)
        
        self.combo_convert = QComboBox()
        self.combo_convert.addItems(["paddleocr", "freep2w"])
        options_layout.addWidget(self.combo_convert)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 开始按钮
        self.btn_start = QPushButton("开始处理")
        self.btn_start.clicked.connect(self.start_processing)
        self.btn_start.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 10px; font-size: 16px; }"
        )
        layout.addWidget(self.btn_start)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        
        # 日志
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        layout.addWidget(self.log)
        
        self.input_dir = None
        self.output_dir = None
    
    def select_input(self):
        """选择输入目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if dir_path:
            self.input_dir = Path(dir_path)
            self.input_label.setText(str(self.input_dir))
    
    def select_output(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir = Path(dir_path)
            self.output_label.setText(str(self.output_dir))
    
    def start_processing(self):
        """开始处理"""
        if not self.input_dir or not self.output_dir:
            self.log.append("❌ 请先选择输入和输出目录")
            return
        
        self.btn_start.setEnabled(False)
        self.log.append("✅ 开始处理...")
        
        options = {
            "remove_watermark": self.chk_watermark.isChecked(),
            "watermark_method": self.combo_watermark.currentText(),
            "do_ocr": self.chk_ocr.isChecked(),
            "convert_to_word": self.chk_word.isChecked(),
            "convert_method": self.combo_convert.currentText(),
            "ocr_lang": "chi_sim+eng"
        }
        
        self.worker = WorkerThread(self.input_dir, self.output_dir, options)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def on_progress(self, value, message):
        """进度更新"""
        self.progress.setValue(value)
        self.log.append(f"📊 {message}")
    
    def on_finished(self, success, message):
        """处理完成"""
        self.btn_start.setEnabled(True)
        if success:
            self.log.append(f"✅ {message}")
        else:
            self.log.append(f"❌ {message}")
