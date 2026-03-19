# PDF Converter Pro - 技术模块优化报告

🔍 **龙二【技术】** 完成  
📅 2026-03-19

## 优化概览

本次优化完成了三个核心模块的技术升级：

1. ✅ `core/ocr.py` - OCR 模块增强
2. ✅ `core/converter.py` - WORD 转换模块增强
3. ✅ `core/pipeline.py` - 统一处理流程（新建）

---

## 1. OCR 模块优化 (`core/ocr.py`)

### 新增功能

#### 1.1 多 OCR 引擎支持

```python
class OCREngineType(Enum):
    OCRMYDF = "ocrmypdf"      # 基于 Tesseract 的 OCRmyPDF
    TESSERACT = "tesseract"   # Tesseract 直接调用
    PADDLEOCR = "paddleocr"   # PaddleOCR
```

**引擎特性对比：**

| 引擎 | 优势 | 适用场景 |
|------|------|----------|
| OCRmyPDF | 成熟稳定，直接输出可搜索 PDF | 通用场景 |
| Tesseract | 灵活控制，可自定义参数 | 特殊需求 |
| PaddleOCR | 中文识别效果好 | 中文文档 |

#### 1.2 进度回调机制

```python
class OCRProgress:
    current_page: int       # 当前页
    total_pages: int        # 总页数
    status: str            # pending/processing/completed/failed
    message: str           # 状态消息
```

**使用示例：**

```python
def on_progress(progress):
    print(f"OCR 进度：{progress.current_page}/{progress.total_pages}")
    print(f"状态：{progress.message}")

engine = OCREngine(
    engine_type=OCREngineType.OCRMYDF,
    progress_callback=on_progress
)
```

#### 1.3 增强的错误处理

```python
class OCRError(Exception):
    """OCR 专用异常"""
    pass

# 使用
try:
    success = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
    if not success:
        raise OCRError("OCR 处理失败")
except OCRError as e:
    logger.error(f"OCR 错误：{e}")
except Exception as e:
    logger.error(f"OCR 异常：{e}")
```

### 优化细节

1. **参数增强**
   - `dpi`: 支持自定义分辨率（默认 300）
   - `skip_text`: 跳过已有文本的页面
   - `force_ocr`: 强制 OCR 所有页面

2. **日志记录**
   - 使用 `logging` 模块替代 `print`
   - 分级记录（INFO/WARNING/ERROR）

3. **超时控制**
   - 整体超时：600 秒
   - 单页超时：120 秒（Tesseract 模式）

---

## 2. WORD 转换模块优化 (`core/converter.py`)

### 新增功能

#### 2.1 pdf2docx 备选方案

```python
class ConvertMethod(Enum):
    PADDLEOCR = "paddleocr"   # 主方案：版面恢复
    PDF2DOCX = "pdf2docx"     # 备选：快速转换
    FREEP2W = "freep2w"       # 备选：公式支持
```

**自动降级策略：**

```python
converter = PDF2WordConverter(
    method=ConvertMethod.PADDLEOCR,
    fallback_methods=[
        ConvertMethod.PDF2DOCX,
        ConvertMethod.FREEP2W
    ]
)

# 主方法失败时自动尝试备选
success = converter.convert(input_pdf, output_docx)
```

#### 2.2 优化的 PaddleOCR 参数

```python
cmd = [
    "paddleocr",
    "--det_db_thresh", "0.3",        # 检测阈值优化
    "--det_db_box_score", "0.5",     # 框选分数
    "--rec_batch_num", "6",          # 批量识别数
    "--use_angle_cls", "true",       # 方向分类器
    "--layout", "true",              # 版面分析
    "--table", "true",               # 表格识别
]
```

#### 2.3 格式保持选项

```python
converter = PDF2WordConverter(
    preserve_format=True  # 保持原格式
)

# 带选项的转换
converter.convert_with_options(
    input_pdf=input_pdf,
    output_docx=output_docx,
    options={
        "preserve_format": True,
        "ocr_first": True,  # 先 OCR 后转换
    }
)
```

### 转换方法对比

| 方法 | 速度 | 质量 | 适用场景 |
|------|------|------|----------|
| PaddleOCR | 中 | 高 | 图文混排、表格 |
| pdf2docx | 快 | 中 | 文本型 PDF |
| FreeP2W | 慢 | 高 | 数学公式 |

---

## 3. 统一处理流程 (`core/pipeline.py`)

### 核心特性

#### 3.1 完整流程整合

```
去水印 → OCR → 转换为 WORD
   ↓       ↓         ↓
Watermark  OCR    Converter
```

**使用示例：**

```python
pipeline = ProcessingPipeline(
    remove_watermark=True,      # 去水印
    ocr_enabled=True,           # OCR
    convert_method=ConvertMethod.PADDLEOCR
)

result = pipeline.process_single(input_file, output_file)
```

#### 3.2 进度追踪

```python
class PipelineProgress:
    stage: PipelineStage           # 当前阶段
    status: PipelineStatus         # 状态
    current_file: str             # 当前文件
    total_files: int              # 总文件数
    processed_files: int          # 已处理数
    current_stage_progress: float # 阶段进度
    overall_progress: float       # 总体进度
    message: str                  # 状态消息
```

**进度回调：**

```python
def on_progress(progress: PipelineProgress):
    print(f"总体：{progress.overall_progress*100:.1f}%")
    print(f"阶段：{progress.stage.value}")
    print(f"消息：{progress.message}")

pipeline = ProcessingPipeline(progress_callback=on_progress)
```

#### 3.3 错误恢复机制

**自动恢复策略：**

1. **去水印失败** → 跳过此阶段，继续后续处理
2. **OCR 失败** → 尝试备选 OCR 引擎
3. **转换失败** → 尝试备选转换方法

```python
pipeline = ProcessingPipeline(
    max_recovery_attempts=2  # 最大恢复尝试次数
)

result = pipeline.process_single(input_file, output_file)

if not result.success:
    print(f"失败原因：{result.error_message}")
    print(f"已尝试恢复：{result.recovery_attempts}次")
    print(f"完成阶段：{result.stages_completed}")
```

#### 3.4 断点续传

```python
# 保存检查点
checkpoint = {
    "input_dir": "input_pdfs",
    "processed": ["file1.pdf", "file2.pdf"]
}

# 从检查点恢复
pipeline.resume_from_checkpoint(
    checkpoint_file=Path("checkpoint.json"),
    output_dir=Path("output_word")
)
```

### 流水线阶段

```python
class PipelineStage(Enum):
    WATERMARK_REMOVE = "watermark_remove"
    OCR = "ocr"
    CONVERT = "convert"
    COMPLETED = "completed"
    FAILED = "failed"
```

### 处理结果

```python
@dataclass
class PipelineResult:
    success: bool
    input_file: Path
    output_file: Optional[Path]
    stages_completed: List[PipelineStage]
    error_message: str
    duration_seconds: float
    recovery_attempts: int
```

---

## 4. 使用示例

### 4.1 简单使用

```python
from pathlib import Path
from core import create_pipeline

# 创建流水线
pipeline = create_pipeline(config={
    "remove_watermark": False,
    "ocr_enabled": True,
    "convert_method": "paddleocr",
})

# 处理单个文件
result = pipeline.process_single(
    Path("input.pdf"),
    Path("output.docx")
)

print(f"成功：{result.success}")
```

### 4.2 批量处理

```python
from core import ProcessingPipeline, ConvertMethod

pipeline = ProcessingPipeline(
    ocr_enabled=True,
    convert_method=ConvertMethod.PADDLEOCR,
    convert_fallback_methods=[ConvertMethod.PDF2DOCX]
)

results = pipeline.process_batch(
    input_dir=Path("input_pdfs"),
    output_dir=Path("output_word")
)

success_count = sum(1 for r in results if r.success)
print(f"成功：{success_count}/{len(results)}")
```

### 4.3 带进度回调

```python
from core import ProcessingPipeline, PipelineProgress

def on_progress(progress: PipelineProgress):
    # 更新 UI 进度条
    update_progress_bar(progress.overall_progress * 100)
    # 显示状态消息
    show_status(progress.message)

pipeline = ProcessingPipeline(progress_callback=on_progress)
pipeline.process_batch(input_dir, output_dir)
```

---

## 5. 依赖要求

### 必需依赖

```bash
# OCR 引擎
pip install ocrmypdf
pip install paddlepaddle paddleocr

# 转换引擎
pip install pdf2docx
pip install freep2w  # 可选，公式支持

# 基础依赖
pip install PyMuPDF pillow opencv-python
```

### 系统依赖

```bash
# Tesseract OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# Tesseract OCR (Windows)
# 下载安装：https://github.com/UB-Mannheim/tesseract/wiki

# Tesseract OCR (macOS)
brew install tesseract
```

---

## 6. 性能优化建议

### 6.1 批量处理优化

```python
# ✅ 推荐：批量处理
results = pipeline.process_batch(input_dir, output_dir)

# ❌ 不推荐：循环调用单个处理
for file in input_files:
    pipeline.process_single(file, output)
```

### 6.2 OCR 参数调优

| 场景 | DPI | 语言 | 引擎 |
|------|-----|------|------|
| 清晰文档 | 300 | chi_sim+eng | OCRmyPDF |
| 模糊文档 | 600 | chi_sim+eng | Tesseract |
| 中文为主 | 300 | ch | PaddleOCR |
| 英文为主 | 300 | eng | OCRmyPDF |

### 6.3 内存管理

```python
# 大文件处理时启用临时文件清理
pipeline = ProcessingPipeline(cleanup_temp=True)

# 处理完成后手动清理
pipeline._cleanup_temp_dir()
```

---

## 7. 错误码说明

| 错误类型 | 错误码 | 说明 |
|----------|--------|------|
| OCRError | 1001 | OCR 引擎未安装 |
| OCRError | 1002 | OCR 超时 |
| OCRError | 1003 | 输入文件不存在 |
| ConvertError | 2001 | 转换引擎未安装 |
| ConvertError | 2002 | 转换超时 |
| PipelineError | 3001 | 流水线配置错误 |
| PipelineError | 3002 | 检查点文件不存在 |

---

## 8. 后续优化方向

### 8.1 待实现功能

- [ ] 支持更多输出格式（TXT, HTML, Markdown）
- [ ] 并行处理（多进程/多线程）
- [ ] GPU 加速（PaddleOCR GPU 版本）
- [ ] 云端 OCR 服务集成（百度/阿里/腾讯）
- [ ] 自定义水印检测模型

### 8.2 性能提升

- [ ] 增量处理（仅处理变化部分）
- [ ] 缓存机制（避免重复 OCR）
- [ ] 流式处理（大文件分块）

---

## 总结

本次优化完成了 PDF Converter Pro 核心模块的技术升级：

✅ **OCR 模块**：支持 3 种引擎，添加进度回调，增强错误处理  
✅ **转换模块**：添加 pdf2docx 备选，优化 PaddleOCR 参数，支持格式保持  
✅ **流水线模块**：整合完整流程，支持进度追踪和错误恢复

代码已就绪，可投入使用。

---

🔍 **龙二【技术】** 汇报完成
