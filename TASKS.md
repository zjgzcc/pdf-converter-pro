# 任务分配表 🦎

## 当前状态：开发中

| 成员 | 任务 | 文件 | 状态 |
|------|------|------|------|
| 🦎 龙一【主理】 | 项目初始化、总协调 | README.md, main.py | ✅ |
| 🔍 龙二【技术】 | OCR 模块、转换模块优化 | core/ocr.py, core/converter.py | ✅ |
| 📊 赤影【技术】 | OCR 核心功能开发 | core/ocr.py, scripts/batch_ocr.py | ✅ |
| 🧪 青影【测试】 | 单元测试、集成测试 | tests/test_*.py | ✅ |
| ⚙️ 紫影【研发】 | 代码评审、架构优化 | core/*.py | ✅ |
| 🎨 橙影【设计】 | UI 美化、图标设计 | ui/main_window.py, assets/ | 🔄 |
| 🌙 月影【情报】 | 技术资料搜集 | docs/references.md | 🔄 |
| 🔥 炎影【运营】 | 用户文档、发布计划 | docs/user_guide.md | 🔄 |
| 💎 金影【商业】 | 商业模式分析 | docs/business_plan.md | 🔄 |
| 🌿 绿影【增长】 | 推广策略 | docs/growth_strategy.md | 🔄 |
| ⚡ 雷影【执行】 | MVP 验证、快速迭代 | main.py | 🔄 |

## GitHub 仓库

**仓库地址:** https://github.com/zjgzcc/pdf-converter-pro

**当前分支:** master

---

## GitHub 协同流程

1. **克隆仓库**
   ```bash
   git clone https://github.com/zjgzcc/pdf-converter-pro.git
   cd pdf-converter-pro
   ```

2. **推送代码**
   ```bash
   git add .
   git commit -m "feat: your changes"
   git push origin master
   ```

3. **分支开发**
   ```bash
   git checkout -b feature/watermark-ai
   # 开发...
   git commit -m "feat: 添加 IOPaint 水印去除"
   git push origin feature/watermark-ai
   ```

4. **Pull Request**
   - 在 GitHub 创建 PR
   - 指定 reviewer（紫影【研发】）
   - 评审通过后合并

## 下一步行动

1. 安装依赖：`pip install -r requirements.txt`
2. 测试运行：`python main.py`
3. 创建 GitHub 仓库
4. 邀请团队成员

---

_最后更新：2026-03-19 16:59_
