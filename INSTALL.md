# PDF Converter Pro - 部署指南

## 环境要求

- **Python 3.10 ~ 3.12**（推荐 3.11，不支持 3.13+）
- Windows / Linux / macOS

## 一键部署

```bash
# 1. 拉取代码
git clone https://github.com/zjgzcc/pdf-converter-pro.git
cd pdf-converter-pro

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python web_server.py

# 4. 打开浏览器
# http://localhost:5000
```

## 首次运行

首次 OCR 处理时会自动从 HuggingFace 下载 PaddleOCR 模型（约 20MB），需要联网。
模型缓存在 `~/.paddlex/official_models/`，后续离线可用。

## 功能说明

| 功能 | 说明 |
|------|------|
| OCR 识别 | 扫描版 PDF → 可搜索 PDF（AI 引擎，支持中英文） |
| 转 WORD | PDF → 可编辑 DOCX |
| 去水印 | 自动检测并去除水印 |

## 性能参考

| 环境 | 11页 PDF |
|------|---------|
| CPU (i7) | ~3-4 分钟 |
| GPU (RTX 4060) | ~30 秒（需装 onnxruntime-gpu） |

## GPU 加速（可选）

```bash
# 卸载 CPU 版
pip uninstall onnxruntime

# 安装 GPU 版（需要 CUDA 11.x 或 12.x）
pip install onnxruntime-gpu
```

## 注意事项

- Python 版本必须 ≤ 3.12，PaddleOCR 模型不支持 3.13+
- 首次处理较慢（加载模型），后续会快很多
- 去水印和转 WORD 功能需要额外依赖 `opencv-python` 和 `pdf2docx`
