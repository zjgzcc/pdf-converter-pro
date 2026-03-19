# CLI 使用指南 🖥️

PDF Converter Pro 提供强大的命令行工具，支持单文件处理、批量转换、配置管理等。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本用法

```bash
# 处理单个文件
python cli.py process input.pdf

# 指定输出文件
python cli.py process input.pdf -o output.docx

# 批量处理目录
python cli.py process ./pdfs -o ./output

# 使用配置文件
python cli.py process input.pdf -c config.json
```

## 命令详解

### 1. process - 处理文件

处理单个 PDF 文件或批量处理目录。

```bash
python cli.py process <input> [选项]
```

**参数:**
- `input`: 输入文件路径或目录

**选项:**
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出文件/目录路径 | 自动生成 |
| `-c, --config` | 配置文件路径 | config.json |
| `-p, --pattern` | 文件匹配模式 | *.pdf |
| `--no-ocr` | 跳过 OCR 处理 | False |
| `--no-watermark` | 跳过去水印 | False |
| `--watermark` | 启用去水印 | False |
| `--ocr-language` | OCR 语言 | chi_sim+eng |
| `--convert-method` | 转换方法 | paddleocr |
| `--log-level` | 日志级别 | INFO |
| `--log-file` | 日志文件路径 | 无 |

**示例:**

```bash
# 处理单个文件，跳过 OCR
python cli.py process document.pdf --no-ocr

# 批量处理，启用去水印
python cli.py process ./scanned_pdfs --watermark -o ./clean_docs

# 使用繁体中文 OCR
python cli.py process book.pdf --ocr-language chi_tra+eng

# 指定转换方法
python cli.py process report.pdf --convert-method pdf2docx

# 输出调试日志
python cli.py process input.pdf --log-level DEBUG --log-file debug.log
```

### 2. init - 初始化配置

创建默认配置文件。

```bash
python cli.py init [-o 输出路径]
```

**示例:**

```bash
# 在当前目录创建 config.json
python cli.py init

# 指定配置文件路径
python cli.py init -o ./configs/my_config.json
```

### 3. info - 显示系统信息

显示支持的引擎、方法和版本信息。

```bash
python cli.py info
```

**输出示例:**

```
📊 PDF Converter Pro - 系统信息

支持的 OCR 引擎:
  - ocrmypdf
  - tesseract
  - paddleocr

支持的转换方法:
  - paddleocr
  - pdf2docx
  - pymupdf

支持的 OCR 语言:
  - chi_sim: 简体中文
  - chi_tra: 繁体中文
  - eng: 英文
  - chi_sim+eng: 中英文混合
```

### 4. check - 检查依赖

检查系统依赖是否已安装。

```bash
python cli.py check
```

## 配置文件

配置文件为 JSON 格式，包含所有可配置选项：

```json
{
  "pipeline": {
    "remove_watermark": false,
    "watermark_method": "auto",
    "ocr_enabled": true,
    "ocr_engine": "ocrmypdf",
    "ocr_language": "chi_sim+eng",
    "convert_method": "paddleocr",
    "convert_fallback_methods": ["pdf2docx"],
    "preserve_format": true,
    "max_recovery_attempts": 2
  },
  "ocr": {
    "engine": "ocrmypdf",
    "language": "chi_sim+eng",
    "dpi": 300,
    "deskew": true,
    "clean": true
  },
  "converter": {
    "default_method": "paddleocr",
    "preserve_images": true,
    "preserve_tables": true
  },
  "watermark": {
    "enabled": false,
    "method": "auto",
    "ai_model": "iopaint"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/pdf_converter.log"
  }
}
```

### 配置项说明

#### Pipeline (流水线)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `remove_watermark` | bool | 是否去除水印 | false |
| `watermark_method` | string | 去水印方法 (auto/opencv/iopaint) | auto |
| `ocr_enabled` | bool | 是否启用 OCR | true |
| `ocr_engine` | string | OCR 引擎 (ocrmypdf/tesseract/paddleocr) | ocrmypdf |
| `ocr_language` | string | OCR 识别语言 | chi_sim+eng |
| `convert_method` | string | 转换方法 | paddleocr |
| `convert_fallback_methods` | array | 备选转换方法 | ["pdf2docx"] |
| `preserve_format` | bool | 保持原格式 | true |
| `max_recovery_attempts` | int | 最大错误恢复次数 | 2 |

#### OCR

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `engine` | string | OCR 引擎 | ocrmypdf |
| `language` | string | 识别语言 | chi_sim+eng |
| `dpi` | int | 扫描 DPI | 300 |
| `deskew` | bool | 自动纠偏 | true |
| `clean` | bool | 清理噪点 | true |

#### Converter (转换器)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `default_method` | string | 默认转换方法 | paddleocr |
| `preserve_images` | bool | 保留图片 | true |
| `preserve_tables` | bool | 保留表格 | true |
| `preserve_layout` | bool | 保留布局 | true |

#### Watermark (水印)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `enabled` | bool | 是否启用 | false |
| `method` | string | 去水印方法 | auto |
| `ai_model` | string | AI 模型 (iopaint) | iopaint |

## 高级用法

### 批量处理脚本

创建批处理脚本 `batch_convert.sh` (Linux/Mac) 或 `batch_convert.bat` (Windows):

**Linux/Mac:**
```bash
#!/bin/bash
INPUT_DIR="./input_pdfs"
OUTPUT_DIR="./output_docs"
CONFIG="./config.json"

python cli.py process "$INPUT_DIR" -o "$OUTPUT_DIR" -c "$CONFIG" --log-level INFO
```

**Windows:**
```batch
@echo off
set INPUT_DIR=.\input_pdfs
set OUTPUT_DIR=.\output_docs
set CONFIG=.\config.json

python cli.py process "%INPUT_DIR%" -o "%OUTPUT_DIR%" -c "%CONFIG%" --log-level INFO
```

### 与 GUI 配合使用

CLI 可以与 GUI 版本配合使用：

```bash
# 先用 CLI 批量预处理
python cli.py process ./raw_pdfs --watermark -o ./preprocessed

# 再用 GUI 进行精细调整
python main.py
```

### 集成到工作流

```bash
# 监听目录，自动转换新文件
while true; do
    inotifywait -e create ./incoming
    python cli.py process ./incoming/*.pdf -o ./converted
    mv ./incoming/*.pdf ./archive
done
```

## 故障排除

### 常见问题

**1. OCR 引擎未找到**
```bash
# 安装 OCRmyPDF
pip install ocrmypdf

# 或安装 Tesseract
# Ubuntu/Debian
sudo apt install tesseract-ocr

# Windows: 下载安装包安装
```

**2. 中文字体缺失**
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# macOS
brew install tesseract-lang
```

**3. 转换失败**
- 检查日志：`--log-level DEBUG --log-file debug.log`
- 尝试备选方法：`--convert-method pdf2docx`
- 检查文件是否损坏

### 查看日志

```bash
# 实时查看日志
tail -f logs/pdf_converter.log

# 查看错误日志
grep ERROR logs/pdf_converter.log
```

## 性能优化

### 批量处理优化

```json
{
  "advanced": {
    "parallel_processing": true,
    "max_workers": 4,
    "memory_limit_mb": 2048,
    "timeout_seconds": 300
  }
}
```

### 大文件处理

对于大文件，建议：
1. 增加 `max_recovery_attempts` 到 3-5
2. 启用 `cleanup_temp` 清理临时文件
3. 设置合理的 `timeout_seconds`

## 更多信息

- GitHub: https://github.com/zjgzcc/pdf-converter-pro
- 组织：影诺办
- 文档：`docs/` 目录

---

_最后更新：2026-03-19_
