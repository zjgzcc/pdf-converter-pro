#!/usr/bin/env python3
"""
PDF Converter Pro - 主入口
🦎 影诺办龙一【主理】
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Converter Pro")
    app.setOrganizationName("影诺办")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
