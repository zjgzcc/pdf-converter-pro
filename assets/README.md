# 🎨 Assets - PDF Converter Pro

本目录包含应用的所有视觉资源和配置文件。

## 目录结构

```
assets/
├── theme.qss              # QSS 样式表文件（现代 UI 主题）
├── icons.json            # 图标和颜色配置
├── app_icon_placeholder.svg  # 应用图标占位符
└── README.md             # 本文件
```

## 📋 文件说明

### theme.qss
现代 UI 样式表，包含：
- **配色方案**：紫色主题 (#6c5ce7)
- **组件样式**：按钮、输入框、进度条、列表等
- **交互效果**：悬停、按下、禁用状态
- **滚动条美化**：现代化滚动条样式
- **工具提示**：深色主题提示框

### icons.json
配置文件的图标和颜色：
- **Emoji 图标**：应用内使用的表情符号
- **颜色变量**：主题色、成功色、错误色等
- **间距配置**：统一的间距和圆角值

### app_icon_placeholder.svg
应用图标占位符（SVG 格式）：
- 尺寸：256x256
- 可替换为实际的 PNG/SVG 图标
- 建议尺寸：256x256, 512x512

## 🎨 颜色主题

| 颜色 | 色值 | 用途 |
|------|------|------|
| 主色 | #6c5ce7 | 按钮、强调元素 |
| 主色深 | #5b4cdb | 悬停状态 |
| 主色浅 | #a29bfe | 渐变、高亮 |
| 成功 | #00b894 | 完成状态、成功提示 |
| 错误 | #d63031 | 错误状态、删除按钮 |
| 警告 | #fdcb6e | 警告提示 |
| 信息 | #0984e3 | 信息提示、链接 |
| 背景 | #f5f6fa | 主背景色 |
| 表面 | #ffffff | 卡片、组框背景 |
| 文字主 | #2d3436 | 主要文字 |
| 文字次 | #636e72 | 次要文字、提示 |
| 边框 | #dfe6e9 | 边框、分割线 |

## 🛠️ 使用方法

### 在代码中加载主题

```python
from pathlib import Path

def load_theme(self):
    theme_path = Path(__file__).parent.parent / "assets" / "theme.qss"
    if theme_path.exists():
        with open(theme_path, 'r', encoding='utf-8') as f:
            self.setStyleSheet(f.read())
```

### 自定义颜色

编辑 `icons.json` 中的颜色配置，然后在 QSS 中使用对应的色值。

### 替换应用图标

1. 准备 256x256 或 512x512 的 PNG/SVG 图标
2. 替换 `app_icon_placeholder.svg`
3. 在 `main_window.py` 中启用图标加载：
   ```python
   self.setWindowIcon(QIcon(":/icons/app_icon.png"))
   ```

## 📝 设计原则

1. **现代简洁**：圆角、阴影、渐变
2. **一致性**：统一的间距、颜色、字体
3. **可用性**：清晰的视觉层次、明确的交互反馈
4. **无障碍**：足够的对比度、清晰的文字

## 🔄 更新日志

- **v1.0** (2026-03-19)
  - 初始版本
  - 现代紫色主题
  - 拖拽支持
  - 文件预览组件
  - 历史记录功能

---

🎨 设计：橙影【设计】
