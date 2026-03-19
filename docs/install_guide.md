# Windows 环境安装指南 - PDF Converter Pro

本指南详细说明在 Windows 系统上部署 PDF Converter Pro 所需的所有步骤。

---

## 📋 系统要求

- **操作系统**: Windows 10/11 (64 位)
- **Python**: 3.9 或更高版本
- **内存**: 建议 8GB 以上
- **磁盘空间**: 至少 5GB 可用空间
- **GPU** (可选): NVIDIA 显卡用于 AI 加速

---

## 🔧 第一步：安装 Python

### 方法一：官方安装（推荐）

1. 访问 https://www.python.org/downloads/
2. 下载最新 Python 3.11 或 3.12 安装包
3. 运行安装程序，**务必勾选 "Add Python to PATH"**
4. 点击 "Install Now"

### 验证安装
```powershell
# 打开 PowerShell 或 CMD
python --version
# 应输出：Python 3.x.x

pip --version
# 应输出：pip x.x.x from ...
```

### 方法二：使用 winget（Windows 包管理器）
```powershell
winget install Python.Python.3.12
```

---

## 📦 第二步：安装项目依赖

### 克隆项目（如未克隆）
```powershell
cd C:\Users\chche\.openclaw\workspace
git clone <项目仓库地址> pdf-converter-pro
cd pdf-converter-pro
```

### 创建虚拟环境（推荐）
```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 如果提示权限问题，执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 安装依赖包
```powershell
# 升级 pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 手动安装核心依赖
```powershell
# OCR 处理
pip install ocrmypdf
pip install paddlepaddle
pip install paddleocr

# PDF 处理
pip install pymupdf
pip install pdf2image
pip install pypdf
pip install pdfplumber

# 图像处理
pip install pillow
pip install opencv-python
pip install numpy

# 去水印
pip install iopaint

# GUI
pip install PyQt5
```

---

## 🔤 第三步：安装 Tesseract OCR

### 下载 Tesseract

1. 访问 UB-Mannheim 下载页面:
   https://github.com/UB-Mannheim/tesseract/wiki

2. 下载最新安装包（推荐）:
   - `tesseract-ocr-w64-setup-5.x.x.exe` (64 位)

3. 运行安装程序，记住安装路径（默认）:
   `C:\Program Files\Tesseract-OCR\`

### 安装中文语言包

#### 方法一：安装时选择
在安装过程中，勾选以下语言包：
- ☑ Chinese (Simplified) - 简体中文
- ☑ Chinese (Traditional) - 繁体中文
- ☑ English - 英文

#### 方法二：手动下载语言包

1. 访问 tessdata 仓库:
   https://github.com/tesseract-ocr/tessdata

2. 下载以下文件:
   - `chi_sim.traineddata` (简体中文)
   - `chi_tra.traineddata` (繁体中文)
   - `eng.traineddata` (英文)

3. 复制到 tessdata 目录:
   ```
   C:\Program Files\Tesseract-OCR\tessdata\
   ```

### 配置环境变量

1. 右键"此电脑" → "属性" → "高级系统设置"
2. 点击"环境变量"
3. 在"系统变量"中找到 `Path`
4. 点击"编辑" → "新建"
5. 添加 Tesseract 安装路径:
   ```
   C:\Program Files\Tesseract-OCR\
   ```
6. 点击"确定"保存

### 验证安装
```powershell
tesseract --version
# 应输出 Tesseract 版本信息

tesseract --list-langs
# 应列出已安装的语言包，包括 chi_sim, eng 等
```

---

## 🖼️ 第四步：安装 Poppler（PDF 转图片必需）

### 下载 Poppler

1. 访问 releases 页面:
   https://github.com/oschwartz10612/poppler-windows/releases

2. 下载最新版本的 ZIP 文件:
   `Release-xx.xx.x-0.zip`

3. 解压到合适位置，例如:
   `C:\Program Files\poppler\`

### 配置环境变量

1. 添加 Poppler bin 目录到 PATH:
   ```
   C:\Program Files\poppler\Library\bin
   ```

2. 验证安装:
   ```powershell
   pdftoppm -h
   # 应显示帮助信息
   ```

---

## 🚀 第五步：安装 GPU 加速（可选）

### NVIDIA GPU 用户

#### 安装 CUDA（如未安装）
1. 访问 https://developer.nvidia.com/cuda-downloads
2. 选择 Windows + 对应版本
3. 下载安装

#### 安装 PaddlePaddle GPU 版本
```powershell
# 卸载 CPU 版本（如已安装）
pip uninstall paddlepaddle -y

# 安装 GPU 版本
pip install paddlepaddle-gpu

# 或使用国内镜像
pip install paddlepaddle-gpu -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 验证 GPU 支持
```python
import paddle
paddle.utils.run_check()
# 应输出 "PaddlePaddle is installed successfully!"
```

---

## ✅ 第六步：验证安装

### 运行测试脚本
```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 测试 Python 依赖
python -c "import ocrmypdf; print('OCRmyPDF:', ocrmypdf.__version__)"
python -c "import paddleocr; print('PaddleOCR installed')"
python -c "import fitz; print('PyMuPDF:', fitz.__version__)"
python -c "import iopaint; print('IOPaint installed')"

# 测试 Tesseract
python -c "import pytesseract; print('Tesseract:', pytesseract.get_tesseract_version())"

# 测试 Poppler
python -c "from pdf2image import convert_from_path; print('Poppler OK')"
```

### 运行项目
```powershell
# 启动 GUI
python main.py

# 或运行核心模块测试
python -m core.converter
```

---

## ❓ 常见问题解决

### 问题 1: pip 安装失败
**错误**: `Could not fetch URL` 或连接超时

**解决方案**:
```powershell
# 使用国内镜像
pip install <包名> -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip install <包名> -i https://mirrors.aliyun.com/pypi/simple/
```

### 问题 2: Tesseract 找不到
**错误**: `TesseractNotFoundError: tesseract is not installed`

**解决方案**:
```python
# 在代码中指定 Tesseract 路径
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

或在环境变量中添加 Tesseract 路径到 PATH。

### 问题 3: 中文识别乱码
**原因**: 未安装中文语言包

**解决方案**:
1. 下载 `chi_sim.traineddata`
2. 放到 `C:\Program Files\Tesseract-OCR\tessdata\`
3. 使用 `lang='chi_sim'` 参数

### 问题 4: pdf2image 报错
**错误**: `PDFInfoNotInstalledError`

**原因**: 未安装 Poppler

**解决方案**:
1. 下载并安装 Poppler（见第四步）
2. 将 Poppler bin 目录添加到 PATH

### 问题 5: PaddleOCR 模型下载失败
**错误**: 模型下载超时或失败

**解决方案**:
```python
# 手动下载模型并指定路径
from paddleocr import PaddleOCR
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',
    download=True,
    det_model_dir='./models/det',
    rec_model_dir='./models/rec'
)
```

或使用国内镜像源下载模型文件。

### 问题 6: 虚拟环境激活失败
**错误**: `无法加载脚本，因为在此系统上禁止运行脚本`

**解决方案**:
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 7: OpenCV 导入错误
**错误**: `ImportError: DLL load failed`

**解决方案**:
```powershell
# 卸载后重新安装
pip uninstall opencv-python opencv-python-headless -y
pip install opencv-python-headless
```

### 问题 8: PyQt5 界面不显示
**错误**: 程序运行但无界面

**解决方案**:
```powershell
# 重新安装 PyQt5
pip uninstall PyQt5 -y
pip install PyQt5==5.15.9
```

---

## 📝 快速检查清单

安装完成后，确认以下项目：

- [ ] Python 3.9+ 已安装并添加到 PATH
- [ ] 虚拟环境已创建并激活
- [ ] 所有 Python 依赖包已安装
- [ ] Tesseract OCR 已安装
- [ ] 中文语言包已安装（chi_sim.traineddata）
- [ ] Poppler 已安装并添加到 PATH
- [ ] 环境变量 PATH 配置正确
- [ ] 测试脚本运行无错误
- [ ] 项目可以正常启动

---

## 🔗 相关资源

- [Python 官方下载](https://www.python.org/downloads/)
- [Tesseract Windows 安装包](https://github.com/UB-Mannheim/tesseract/wiki)
- [Poppler Windows 版本](https://github.com/oschwartz10612/poppler-windows/releases)
- [PaddlePaddle 安装指南](https://www.paddlepaddle.org.cn/install/quick)

---

*最后更新: 2026-03-19*
