# 测试样本文件目录
# Test Sample Files Directory

本目录用于存放测试用的样本文件。

## 所需测试文件

### PDF 测试文件
- `sample_invoice.pdf` - 发票样本（用于 OCR 测试）
- `sample_contract.pdf` - 合同样本（用于转换测试）
- `sample_scan.pdf` - 扫描件样本（用于 OCR 测试）

### 图片测试文件
- `sample_watermark.png` - 带水印图片（用于去水印测试）
- `sample_clean.png` - 干净图片（对比测试）

## 创建测试文件

由于 PDF 和图片文件无法直接通过文本创建，请使用以下方式生成：

### 方法 1：使用 Python 脚本
```python
# 创建简单的 PDF 占位符
from reportlab.pdfgen import canvas

c = canvas.Canvas("sample_invoice.pdf")
c.drawString(100, 750, "Sample Invoice")
c.drawString(100, 730, "Item: Test Product")
c.drawString(100, 710, "Price: $100.00")
c.save()
```

### 方法 2：使用在线工具
- 从 https://www.pdf24.org/ 下载样本 PDF
- 从 https://www.samplepdf.com/ 获取测试文件

### 方法 3：使用现有文件
将项目中的实际 PDF 文件复制到此目录进行测试。

## 注意事项

1. 测试文件应小于 5MB
2. 避免使用包含敏感信息的真实文件
3. 建议使用脱敏的样本数据
