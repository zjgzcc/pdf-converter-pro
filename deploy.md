# PDF Converter Pro 部署指南

## 📦 项目结构

```
pdf-converter-pro/
├── web_server.py          # Web 服务后端
├── web_ui.html            # Web 界面
├── config.json            # 配置文件
├── requirements.txt       # Python 依赖
├── .gitignore             # Git 忽略文件
├── README.md              # 项目说明
└── core/                  # 核心模块
    ├── rapid_ocr.py       # RapidOCR 引擎
    ├── ocr_v2.py          # OCR 模块
    ├── converter.py       # PDF 转 WORD
    ├── watermark.py       # 去水印
    └── postprocess.py     # 后处理
```

## 🚀 快速部署

### 方式 1：一键部署（推荐）

双击运行：
```
D:\PDF-AI\deployauto\deploy.bat
```

### 方式 2：手动部署

```bash
# 1. 拉取最新代码
cd C:\Users\50306\.openclaw\workspace\pdf-converter-pro
git pull origin master

# 2. 安装依赖
.venv311\Scripts\python.exe -m pip install -r requirements.txt

# 3. 启动服务
.venv311\Scripts\python.exe web_server.py
```

## 🛠️ 工作流脚本

| 脚本 | 路径 | 功能 |
|------|------|------|
| 拉取最新 | `D:\PDF-AI\deployauto\pull-master.bat` | 拉取 master 分支最新代码 |
| 推送本地 | `D:\PDF-AI\deployauto\push-local.bat` | 推送本地更改到远程 |
| 一键部署 | `D:\PDF-AI\deployauto\deploy.bat` | 安装依赖 + 启动服务 |

## 🌐 访问服务

服务启动后，打开浏览器访问：
```
http://localhost:5000
```

## 📝 配置说明

编辑 `config.json` 自定义配置：
- OCR 引擎选择
- 输出格式
- 处理参数

## 🔧 故障排查

### 服务无法启动
1. 检查端口 5000 是否被占用
2. 检查虚拟环境是否正确创建
3. 检查依赖是否完整安装

### GPU 加速不生效
1. 检查 NVIDIA 驱动是否安装
2. 检查 CUDA 依赖是否完整
3. 查看日志确认 GPU 检测结果

## 📊 性能指标

| 模式 | 速度 | 适用场景 |
|------|------|----------|
| GPU | ~2 秒/页 | 大批量处理 |
| CPU | ~8 秒/页 | 小批量/无 GPU |

---

**版本：** V1  
**最后更新：** 2026-03-27
