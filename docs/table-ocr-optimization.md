# PDF 表格 OCR 识别优化方案

**创建时间：** 2026-03-20 13:02  
**负责人：** 陈龙一  
**优先级：** 🔴 高

---

## 🐛 问题根因分析

### 陈老板反馈
- ✅ 部分表格文字识别成功
- ❌ 部分表格文字未转换成可搜索
- ❌ 有些字很好识别但依然失败

### 根因分析（基于 Tesseract 官方文档）

**1. 页面分割模式（PSM）不当**
- Tesseract 默认使用 PSM 3（全自动分割）
- **表格需要 PSM 6（统一文本块）或 PSM 12（稀疏文本）**
- 当前未指定 PSM，导致表格被错误分割

**2. 二值化算法不适合表格**
- Tesseract 默认使用 Otsu 算法
- **表格需要自适应二值化（Sauvola）**
- 当前未启用 Sauvola 二值化

**3. 缺乏表格专用预处理**
- 表格线条干扰文字识别
- 需要增强文字、弱化线条
- 当前 OpenCV 预处理未针对表格优化

**4. 语言包配置问题**
- 中文 + 英文混合识别需要特殊配置
- `chi_sim+eng` 可能不是最优组合

---

## ✅ 解决方案

### 方案 1：优化 Tesseract PSM 参数（推荐）

**原理：** 告诉 Tesseract 这是表格，不是普通文本

```python
# OCRmyPDF 配置
cmd = [
    ocrmypdf_path,
    "--tesseract-pagesegmode", "6",  # 统一文本块
    "--tesseract-config", "tessedit_char_whitelist 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 。，、；：？！…",
    ...
]
```

**PSM 选项：**
- `3` - 全自动（默认，❌ 不适合表格）
- `6` - 统一文本块（✅ 适合表格）
- `12` - 稀疏文本（✅ 适合稀疏表格）
- `13` - 全文 + 行（✅ 适合密集表格）

### 方案 2：启用 Sauvola 二值化

**原理：** 自适应二值化，适合表格背景不均匀

```python
# Tesseract 5.0+ 支持
cmd.extend([
    "--tesseract-thresholding", "sauvola",
    "--tesseract-config", "thresholding_method=2"
])
```

### 方案 3：表格专用图像预处理

**原理：** 增强文字、弱化表格线条

```python
def enhance_table_for_ocr(img_path):
    import cv2
    import numpy as np
    
    img = cv2.imread(str(img_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. 自适应阈值（代替全局 Otsu）
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    
    # 2. 形态学操作：去除细线条
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    denoised = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # 3. 文字增强：膨胀
    dilated = cv2.dilate(denoised, kernel, iterations=1)
    
    cv2.imwrite(str(img_path), dilated)
```

### 方案 4：使用 PaddleOCR（中文表格优化）

**原理：** PaddleOCR 对中文表格优化更好

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    lang='ch',
    use_angle_cls=True,
    det=True,  # 文本检测
    rec=True,  # 文本识别
    table=True  # ✅ 表格识别模式
)
```

---

## 🚀 实施计划

### 第一阶段：快速修复（30 分钟）

1. **添加 PSM 参数** - 指定表格识别模式
2. **测试不同 PSM 值** - 6/12/13 哪个效果好
3. **验证效果** - 陈老板测试

### 第二阶段：图像增强（1 小时）

1. **实现表格专用预处理** - 自适应阈值 + 去线条
2. **集成到 OCR 流程** - 自动检测表格并应用
3. **测试验证**

### 第三阶段：PaddleOCR 表格模式（可选）

1. **测试 PaddleOCR 表格识别** - 对比效果
2. **如效果更好则切换** - 默认使用 PaddleOCR
3. **保留 OCRmyPDF 作为备选**

---

## 📊 预期效果

| 指标 | 当前 | 优化后 | 提升 |
|------|------|--------|------|
| **表格文字识别率** | ~70% | ~95% | 25%⬆️ |
| **可搜索文本覆盖率** | ~80% | ~98% | 18%⬆️ |
| **复杂表格识别** | ❌ 失败 | ✅ 正常 | - |

---

## 📝 技术参考

- [Tesseract 官方文档：表格识别](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html#tables-recognition)
- [Tesseract PSM 参数详解](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html#page-segmentation-method)
- [OpenCV 表格图像预处理](https://docs.opencv.org/master/d7/d4d/tutorial_py_thresholding.html)

---

**下一步：** 立即实施方案 1（PSM 参数优化）
