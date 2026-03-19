# OCR 模块技术文档

📊 赤影【技术】开发  
🧪 青影【测试】验证  
⚙️ 紫影【研发】评审

---

## 功能概述

OCR 模块提供完整的 PDF 文字识别功能，支持：

1. **OCRmyPDF 引擎** - 推荐，功能最完整
2. **Tesseract 引擎** - 开源 OCR 引擎
3. **PaddleOCR 引擎** - 百度开源，中文识别优秀

### 核心功能

- ✅ 扫描 PDF 转可搜索 PDF（添加文本层）
- ✅ 批量 OCR 处理（多线程加速）
- ✅ 多种质量预设（快速/标准/高质量/最佳）
- ✅ 进度回调支持
- ✅ 完善的错误处理

---

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

确保系统已安装：

- **OCRmyPDF**: `brew install ocrmypdf` (macOS) 或 `apt install ocrmypdf` (Linux)
- **Tesseract**: `brew install tesseract` 或 `apt install tesseract-ocr`

### 基本使用

```python
from pathlib import Path
from core.ocr import quick_ocr

# 最简单的用法
result = quick_ocr(
    Path("scan.pdf"),
    language="chi_sim+eng"
)

if result.success:
    print(f"成功！输出：{result.output_file}")
```

### 添加文本层

```python
from core.ocr import add_text_layer

success = add_text_layer(
    input_pdf=Path("scan.pdf"),
    output_pdf=Path("searchable.pdf"),
    language="chi_sim+eng",
    dpi=300
)
```

---

## 详细用法

### 1. 使用 OCR 引擎

```python
from core.ocr import OCREngine, OCREngineType, OCRConfig, OCRQuality

# 创建配置
config = OCRConfig(
    language="chi_sim+eng",  # 语言
    dpi=300,                  # 分辨率
    force_ocr=True,           # 强制 OCR
    quality=OCRQuality.STANDARD,  # 质量预设
    threads=4,                # OCRmyPDF 内部线程数
    optimize=True,            # 优化输出 PDF
    deskew=False,             # 自动纠正倾斜
    clean=False               # 清理图像噪声
)

# 创建引擎
engine = OCREngine(
    engine_type=OCREngineType.OCRMYDF,
    config=config
)

# 检查引擎可用性
if engine.is_engine_available():
    result = engine.convert_to_searchable_pdf(
        Path("input.pdf"),
        Path("output.pdf")
    )
```

### 2. 质量预设

```python
from core.ocr import OCRQuality, OCRConfig

# 快速模式 - 150 DPI, 不优化
config = OCRConfig(quality=OCRQuality.FAST)

# 标准模式 - 300 DPI, 优化
config = OCRConfig(quality=OCRQuality.STANDARD)

# 高质量 - 450 DPI, 清理噪声
config = OCRConfig(quality=OCRQuality.HIGH)

# 最佳质量 - 600 DPI, 纠正倾斜 + 清理
config = OCRConfig(quality=OCRQuality.BEST)
```

### 3. 批量处理

```python
from core.ocr import batch_ocr, OCRConfig, OCREngineType

# 批量处理目录中的所有 PDF
success, fail, results = batch_ocr(
    input_dir=Path("input_pdfs"),
    output_dir=Path("output_pdfs"),
    config=OCRConfig(language="chi_sim+eng"),
    engine_type=OCREngineType.OCRMYDF,
    max_workers=4,  # 4 个线程并行
)

print(f"成功：{success}, 失败：{fail}")
```

### 4. 进度回调

```python
from core.ocr import OCREngine, OCRProgress, OCRConfig

def show_progress(progress: OCRProgress):
    if progress.total_files > 0:
        percent = (progress.current_page / progress.total_files * 100)
        print(f"进度：{progress.current_page}/{progress.total_files} ({percent:.1f}%)")
    print(f"状态：{progress.status} - {progress.message}")

engine = OCREngine(
    config=OCRConfig(),
    progress_callback=show_progress
)

result = engine.convert_to_searchable_pdf(
    Path("input.pdf"),
    Path("output.pdf")
)
```

---

## 命令行工具

### 批量 OCR

```bash
# 基本用法
python scripts/batch_ocr.py input/ output/

# 指定线程数和质量
python scripts/batch_ocr.py input/ output/ --threads 8 --quality high

# 指定语言和 DPI
python scripts/batch_ocr.py input/ output/ --lang eng --dpi 600

# 详细输出
python scripts/batch_ocr.py input/ output/ --verbose
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input_dir` | 输入目录 | 必需 |
| `output_dir` | 输出目录 | 必需 |
| `--threads, -t` | 线程数 | 4 |
| `--quality, -q` | 质量 (fast/standard/high/best) | standard |
| `--language, -l` | OCR 语言 | chi_sim+eng |
| `--dpi` | DPI | 300 |
| `--force-ocr` | 强制 OCR | False |
| `--engine` | 引擎 (ocrmypdf/tesseract/paddleocr) | ocrmypdf |
| `--verbose, -v` | 详细输出 | False |

---

## API 参考

### 类

#### `OCREngineType` (Enum)

OCR 引擎类型枚举

- `OCRMYDF` - OCRmyPDF（推荐）
- `TESSERACT` - Tesseract
- `PADDLEOCR` - PaddleOCR

#### `OCRQuality` (Enum)

质量预设枚举

- `FAST` - 快速模式
- `STANDARD` - 标准模式
- `HIGH` - 高质量
- `BEST` - 最佳质量

#### `OCRConfig` (dataclass)

OCR 配置

```python
@dataclass
class OCRConfig:
    language: str = "chi_sim+eng"
    dpi: int = 300
    force_ocr: bool = True
    skip_text: bool = False
    quality: OCRQuality = OCRQuality.STANDARD
    threads: int = 1
    optimize: bool = True
    deskew: bool = False
    clean: bool = False
```

#### `OCRProgress` (dataclass)

进度信息

```python
@dataclass
class OCRProgress:
    current_page: int = 0
    total_pages: int = 0
    current_file: str = ""
    total_files: int = 0
    status: str = "pending"
    message: str = ""
    percent: float = 0.0
```

#### `OCRResult` (dataclass)

OCR 结果

```python
@dataclass
class OCRResult:
    success: bool
    input_file: Path
    output_file: Optional[Path] = None
    pages_processed: int = 0
    text_extracted: str = ""
    error_message: str = ""
    processing_time: float = 0.0
```

#### `OCREngine` (class)

OCR 引擎主类

```python
class OCREngine:
    def __init__(
        self,
        engine_type: OCREngineType = OCREngineType.OCRMYDF,
        config: Optional[OCRConfig] = None,
        progress_callback: Optional[Callable[[OCRProgress], None]] = None
    )
    
    def is_engine_available(self) -> bool
    def get_available_engine() -> Optional[OCREngineType]
    def convert_to_searchable_pdf(
        input_pdf: Path,
        output_pdf: Path,
        config: Optional[OCRConfig] = None
    ) -> OCRResult
    def extract_text(pdf_path: Path) -> str
    def has_text_layer(pdf_path: Path) -> bool
```

### 函数

#### `batch_ocr`

批量 OCR 处理

```python
def batch_ocr(
    input_dir: Path,
    output_dir: Path,
    config: Optional[OCRConfig] = None,
    engine_type: OCREngineType = OCREngineType.OCRMYDF,
    max_workers: int = 4,
    progress_callback: Optional[Callable[[OCRProgress], None]] = None
) -> Tuple[int, int, List[OCRResult]]
```

返回：`(成功数，失败数，结果列表)`

#### `add_text_layer`

便捷函数：添加文本层

```python
def add_text_layer(
    input_pdf: Path,
    output_pdf: Path,
    language: str = "chi_sim+eng",
    dpi: int = 300,
    force_ocr: bool = True
) -> bool
```

#### `quick_ocr`

便捷函数：快速 OCR

```python
def quick_ocr(
    input_pdf: Path,
    output_pdf: Optional[Path] = None,
    **kwargs
) -> OCRResult
```

---

## 语言代码

| 语言 | 代码 |
|------|------|
| 简体中文 | `chi_sim` |
| 繁体中文 | `chi_tra` |
| 英文 | `eng` |
| 中英文混合 | `chi_sim+eng` |
| 日文 | `jpn` |
| 韩文 | `kor` |

---

## 性能优化建议

### 1. 批量处理

- 使用多线程：`max_workers=4` 或更高
- 根据 CPU 核心数调整线程数
- 避免过多线程导致 I/O 瓶颈

### 2. 质量选择

- 快速模式：适合草稿、内部文档
- 标准模式：适合一般用途
- 高质量：适合重要文档、合同
- 最佳质量：适合档案、法律文件

### 3. DPI 设置

- 150 DPI：快速预览
- 300 DPI：标准质量（推荐）
- 450 DPI：高质量
- 600 DPI：档案级质量

---

## 故障排除

### OCRmyPDF 不可用

```bash
# macOS
brew install ocrmypdf

# Ubuntu/Debian
apt install ocrmypdf

# Windows (WSL)
wsl sudo apt install ocrmypdf
```

### Tesseract 语言包

```bash
# 安装中文语言包
brew install tesseract-lang  # macOS
apt install tesseract-ocr-chi-sim  # Ubuntu
```

### 内存不足

- 降低 DPI 设置
- 减少线程数
- 分批处理大文件

### 识别准确率低

- 提高 DPI（至少 300）
- 使用高质量预设
- 确保图像清晰
- 尝试不同引擎

---

## 测试

```bash
# 运行 OCR 测试
pytest tests/test_ocr.py -v

# 运行示例
python examples/ocr_examples.py

# 批量处理测试
python scripts/batch_ocr.py tests/ tests/output/ --verbose
```

---

## 更新日志

### v2.0 (2026-03-19)

- ✅ 优化 OCRmyPDF 和 Tesseract 集成
- ✅ 添加 PDF 文本层功能
- ✅ 实现多线程批量处理
- ✅ 新增质量预设
- ✅ 完善进度回调
- ✅ 改进错误处理

---

_文档版本：2.0_  
_最后更新：2026-03-19_
