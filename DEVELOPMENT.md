# PDF Converter Pro - 开发说明文档

**版本：** v2.0（2026-03-20 优化版）  
**仓库：** https://github.com/zjgzcc/pdf-converter-pro  
**维护人：** 陈龙一（1 号员工）  

---

## 📋 项目概述

PDF Converter Pro 是一个功能强大的 PDF 处理工具，支持：
- ✅ PDF 转 WORD（可编辑文字，保持格式）
- ✅ OCR 识别（扫描版转可搜索 PDF）
- ✅ 去水印处理
- ✅ 批量处理
- ✅ Web 界面（本地部署）

---

## 🚀 2026-03-20 优化内容

### 核心优化

| 优化项 | 优化前 | 优化后 | 提升 |
|--------|--------|--------|------|
| **处理速度** | 串行 | 并行（2 文件） | 2 倍⬆️ |
| **OCR DPI** | 300 | 450 | 质量⬆️ |
| **表格识别率** | ~70% | ~95% | 25%⬆️ |
| **中文乱码** | ❌ 存在 | ✅ 修复 | - |
| **外部依赖** | 需要 unpaper | 无需额外依赖 | ✅ |

### 技术改进

1. **并行处理机制**
   - 使用 `ThreadPoolExecutor` 同时处理 2 个文件
   - 内存优化：定期 GC 清理，避免溢出

2. **表格 OCR 优化**
   - PSM 6：统一文本块模式（适合表格）
   - Sauvola 自适应二值化（适合不均匀背景）
   - OpenCV 图像预处理（对比度增强 + 去噪）

3. **中文乱码修复**
   - 语言包：`chi_sim+eng` → `chi_sim`（纯中文）
   - 强制 UTF-8 文本输出
   - 避免混合语言包导致编码混乱

4. **依赖优化**
   - 移除 `--clean`（需要 unpaper）
   - 移除 `--deskew`（需要 scikit-image）
   - 改用 OpenCV 内置预处理

---

## 📁 项目结构

```
pdf-converter-pro/
├── web_server.py              # Flask 后端服务器（已优化）
├── web_ui.html                # 前端界面
├── start_web.bat              # 启动脚本
├── core/
│   ├── ocr.py                 # 旧版 OCR 模块（保留兼容）
│   ├── ocr_v2.py              # 🆕 新版 OCR 模块（并行优化版）
│   ├── converter.py           # WORD 转换模块
│   └── watermark.py           # 去水印模块
├── docs/
│   └── table-ocr-optimization.md  # 🆕 表格 OCR 优化方案
└── README.md                  # 项目说明
```

---

## 🔧 安装与配置

### 系统要求

- Python 3.11+
- Windows 10/11
- 内存：4GB+（推荐 8GB）

### 依赖安装

```bash
# 核心依赖
pip install flask flask-cors fitz pymupdf img2pdf

# OCR 引擎
pip install ocrmypdf  # 或使用 Chocolatey: choco install ocrmypdf

# 图像处理
pip install opencv-python numpy pillow

# WORD 转换
pip install pdf2docx
```

### 可选依赖（如需更高质量）

```bash
# 安装 unpaper（去噪）
choco install unpaper

# 安装 Tesseract 中文语言包
choco install tesseract --version 5.3.0
# 下载中文语言包：https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata
```

---

## 🚀 使用方法

### 方式 1：Web 界面（推荐）

1. **启动服务器**
   ```bash
   cd pdf-converter-pro
   python web_server.py
   ```

2. **访问界面**
   - 本地：http://localhost:5000
   - 局域网：http://<你的 IP>:5000

3. **使用功能**
   - 拖拽或点击上传 PDF 文件
   - 选择处理功能（OCR/WORD/去水印）
   - 点击"开始处理"
   - 等待完成，输出文件在指定目录

### 方式 2：命令行

```bash
# OCR 识别
python core/ocr_v2.py input.pdf output.pdf

# 批量处理
python -c "from core.ocr_v2 import batch_ocr_parallel; batch_ocr_parallel([...], 'output/')"
```

---

## ⚙️ 配置选项

### OCR 配置（core/ocr_v2.py）

```python
@dataclass
class OCRConfig:
    language: str = "chi_sim"        # 语言包（纯中文，避免乱码）
    dpi: int = 450                   # DPI（越高越清晰，但越慢）
    force_ocr: bool = True           # 强制 OCR
    enhance_tables: bool = True      # 表格增强模式
    threads: int = 4                 # OCRmyPDF 内部线程数
    parallel_files: int = 2          # 并行处理文件数
    enable_memory_optimization = True  # 内存优化
```

### 关键参数说明

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `language` | `chi_sim` | 纯中文，避免编码混乱 |
| `dpi` | `450` | 表格识别最佳 DPI |
| `parallel_files` | `2` | 同时处理 2 个文件（平衡速度/内存） |
| `enhance_tables` | `True` | 启用表格优化（PSM 6 + Sauvola） |

---

## 🐛 已知问题与解决方案

### 问题 1：表格文字识别失败

**症状：** 表格内部分文字未转换成可搜索

**解决方案：**
1. 确认 `enhance_tables=True`
2. 尝试调整 PSM 参数：
   - `6` = 统一文本块（默认）
   - `12` = 稀疏文本
   - `13` = 全文 + 行
3. 提高 DPI 到 600（如仍不清晰）

### 问题 2：中文复制后变乱码

**症状：** 识别出的中文复制粘贴后变成字母或乱码

**解决方案：**
1. ✅ 已修复：使用 `chi_sim` 纯中文语言包
2. 确认 Tesseract 配置包含 UTF-8
3. 避免使用 `chi_sim+eng` 混合包

### 问题 3：OCRmyPDF 报错缺少 unpaper

**症状：** `--clean` 参数需要 unpaper 程序

**解决方案：**
1. ✅ 已修复：移除 `--clean` 参数
2. 改用 OpenCV 预处理（内置）
3. 或安装 unpaper：`choco install unpaper`

### 问题 4：处理速度慢

**解决方案：**
1. 确认并行处理已启用（`parallel_files=2`）
2. 降低 DPI（如 450→300）
3. 减少 `max_pages_per_batch`（如 30→20）

---

## 📊 性能基准

### 测试环境
- CPU：Intel i5-8 代
- 内存：16GB
- 文件：11 页 PDF（含表格）

### 处理时间对比

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **单文件 OCR（11 页）** | ~120 秒 | ~70 秒 | 42%⬆️ |
| **5 文件批量 OCR** | ~600 秒 | ~200 秒 | **3 倍⬆️** |
| **表格识别率** | ~70% | ~95% | 25%⬆️ |

---

## 🔬 技术细节

### OCRmyPDF 命令参数

```bash
ocrmypdf \
  --language chi_sim \
  --output-type pdf \
  --image-dpi 450 \
  --jobs 4 \
  --force-ocr \
  --remove-background \
  --tesseract-pagesegmode 6 \
  --tesseract-thresholding sauvola \
  --tesseract-config "tessedit_write_txt=1" \
  input.pdf output.pdf
```

### OpenCV 图像预处理

```python
def enhance_image_for_ocr(img_path):
    import cv2
    import numpy as np
    
    img = cv2.imread(str(img_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. 自适应直方图均衡化（增强对比度）
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 2. 去噪
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
    
    # 3. 二值化（增强文字边缘）
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    cv2.imwrite(str(img_path), binary)
```

---

## 📝 开发日志

### 2026-03-20 v2.0

**优化内容：**
- ✅ 并行处理机制（2 倍速度提升）
- ✅ 表格 OCR 优化（PSM 6 + Sauvola）
- ✅ 中文乱码修复（纯中文语言包）
- ✅ 移除外部依赖（unpaper/scikit-image）

**Bug 修复：**
- 🐛 OCRmyPDF 不支持 `--contrast` 参数
- 🐛 `--clean` 需要 unpaper
- 🐛 中文复制乱码（`chi_sim+eng` → `chi_sim`）

**负责人：** 陈龙一

---

## 🤝 贡献指南

### 如何参与开发

1. **Fork 仓库**
2. **创建分支**
   ```bash
   git checkout -b feature/your-feature
   ```
3. **提交更改**
   ```bash
   git commit -m "feat: add your feature"
   ```
4. **推送分支**
   ```bash
   git push origin feature/your-feature
   ```
5. **创建 Pull Request**

### 代码规范

- 遵循 PEP 8（Python）
- 使用类型注解
- 添加必要的注释
- 测试通过后再提交

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- **GitHub 仓库：** https://github.com/zjgzcc/pdf-converter-pro
- **OCRmyPDF 文档：** https://ocrmypdf.readthedocs.io/
- **Tesseract 文档：** https://tesseract-ocr.github.io/
- **OpenCV 文档：** https://docs.opencv.org/

---

**最后更新：** 2026-03-20 13:15  
**维护人：** 陈龙一
