# PDF Converter Pro - 便携版使用说明
⚡ 雷影【执行】开箱即用版本

## 📦 打包说明

本便携版由 `scripts/build_exe.py` 自动生成，包含：

- **PDF Converter Pro.exe**: 主程序（PyInstaller 打包的单文件 EXE）
- **README.txt**: 简要使用说明
- **启动程序.bat**: 一键启动批处理

## 🚀 部署到另一台电脑

### 步骤 1: 打包
在项目目录运行：
```bash
python scripts/build_exe.py
```

等待打包完成，生成 `pdf-converter-pro-portable/` 目录。

### 步骤 2: 复制
将整个 `pdf-converter-pro-portable/` 目录复制到目标电脑。

### 步骤 3: 运行
在目标电脑上：
- 双击 `启动程序.bat` 或
- 双击 `PDF Converter Pro.exe`

## ⚙️ 系统要求

### 最低要求
- Windows 7/8/10/11 (64 位)
- 2GB 可用内存
- 500MB 可用磁盘空间

### 推荐配置
- Windows 10/11 (64 位)
- 4GB 可用内存
- 1GB 可用磁盘空间

## 📋 功能说明

✅ **PDF 转 Word** - 高质量转换为 DOCX 格式  
✅ **OCR 识别** - 支持中英文文字识别  
✅ **批量处理** - 支持整个目录批量转换  
✅ **图形界面** - 直观易用的操作界面  

## 🔧 高级用法

### 命令行参数
```cmd
PDF Converter Pro.exe --help
```

### 示例
```cmd
:: 单个文件转换
PDF Converter Pro.exe input.pdf -o output_dir

:: 批量处理目录
PDF Converter Pro.exe input_folder -o output_folder

:: 仅 OCR（不转 Word）
PDF Converter Pro.exe scan.pdf -o output --ocr --no-word

:: 仅转 Word（不 OCR）
PDF Converter Pro.exe document.pdf -o output --no-ocr --word
```

## ⚠️ 注意事项

1. **首次运行**: 可能需要几秒初始化时间
2. **权限**: 确保输出目录有写入权限
3. **大文件**: 处理大文件时请耐心等待
4. **杀毒软件**: 如被拦截，请添加信任或临时关闭

## 🆘 故障排除

### 程序无法启动
- 以管理员身份运行
- 检查 Windows 事件查看器
- 确保 .NET Framework 已安装

### 转换失败
- 验证 PDF 文件完整性
- 检查磁盘空间
- 查看控制台错误信息

### OCR 不准确
- 确保扫描质量清晰
- 调整图片对比度
- 使用标准字体文档

## 📞 技术支持

如遇问题，请提供：
1. 操作系统版本
2. 错误信息截图
3. 问题文件样本（如可分享）

---
**版本**: MVP 0.1.0  
**团队**: 影诺办  
**执行**: ⚡ 雷影【执行】  
**日期**: 2026-03-19

---
快速部署 | 高效执行 | MVP 验证
