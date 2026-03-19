# 🚀 PDF Converter Pro - 快速部署指南
⚡ 雷影【执行】MVP 验证版

## 📋 目录

1. [环境准备](#环境准备)
2. [安装步骤](#安装步骤)
3. [快速测试](#快速测试)
4. [打包 EXE](#打包-exe)
5. [在另一台电脑运行](#在另一台电脑运行)
6. [故障排除](#故障排除)

---

## 环境准备

### 系统要求

- **操作系统**: Windows 10/11 (64 位)
- **Python**: 3.9 - 3.12
- **内存**: 最少 4GB (推荐 8GB+)
- **磁盘**: 最少 2GB 可用空间

### 检查 Python 版本

```bash
python --version
# 应该显示 Python 3.9.x 或更高版本
```

---

## 安装步骤

### 步骤 1: 克隆或下载项目

```bash
# 如果从 Git 获取
git clone <repository-url>
cd pdf-converter-pro

# 或直接解压 ZIP 文件
```

### 步骤 2: 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# 激活后，命令行前会显示 (venv)
```

### 步骤 3: 安装依赖

```bash
# 基础依赖（MVP 版）
pip install -r requirements.txt

# 或最小依赖（快速启动）
pip install PyMuPDF pdf2docx opencv-python numpy Pillow tqdm
```

### 步骤 4: 安装可选依赖（按需）

```bash
# OCR 功能（需要 Tesseract）
pip install ocrmypdf pytesseract

# Tesseract OCR 引擎（Windows）
# 下载：https://github.com/UB-Mannheim/tesseract/wiki
# 安装后添加到系统 PATH

# 高级 WORD 转换
pip install paddlepaddle paddleocr

# GUI 界面
pip install PyQt6
```

---

## 快速测试

### 测试 1: 运行快速测试脚本

```bash
# 一键测试所有模块
python scripts/quick_test.py
```

**预期输出:**
```
🦎 ============================================================
🦎  PDF Converter Pro - 快速测试套件
🦎  ⚡ 雷影【执行】一键测试
🦎 ============================================================

✅ 所有测试通过！MVP 验证成功！
```

### 测试 2: 运行轻量版

```bash
# 查看帮助
python main_lite.py --help

# 测试单个文件
python main_lite.py test.pdf -o output/

# 测试批量处理
python main_lite.py input_dir/ -o output_dir/
```

### 测试 3: 验证核心功能

```bash
# 创建测试目录
mkdir test_input test_output

# 放入测试 PDF 文件到 test_input/

# 运行处理
python main_lite.py test_input/ -o test_output/ --ocr --word
```

---

## 打包 EXE

### 步骤 1: 安装 PyInstaller

```bash
pip install pyinstaller
```

### 步骤 2: 运行打包脚本

```bash
python scripts/build.py
```

### 步骤 3: 检查输出

```bash
# 查看生成的文件
dir dist\

# 应该看到:
# - PDF Converter Pro.exe
# - DEPLOYMENT.md
```

### 打包选项

```bash
# 手动打包（命令行版本）
pyinstaller --clean --noconfirm --name "PDF Converter Pro" main_lite.py

# 手动打包（GUI 版本）
pyinstaller --clean --noconfirm --windowed --name "PDF Converter Pro GUI" main.py
```

---

## 在另一台电脑运行

### 方案 A: 运行 EXE（推荐）

1. **复制文件到目标电脑**
   ```
   复制整个 dist/ 文件夹到目标电脑
   或只复制 PDF Converter Pro.exe
   ```

2. **在目标电脑运行**
   ```bash
   # 双击运行或命令行
   "PDF Converter Pro.exe" --help
   
   # 处理文件
   "PDF Converter Pro.exe" input.pdf -o output/
   ```

3. **无需安装 Python！**
   - EXE 已包含所有依赖
   - 开箱即用

### 方案 B: 源码部署

1. **在目标电脑安装 Python**
   ```bash
   # 下载 Python: https://www.python.org/downloads/
   # 安装时勾选 "Add Python to PATH"
   ```

2. **安装依赖**
   ```bash
   pip install PyMuPDF pdf2docx opencv-python numpy
   ```

3. **运行**
   ```bash
   python main_lite.py input.pdf -o output/
   ```

---

## 故障排除

### 问题 1: `ModuleNotFoundError: No module named 'xxx'`

**原因**: 缺少依赖

**解决**:
```bash
pip install -r requirements.txt
```

### 问题 2: `ocrmypdf: command not found`

**原因**: 未安装 Tesseract OCR 引擎

**解决**:
```bash
# 方案 1: 安装 Tesseract
# 下载：https://github.com/UB-Mannheim/tesseract/wiki

# 方案 2: 跳过 OCR
python main_lite.py input.pdf -o output/ --no-ocr

# 方案 3: 使用简化版（自动降级）
# MVP 版会自动跳过不可用的功能
```

### 问题 3: EXE 运行时报错

**原因**: 缺少运行时依赖

**解决**:
```bash
# 重新打包，确保包含所有依赖
pip install --upgrade pyinstaller
python scripts/build.py

# 或复制整个 dist 文件夹，不只是 EXE
```

### 问题 4: WORD 转换失败

**原因**: pdf2docx 兼容性问题

**解决**:
```bash
# 确保安装了正确版本
pip install --upgrade pdf2docx

# 或使用替代方案
pip install paddleocr
```

### 问题 5: 内存不足

**原因**: 处理大型 PDF 文件

**解决**:
```bash
# 分批处理文件
# 或增加系统虚拟内存
# 或使用 64 位 Python
```

---

## 📊 性能基准

| 操作 | 速度 | 备注 |
|------|------|------|
| OCR (单页) | ~2-5 秒 | 取决于图像质量 |
| PDF→WORD (单页) | ~3-8 秒 | 取决于布局复杂度 |
| 去水印 (单页) | ~1-3 秒 | 简单水印 |
| 批量处理 (10 页) | ~30-60 秒 | 并行处理 |

---

## 🦎 版本信息

- **版本**: MVP 0.1.0
- **日期**: 2026-03-19
- **执行**: ⚡ 雷影【执行】
- **团队**: 影诺办

---

## 快速命令参考

```bash
# 帮助
python main_lite.py --help

# 单个文件
python main_lite.py file.pdf -o output/

# 批量处理
python main_lite.py input_dir/ -o output_dir/

# 仅 OCR
python main_lite.py file.pdf -o output/ --ocr --no-word

# 仅 WORD
python main_lite.py file.pdf -o output/ --no-ocr --word

# 快速测试
python scripts/quick_test.py

# 打包
python scripts/build.py
```

---

**快速部署 | 高效执行 | MVP 验证** 🚀
