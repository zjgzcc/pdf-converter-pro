"""
文件列表预览组件
🎨 橙影【设计】
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from pathlib import Path


class FilePreviewWidget(QWidget):
    """文件预览组件"""
    
    file_selected = pyqtSignal(str)  # 文件路径
    files_loaded = pyqtSignal(int)   # 文件数量
    
    def __init__(self, title: str = "文件预览", parent=None):
        super().__init__(parent)
        self.title = title
        self.current_files = []
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题栏
        title_layout = QHBoxLayout()
        self.title_label = QLabel(f"📄 {self.title}")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #6c5ce7;")
        title_layout.addWidget(self.title_label)
        
        self.count_label = QLabel("0 个文件")
        self.count_label.setStyleSheet("color: #636e72; font-size: 12px;")
        title_layout.addWidget(self.count_label)
        
        title_layout.addStretch()
        
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.setObjectName("btn_small")
        btn_refresh.setStyleSheet(
            "QPushButton { padding: 5px 10px; min-width: 60px; font-size: 12px; }"
        )
        btn_refresh.clicked.connect(self.refresh_files)
        title_layout.addWidget(btn_refresh)
        
        layout.addLayout(title_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #dfe6e9;
                border-radius: 8px;
                padding: 10px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 5px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: #6c5ce7;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #dfe6e9;
            }
        """)
        self.file_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.file_list)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        
        btn_clear = QPushButton("🗑️ 清空")
        btn_clear.setObjectName("btn_small")
        btn_clear.setStyleSheet(
            "QPushButton { padding: 5px 10px; min-width: 60px; font-size: 12px; "
            "background-color: #d63031; }"
        )
        btn_clear.clicked.connect(self.clear_files)
        btn_layout.addWidget(btn_clear)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def load_files(self, directory: Path, extensions: list = None):
        """加载目录中的文件"""
        if not directory.exists():
            return
        
        self.file_list.clear()
        self.current_files = []
        
        if extensions is None:
            extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        
        # 获取所有匹配的文件
        files = []
        for ext in extensions:
            files.extend(directory.glob(f"*{ext}"))
            files.extend(directory.glob(f"*{ext.upper()}"))
        
        # 排序并添加到列表
        files = sorted(set(files), key=lambda x: x.name.lower())
        
        for file_path in files:
            self.current_files.append(str(file_path))
            item = QListWidgetItem(f"📄 {file_path.name}")
            item.setToolTip(str(file_path))
            item.setData(Qt.ItemDataRole.UserRole, str(file_path))
            self.file_list.addItem(item)
        
        self.count_label.setText(f"{len(self.current_files)} 个文件")
        self.files_loaded.emit(len(self.current_files))
    
    def refresh_files(self):
        """刷新文件列表"""
        if self.current_files:
            # 从第一个文件获取目录
            first_file = Path(self.current_files[0])
            self.load_files(first_file.parent)
    
    def clear_files(self):
        """清空文件列表"""
        self.file_list.clear()
        self.current_files = []
        self.count_label.setText("0 个文件")
    
    def on_item_double_clicked(self, item: QListWidgetItem):
        """双击文件项"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_selected.emit(file_path)
    
    def get_selected_files(self) -> list:
        """获取选中的文件"""
        selected = self.file_list.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected if item.data(Qt.ItemDataRole.UserRole)]
    
    def get_all_files(self) -> list:
        """获取所有文件"""
        return self.current_files.copy()
    
    def load_files_from_list(self, file_paths: list):
        """从文件路径列表加载"""
        self.file_list.clear()
        self.current_files = []
        
        for file_path in file_paths:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            self.current_files.append(str(file_path))
            icon = "📄"
            if file_path.suffix.lower() == ".pdf":
                icon = "📕"
            elif file_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                icon = "🖼️"
            
            item = QListWidgetItem(f"{icon} {file_path.name}")
            item.setToolTip(str(file_path))
            item.setData(Qt.ItemDataRole.UserRole, str(file_path))
            self.file_list.addItem(item)
        
        self.count_label.setText(f"{len(self.current_files)} 个文件")
        self.files_loaded.emit(len(self.current_files))
