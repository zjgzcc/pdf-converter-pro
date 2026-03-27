# PDF Converter Pro 🦎

扫描版 PDF 转可搜索 PDF + WORD 批量处理工具

## 功能特性

- ✅ OCR 识别（OCRmyPDF + Tesseract）
- ✅ 智能去水印（IOPaint AI / OpenCV）
- ✅ PDF 转 WORD（PaddleOCR 版面恢复）
- ✅ 批量处理
- ✅ Windows GUI 界面

## 技术架构（方案 B - 混合引擎）

```
扫描 PDF → 去水印模块 → OCR 模块 → WORD 转换模块 → 输出
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 GUI
python main.py
```

## 团队协作

| 成员 | 职责 | 状态 |
|------|------|------|
| 🦎 龙一【主理】 | 总协调 | ✅ |
| 🔍 龙二【技术】 | 技术调研 | 🔄 |
| 📊 赤影【市场】 | 竞品分析 | 🔄 |
| 🧪 青影【测试】 | 测试验证 | 🔄 |
| ⚙️ 紫影【研发】 | 技术评审 | 🔄 |
| 🎨 橙影【设计】 | UI/UX 设计 | 🔄 |
| 🌙 月影【情报】 | 信息搜集 | 🔄 |
| 🔥 炎影【运营】 | 运营策略 | 🔄 |
| 💎 金影【商业】 | 商业分析 | 🔄 |
| 🌿 绿影【增长】 | 增长玩法 | 🔄 |
| ⚡ 雷影【执行】 | MVP 验证 | 🔄 |

## 项目结构

```
pdf-converter-pro/
├── main.py              # GUI 入口
├── core/
│   ├── watermark.py     # 去水印模块
│   ├── ocr.py           # OCR 模块
│   └── converter.py     # WORD 转换模块
├── ui/
│   └── main_window.py   # 主界面
├── tests/               # 测试用例
├── requirements.txt     # 依赖
└── README.md
```

## License

MIT
