# 技术参考资料 - PDF Converter Pro

本文档整理了项目使用的核心技术栈官方文档和最佳实践。

---

## 📚 OCRmyPDF

### 官方资源
- **官方文档**: https://ocrmypdf.readthedocs.io/
- **GitHub 仓库**: https://github.com/jbarlow83/OCRmyPDF
- **PyPI 页面**: https://pypi.org/project/ocrmypdf/

### 核心功能
- PDF OCR 处理（光学字符识别）
- 生成可搜索的 PDF 文件
- 支持多种 OCR 引擎（Tesseract 等）
- PDF 图像预处理和优化

### 最佳实践
1. **图像预处理**: 使用 `--deskew` 自动矫正倾斜页面
2. **语言设置**: 使用 `-l chi_sim+eng` 指定中英文混合识别
3. **输出优化**: 使用 `--optimize 3` 进行最高级别压缩
4. **批量处理**: 结合 Python 脚本实现批量 PDF 处理

### 常用命令示例
```bash
# 基础 OCR 处理
ocrmypdf input.pdf output.pdf

# 中英文识别 + 图像矫正
ocrmypdf -l chi_sim+eng --deskew input.pdf output.pdf

# 优化输出文件大小
ocrmypdf --optimize 3 input.pdf output.pdf

# 仅 OCR 不修改原 PDF
ocrmypdf --skip-text input.pdf output.pdf
```

---

## 📚 PaddleOCR

### 官方资源
- **GitHub 仓库**: https://github.com/PaddlePaddle/PaddleOCR
- **官方文档**: https://paddleocr.readthedocs.io/
- **快速开始**: https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/quickstart_en.md

### 核心功能
- 超轻量 OCR 系统（仅几 MB）
- 支持 80+ 语言识别
- 文本检测 + 文本识别端到端处理
- 支持表格识别、版面分析

### 安装指南
```bash
# 安装 PaddlePaddle
pip install paddlepaddle

# 安装 PaddleOCR
pip install paddleocr

# 或使用国内镜像
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 使用示例
```python
from paddleocr import PaddleOCR

# 初始化（自动下载模型）
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# 识别图片
img_path = 'test.jpg'
result = ocr.ocr(img_path, cls=True)

# 输出结果
for line in result:
    print(line)
```

### 最佳实践
1. **模型选择**: 根据场景选择轻量版或高精度版模型
2. **批量处理**: 使用 `batch_size` 参数提升处理效率
3. **角度分类**: 启用 `use_angle_cls=True` 处理倾斜文本
4. **GPU 加速**: 生产环境建议使用 GPU 版本 PaddlePaddle

---

## 📚 IOPaint（去水印）

### 官方资源
- **GitHub 仓库**: https://github.com/Sanster/IOPaint
- **在线演示**: https://paint.byai.me/
- **文档**: https://github.com/Sanster/IOPaint#installation

### 核心功能
- AI 图像修复（Inpainting）
- 水印/文字/物体移除
- 支持多种 AI 模型（LaMa、MAT 等）
- 本地运行，保护隐私

### 安装指南
```bash
# 基础安装
pip install iopaint

# 或使用国内镜像
pip install iopaint -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 使用示例
```bash
# 启动 Web UI
iopaint start

# 命令行处理
iopaint run --image input.jpg --mask mask.png --output output.jpg

# 指定模型
iopaint start --model=lama
```

### Python API 使用
```python
from iopaint import InpaintRunner

runner = InpaintRunner()
runner.run(image='input.jpg', mask='mask.png', output='output.jpg')
```

### 最佳实践
1. **掩码制作**: 使用图像处理工具精确标记需要移除的区域
2. **模型选择**: LaMa 适合一般场景，MAT 适合复杂背景
3. **批量处理**: 使用脚本批量处理多张图片
4. **后处理**: 必要时进行边缘融合处理

---

## 📚 PDF 处理库

### PyMuPDF (fitz)
- **官方文档**: https://pymupdf.readthedocs.io/
- **GitHub**: https://github.com/pymupdf/PyMuPDF
- **用途**: PDF 读取、编辑、渲染

```bash
pip install pymupdf
```

### pdf2image
- **官方文档**: https://pdf2image.readthedocs.io/
- **GitHub**: https://github.com/Belval/pdf2image
- **用途**: PDF 转图片（依赖 poppler）

```bash
pip install pdf2image
# Windows 需安装 poppler: https://github.com/oschwartz10612/poppler-windows/releases
```

### pdfplumber
- **官方文档**: https://github.com/jsvine/pdfplumber
- **用途**: PDF 文本和表格提取

```bash
pip install pdfplumber
```

### PyPDF2 / pypdf
- **官方文档**: https://pypdf.readthedocs.io/
- **GitHub**: https://github.com/py-pdf/pypdf
- **用途**: PDF 合并、分割、元数据操作

```bash
pip install pypdf
```

---

## 📚 Tesseract OCR

### 官方资源
- **GitHub**: https://github.com/tesseract-ocr/tesseract
- **文档**: https://tesseract-ocr.github.io/
- **Python 封装**: https://github.com/madmaze/pytesseract

### 安装（Windows）
1. 下载安装程序: https://github.com/UB-Mannheim/tesseract/wiki
2. 下载中文语言包:
   - 简体中文: `chi_sim.traineddata`
   - 繁体中文: `chi_tra.traineddata`
3. 放置到 `C:\Program Files\Tesseract-OCR\tessdata\`

### Python 使用
```python
import pytesseract
from PIL import Image

# 设置 Tesseract 路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 识别图片
text = pytesseract.image_to_string(Image.open('test.png'), lang='chi_sim+eng')
print(text)
```

---

## 📚 其他相关资源

### 图像处理
- **OpenCV**: https://docs.opencv.org/
- **Pillow**: https://pillow.readthedocs.io/

### 深度学习
- **PyTorch**: https://pytorch.org/docs/
- **ONNX Runtime**: https://onnxruntime.ai/docs/

### PDF 规范
- **PDF 1.7 规范**: https://opensource.adobe.com/dc-acrobat-sdk-docs/library/pdfreference/
- **PDF/A 标准**: https://www.iso.org/standard/51949.html

---

*最后更新: 2026-03-19*
