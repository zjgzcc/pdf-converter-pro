"""
处理历史记录管理
🎨 橙影【设计】
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, history_file: Optional[Path] = None):
        if history_file is None:
            history_file = Path(__file__).parent.parent / "data" / "history.json"
        self.history_file = history_file
        self.history: List[Dict] = []
        self.load_history()
    
    def load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []
        else:
            # 创建数据目录
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history = []
    
    def save_history(self):
        """保存历史记录"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存历史记录失败：{e}")
    
    def add_record(self, input_dir: Path, output_dir: Path, options: Dict, 
                   success: bool, files_processed: int = 0):
        """添加处理记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "options": options,
            "success": success,
            "files_processed": files_processed,
            "duration_seconds": 0  # 由调用方更新
        }
        self.history.insert(0, record)  # 新记录在前
        
        # 保留最近 50 条记录
        if len(self.history) > 50:
            self.history = self.history[:50]
        
        self.save_history()
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """获取最近的记录"""
        return self.history[:limit]
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self.save_history()
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = len(self.history)
        success_count = sum(1 for r in self.history if r["success"])
        total_files = sum(r.get("files_processed", 0) for r in self.history)
        
        return {
            "total_records": total,
            "success_rate": (success_count / total * 100) if total > 0 else 0,
            "total_files_processed": total_files,
            "last_used": self.history[0]["timestamp"] if self.history else None
        }
