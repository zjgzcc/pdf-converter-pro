# GitHub 协同开发指南 🦎

## 快速开始

### 1. 创建 GitHub 仓库

```bash
# 在 GitHub.com 创建新仓库
# 仓库名：pdf-converter-pro
# 可见性：Private（推荐）或 Public
```

### 2. 初始化本地仓库

```bash
cd C:\Users\chche\.openclaw\workspace\pdf-converter-pro

# 初始化（已完成）
git init

# 添加远程仓库（替换为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/pdf-converter-pro.git

# 或者使用 SSH（推荐）
git remote add origin git@github.com:YOUR_USERNAME/pdf-converter-pro.git
```

### 3. 首次推送

```bash
# 添加所有文件
git add .

# 提交
git commit -m "🦎 Initial commit - PDF Converter Pro MVP

- 核心模块：OCR、去水印、WORD 转换
- GUI 界面（PyQt6）
- 批量处理支持
- 团队协作框架"

# 推送
git branch -M main
git push -u origin main
```

### 4. 邀请团队成员

1. 进入 GitHub 仓库页面
2. Settings → Collaborators
3. 添加团队成员邮箱或用户名
4. 分配权限（推荐：Write）

### 5. 分支开发流程

```bash
# 创建功能分支
git checkout -b feature/watermark-ai

# 开发...

# 提交
git add .
git commit -m "feat: 添加 IOPaint 水印去除支持"

# 推送分支
git push origin feature/watermark-ai
```

### 6. 创建 Pull Request

1. 在 GitHub 仓库页面点击 "Pull requests"
2. 点击 "New pull request"
3. 选择分支：`feature/watermark-ai` → `main`
4. 填写 PR 描述
5. 指定 Reviewer（@紫影）
6. 创建 PR

### 7. 代码评审清单（紫影专用）

- [ ] 代码符合项目规范
- [ ] 有适当的错误处理
- [ ] 有单元测试覆盖
- [ ] 文档已更新
- [ ] 无敏感信息泄露

### 8. 同步上游代码

```bash
# 切换到主分支
git checkout main

# 拉取最新代码
git pull origin main

# 同步到功能分支
git checkout feature/your-branch
git merge main
```

## 提交信息规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

## 项目目录结构

```
pdf-converter-pro/
├── .git/
├── .gitignore
├── README.md
├── TASKS.md
├── requirements.txt
├── main.py
├── core/
│   ├── __init__.py
│   ├── watermark.py
│   ├── ocr.py
│   └── converter.py
├── ui/
│   ├── __init__.py
│   └── main_window.py
├── tests/
├── docs/
└── scripts/
```

---

_影诺办 · PDF Converter Pro 项目组_
