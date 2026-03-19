#!/usr/bin/env python3
"""
PDF Converter Pro - 主入口
🦎 影诺办龙一【主理】

性能优化：启动时预加载 PaddleOCR 模型，避免首次使用延迟
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def preload_models():
    """预加载 AI 模型（后台线程）"""
    try:
        from core.ocr import OCREngine, OCREngineType
        import threading
        
        def _load():
            logger.info("🔍 后台预加载 PaddleOCR 模型...")
            engine = OCREngine(
                engine_type=OCREngineType.PADDLEOCR,
                preload_models=True
            )
        
        # 在后台线程中加载，避免阻塞 UI 启动
        thread = threading.Thread(target=_load, daemon=True)
        thread.start()
        logger.info("✅ PaddleOCR 预加载任务已启动（后台运行）")
        
    except Exception as e:
        logger.warning(f"预加载失败：{e}，将在首次使用时延迟加载")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Converter Pro")
    app.setOrganizationName("影诺办")
    
    # 启动后预加载模型（不阻塞 UI）
    preload_models()
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
