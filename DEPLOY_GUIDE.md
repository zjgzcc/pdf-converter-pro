# PDF Converter Pro - 部署手册

## 📋 目录
1. [首次安装](#首次安装)
2. [日常使用](#日常使用)
3. [故障排除](#故障排除)
4. [持久化配置](#持久化配置)

---

## 首次安装

### 1. 解压项目
将项目解压到固定位置，例如：
```
D:\PDF-AI\pdf-converter-pro\
```

**⚠️ 重要：解压后不要移动文件夹位置，否则快捷方式会失效**

### 2. 运行安装脚本
双击运行 `install.bat`

安装过程：
- 检查 Python 3.11
- 创建虚拟环境 `.venv311`
- 安装 GPU 依赖（约 1GB，需要 5-10 分钟）
- 验证 GPU 可用性

### 3. 启动服务
双击运行 `start_service.bat`

服务启动后，浏览器访问：http://localhost:5000

### 4. 设置开机自启（可选）
双击运行 `setup_autostart.bat`

下次开机时服务将自动启动。

---

## 日常使用

### 启动服务
```
双击 start_service.bat
```

### 停止服务
```
在命令窗口按 Ctrl+C
```

### 访问服务
```
http://localhost:5000
```

---

## 故障排除

### 问题1: 显示"已有任务在处理中"

**原因：** 上次任务异常退出，状态未重置

**解决：**
1. 刷新页面（F5）
2. 如果无效，重启服务：
   - 按 Ctrl+C 停止
   - 重新运行 `start_service.bat`

### 问题2: GPU 未启用（显示 CPU）

**原因：** CUDA 运行时库缺失

**解决：**
```bash
# 重新安装 GPU 依赖
.venv311\Scripts\pip.exe install -r requirements-gpu.txt
```

### 问题3: 服务无法启动

**检查清单：**
1. Python 3.11 是否安装
2. 虚拟环境 `.venv311` 是否存在
3. 端口 5000 是否被占用

**查看端口占用：**
```bash
netstat -ano | findstr 5000
```

---

## 持久化配置

### 依赖持久化
所有依赖版本已固定在 `requirements-gpu.txt` 中，包括：
- CUDA 运行时库（nvidia-*-cu12）
- OCR 引擎（rapidocr, paddleocr）
- Web 框架（flask）

### 虚拟环境持久化
虚拟环境 `.venv311/` 包含：
- Python 解释器
- 所有安装的包
- CUDA 动态链接库

**⚠️ 不要删除此目录**

### 数据持久化
临时文件位置：`%TEMP%\pdf_converter_pro\`
- 上传的文件
- 处理后的输出

每次启动服务时会自动清理。

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `install.bat` | 首次安装脚本 |
| `start_service.bat` | 启动服务脚本 |
| `setup_autostart.bat` | 设置开机自启 |
| `requirements-gpu.txt` | GPU 版本依赖清单 |
| `web_server.py` | Web 服务主程序 |
| `web_ui.html` | Web 界面 |
| `core/` | 核心处理模块 |

---

## 更新日志

- **2026-03-28** - 添加依赖锁定、开机自启、状态重置机制
- **2026-03-27** - V1 生产版本发布

---

**维护人：** 陈龙一
**最后更新：** 2026-03-28
