# 水印去除模块文档

🔍 **龙二【技术】** 负责实现  
🧪 **青影【测试】** 负责验证

## 概述

水印去除模块提供完整的图片去水印功能，支持两种处理模式：

1. **OpenCV 传统方法** - 适合颜色单一的浅色水印
2. **IOPaint AI 方法** - 适合复杂背景、半透明水印（使用 LaMa 模型）

## 安装

### 基础安装（OpenCV 模式）

```bash
pip install opencv-python numpy Pillow PyMuPDF
```

### 完整安装（包含 IOPaint AI 模式）

```bash
pip install opencv-python numpy Pillow PyMuPDF iopaint
```

> **注意**: IOPaint 是可选依赖。如果未安装，系统会自动回退到 OpenCV 模式。

## 核心功能

### 1. 单张图片去水印

```python
from pathlib import Path
from core.watermark import WatermarkRemover

# 创建去水印器
remover = WatermarkRemover(method="auto")  # auto | opencv | iopaint

# 去除水印
input_path = Path("input.png")
output_path = Path("output.png")
success = remover.remove(input_path, output_path)
```

### 2. 批量去水印

```python
from core.watermark import batch_remove_watermarks

# 批量处理目录中的所有图片
success, fail, results = batch_remove_watermarks(
    input_dir=Path("input_images"),
    output_dir=Path("output_images"),
    method="auto",
    recursive=True  # 是否递归处理子目录
)

print(f"成功：{success}, 失败：{fail}")
for result in results:
    print(f"  {result['input']} -> {'OK' if result['success'] else 'FAIL'}")
```

### 3. 水印自动检测

```python
from core.watermark import WatermarkDetector
import cv2

# 创建检测器
detector = WatermarkDetector()

# 读取图像
img = cv2.imread("input.png")

# 检测水印区域（返回二值掩码）
mask = detector.detect(img)

# 保存掩码查看检测结果
cv2.imwrite("mask.png", mask)
```

### 4. PDF 转图片 + 去水印

```python
from core.watermark import process_pdf_images

# 将 PDF 每页转为图片并去水印
success, fail = process_pdf_images(
    pdf_path=Path("document.pdf"),
    output_dir=Path("output_pages"),
    method="auto",
    dpi=300  # 转换 DPI
)
```

### 5. 图片合并为 PDF

```python
from core.watermark import images_to_pdf

# 将目录中的图片合并为 PDF
success = images_to_pdf(
    image_dir=Path("images"),
    output_pdf=Path("output.pdf"),
    page_size="A4"  # A4 | Letter | A3 | (width, height)
)
```

### 6. PDF 去水印完整流程

```python
from core.watermark import process_pdf_with_watermark_removal

# PDF -> 图片 -> 去水印 -> PDF
success = process_pdf_with_watermark_removal(
    input_pdf=Path("watermarked.pdf"),
    output_pdf=Path("clean.pdf"),
    method="auto",
    dpi=300
)
```

## PDF 提取模块

### 1. PDF 转图片

```python
from core.pdf_extractor import PDFExtractor

# 创建提取器
extractor = PDFExtractor(dpi=300)

# 转换 PDF
success, fail, results = extractor.pdf_to_images(
    pdf_path=Path("document.pdf"),
    output_dir=Path("output"),
    pages=[1, 2, 3],  # None=全部
    image_format="png"
)
```

### 2. 提取嵌入图片

```python
from core.pdf_extractor import PDFExtractor

extractor = PDFExtractor()

# 提取 PDF 中的所有嵌入图片
success, fail, results = extractor.extract_embedded_images(
    pdf_path=Path("document.pdf"),
    output_dir=Path("extracted_images")
)
```

### 3. 图片合并为 PDF

```python
from core.pdf_extractor import PDFMerger

# 创建合并器
merger = PDFMerger(page_size="A4")

# 合并目录中的图片
success = merger.images_to_pdf(
    image_dir=Path("images"),
    output_pdf=Path("output.pdf"),
    pattern="*.png",
    fit_page=True
)

# 或合并图片列表
success = merger.images_list_to_pdf(
    image_paths=[Path("img1.png"), Path("img2.png")],
    output_pdf=Path("output.pdf")
)
```

### 4. 完整处理流程（带回调）

```python
from core.pdf_extractor import PDFProcessor
from core.watermark import WatermarkRemover

# 创建处理器
processor = PDFProcessor(dpi=300, page_size="A4")

# 定义处理回调
def remove_watermark_callback(image_path):
    remover = WatermarkRemover(method="auto")
    output_path = image_path.parent / f"clean_{image_path.name}"
    remover.remove(image_path, output_path)
    return output_path

# 处理 PDF
success = processor.process_with_callback(
    input_pdf=Path("input.pdf"),
    output_pdf=Path("output.pdf"),
    process_callback=remove_watermark_callback
)
```

## 方法选择指南

| 场景 | 推荐方法 | 说明 |
|------|----------|------|
| 浅色文字水印 | `opencv` | 速度快，效果好 |
| 半透明水印 | `iopaint` | AI 修复更自然 |
| 复杂背景水印 | `iopaint` | LaMa 模型智能填充 |
| 大面积水印 | `iopaint` | 传统方法会有痕迹 |
| 批量处理 | `opencv` | 速度优先 |
| 高质量单张 | `iopaint` | 质量优先 |
| 不确定 | `auto` | 自动分析选择 |

## 参数说明

### WatermarkRemover

```python
WatermarkRemover(
    method="auto",              # "auto" | "opencv" | "iopaint"
    confidence_threshold=0.5    # 自动检测阈值
)
```

### batch_remove_watermarks

```python
batch_remove_watermarks(
    input_dir,                  # 输入目录
    output_dir,                 # 输出目录
    method="auto",              # 去水印方法
    recursive=False             # 是否递归子目录
)
```

### PDFExtractor

```python
PDFExtractor(
    dpi=300                     # 转换 DPI（72-600）
)
```

### PDFMerger

```python
PDFMerger(
    page_size="A4"              # "A4" | "Letter" | "A3" | (width, height)
)
```

## 性能优化

### 1. 批量处理优化

```python
# 使用 OpenCV 模式进行批量处理（速度更快）
success, fail, results = batch_remove_watermarks(
    input_dir, output_dir,
    method="opencv"  # 比 iopaint 快 10-100 倍
)
```

### 2. DPI 调整

```python
# 降低 DPI 提高速度（适合预览）
extractor = PDFExtractor(dpi=150)

# 提高 DPI 保证质量（适合最终输出）
extractor = PDFExtractor(dpi=300)
```

### 3. 页面选择

```python
# 只处理特定页面
success, fail, results = extractor.pdf_to_images(
    pdf_path, output_dir,
    pages=[1, 3, 5]  # 只转换第 1、3、5 页
)
```

## 常见问题

### Q: IOPaint 安装失败怎么办？

A: IOPaint 是可选依赖。如果安装失败，系统会自动使用 OpenCV 模式。也可以手动指定：

```python
remover = WatermarkRemover(method="opencv")
```

### Q: 去水印效果不好？

A: 尝试以下方法：
1. 切换到 IOPaint 模式：`method="iopaint"`
2. 调整检测阈值
3. 检查水印颜色是否适合 OpenCV 检测

### Q: 处理速度慢？

A: 
1. 使用 OpenCV 模式（比 IOPaint 快 10-100 倍）
2. 降低 DPI（300 -> 150）
3. 只处理需要的页面

### Q: PDF 合并后图片变形？

A: 确保 `fit_page=True`，这会自动保持宽高比：

```python
merger.images_to_pdf(input_dir, output_pdf, fit_page=True)
```

## 测试

### 运行测试

```bash
# 运行单元测试
pytest tests/test_watermark.py
pytest tests/test_pdf_extractor.py

# 运行功能演示
python tests/test_watermark_demo.py

# 运行使用示例
python examples/watermark_usage.py
```

### 测试覆盖

- ✅ 水印检测器
- ✅ OpenCV 去水印
- ✅ 批量处理
- ✅ PDF 转图片
- ✅ 图片合并 PDF
- ✅ 嵌入图片提取
- ⚠️ IOPaint 集成（需要安装 iopaint）

## 更新日志

### v1.0.0 (2026-03-19)

- ✅ 实现 IOPaint 完整集成（LaMa 模型）
- ✅ 添加水印自动检测（颜色分析 + 边缘检测）
- ✅ 支持批量图片去水印
- ✅ 创建 PDF 图片提取功能
- ✅ PDF 每页转图片（PyMuPDF）
- ✅ 处理后的图片合并回 PDF
- ✅ 完整的测试覆盖

## 技术架构

```
core/
├── watermark.py          # 水印去除核心
│   ├── WatermarkDetector  # 水印检测器
│   ├── WatermarkRemover   # 水印去除器
│   └── batch_remove_*     # 批量处理函数
│
└── pdf_extractor.py      # PDF 提取核心
    ├── PDFExtractor      # PDF 转图片
    ├── PDFMerger         # 图片合并 PDF
    └── PDFProcessor      # 完整处理器
```

## 依赖关系

```
opencv-python  → 图像处理和修复
numpy          → 数值计算
Pillow         → 图像格式转换
PyMuPDF        → PDF 处理
iopaint (可选) → AI 去水印
```

---

**最后更新**: 2026-03-19  
**维护者**: 🔍 龙二【技术】
