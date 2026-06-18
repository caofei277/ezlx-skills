---
name: difit
description: 使用 difit CLI 以 GitHub 风格 WebUI 查看和审查本地 git 差异，支持提交审查、分支对比、PR 审查和评论注入，评论可作为 AI 提示复制使用。
metadata:
  display_name: difit 差异审查工具
  version: "1"
  compatibility:
    - filesystem
    - nodejs
    - npm
---

# difit 差异审查工具

## 何时使用

- AI 代理完成代码修改后，需要让用户审查 diff 并给出反馈
- 用户想查看最近提交的差异，以 GitHub 风格 WebUI 审查代码变更
- 需要对比两个分支/提交之间的差异
- 需要审查 GitHub PR（配合 `gh` CLI）
- 代理需要预注入审查评论，引导用户关注特定行
- 用户想审查暂存区（staged）或工作目录（working）的变更
- 需要将审查评论以结构化格式复制为 AI 提示，用于后续编码

## 不适用

- 非 git 仓库环境
- Node.js < 21.0.0
- 纯文本 diff 查看（无 WebUI 需求）——直接用 `git diff`
- GitHub PR 审查但未安装/认证 `gh` CLI

## 前置条件

- Node.js ≥ 21.0.0
- 当前目录在 git 仓库中（`git rev-parse --git-dir` 成功）
- GitHub PR 模式需安装并认证 GitHub CLI：`gh auth status`

检查命令：

```bash
node --version
git rev-parse --git-dir
```

## 输入

- 当前 git 仓库的提交/分支状态
- 用户希望审查的目标（最新提交、指定提交、分支对比、工作目录、PR）
- 代理可选的审查评论（通过 `--comment` 参数注入）

## 输出

- difit WebUI 在浏览器中打开，显示差异对比
- 用户可在 WebUI 中对 diff 行添加评论
- 评论可通过"复制提示"按钮以结构化格式复制为 AI 提示
- `--background` 模式下输出 JSON 连接信息，便于脚本处理

## 约束

- **安装检查**：执行命令前先检查 `difit` 是否已安装，未安装则 `npm install -g difit`
- **Git 仓库**：必须在 git 仓库中执行，非 git 目录提前报错
- **端口冲突**：默认 4966 端口被占用会自动 +1，无需手动指定
- **浏览器自动打开**：默认会自动打开浏览器，CI/脚本环境用 `--no-open`
- **服务器生命周期**：默认浏览器断开后服务器自动停止，需保持时用 `--keep-alive`
- **幂等**：重复执行同一条命令不受影响，评论按 commit 保存在 localStorage

## 主流程

### 步骤 0：前置检查

```bash
node --version
```

确保 Node.js ≥ 21。检查 difit 是否已安装：

```bash
difit --version 2>/dev/null || echo "not installed"
```

未安装时执行：

```bash
npm install -g difit
```

**判据**：Node.js 版本满足要求，difit 命令可用。

### 步骤 1：确定审查目标

与用户确认要审查的内容，或根据场景自动选择：

| 场景 | 命令 |
|------|------|
| 最新提交（HEAD） | `difit` |
| 所有未提交的更改 | `difit .` |
| 仅暂存区更改 | `difit staged` |
| 仅未暂存的更改 | `difit working` |
| 指定提交 | `difit <commit-hash>` |
| 两个提交对比 | `difit <commit> <compare-with>` |
| 分支与 main 对比 | `difit feature main` |
| 工作目录与远程对比 | `difit . origin/main` |
| GitHub PR 审查 | `difit --pr <pr-url>` |
| 标准输入 diff | `git diff --cached \| difit` |

**判据**：已与用户确认审查目标，或根据上下文自动选择。

### 步骤 2：启动 difit（代理注入评论）

代理在启动 difit 时可预注入审查评论，引导用户关注特定行。

```bash
difit --comment '{"type":"thread","filePath":"src/example.ts","position":{"side":"new","line":10},"body":"这里建议用更描述性的变量名"}' --no-open
```

`--comment` 可重复使用，也接受 JSON 数组批量注入：

```bash
difit --comment '[
  {"type":"thread","filePath":"src/api.ts","position":{"side":"new","line":42},"body":"缺少错误处理"},
  {"type":"thread","filePath":"src/types.ts","position":{"side":"new","line":15},"body":"考虑用 interface 替代 type"}
]'
```

> **注意**：注入评论时建议加 `--no-open`，等准备好再让用户打开浏览器。

**判据**：difit 服务器已启动，评论已注入。

### 步骤 3：通知用户审查

告知用户 difit 已启动，提供访问信息：

```
difit WebUI 已启动，请访问 http://127.0.0.1:4966 审查变更
```

若使用 `--background` 模式，可从 JSON 输出中提取 URL。

**判据**：用户已收到访问地址。

### 步骤 4：等待用户反馈

difit 默认在浏览器断开后自动停止服务器。用户完成审查后：
1. 在 WebUI 中添加行内评论
2. 使用"复制提示"按钮复制单个评论
3. 使用"复制所有提示"以结构化格式复制所有评论
4. 将复制的提示粘贴回对话，代理即可按反馈修改代码

**判据**：用户反馈已通过 difit 评论系统收集。

## 代理使用示例

### 场景 1：修改代码后请求审查

```bash
# 代理完成修改后，通知用户审查最新提交
difit --no-open
```

```
我已完成了修改，difit 审查服务器已启动。
请访问 http://127.0.0.1:4966 查看变更。

如果有修改意见，可以在对应行添加评论，
然后使用"复制所有提示"将反馈粘贴回来。
```

### 场景 2：预注入审查评论

```bash
# 代理对自己生成的代码有疑虑，提前标注
difit --comment '{"type":"thread","filePath":"src/handler.ts","position":{"side":"new","line":88},"body":"这里的事务边界是否正确？请确认是否需要外层事务包裹"}' --no-open
```

### 场景 3：审查 GitHub PR

```bash
# 代理审查 Pull Request
difit --pr https://github.com/owner/repo/pull/123
```

> 依赖 `gh` CLI，需先 `gh auth login`。PR 中未解决的 inline review thread 会自动导入为启动评论。

### 场景 4：对比分支变更

```bash
# 审查 feature 分支相对于 main 的变更
difit feature main --merge-base
```

`--merge-base` 会先用 `git merge-base` 解析基准 revision，只显示 feature 分支独有的变更。

### 场景 5：将审查反馈转为 AI 提示

用户在 difit WebUI 中添加评论后，点击"复制所有提示"得到结构化输出：

```
src/components/Button.tsx:L42
使此变量名更具描述性

src/api.ts:L88-L92
此部分应提取为独立函数
```

代理收到后可直接按行号定位并修改。

## 决策表

| 用户需求 | 操作 |
|---------|------|
| 审查最新提交 | `difit` |
| 审查未提交更改 | `difit .` |
| 审查暂存区 | `difit staged` |
| 审查工作目录 | `difit working` |
| 审查指定提交 | `difit <hash>` |
| 对比两个分支 | `difit <branch> <base>` |
| 审查 GitHub PR | `difit --pr <url>` |
| 从管道读取 diff | `command \| difit` |
| 代理预注入评论 | `difit --comment '<json>'` |
| 不自动打开浏览器 | `difit --no-open` |
| 绑定到 0.0.0.0 | `difit --host 0.0.0.0` |
| 后台运行 | `difit --background` |
| 保持服务器运行 | `difit --keep-alive` |
| 启动时清空评论 | `difit --clean` |
| 限制上下文行数 | `difit --context 0` |
| 包含 untracked 文件 | `difit . --include-untracked` |

## 边界情况

- **difit 未安装**：自动执行 `npm install -g difit`
- **非 git 目录**：报错提示，引导用户进入 git 仓库
- **端口被占用**：difit 会自动尝试 +1 端口，无需手动处理
- **Node.js 版本过低**：引导用户升级到 ≥ 21.x
- **`--pr` 模式无 `gh` CLI**：报错提示安装 GitHub CLI 并 `gh auth login`
- **标准输入模式**：通过管道传入时自动识别；也可用 `-` 显式启用
- **包含 untracked 文件**：仅在 `.` 或 `working` 时有效，用 `--include-untracked` 开启
- **浏览器已关闭但服务器终止**：默认行为，需保持时加 `--keep-alive`
- **评论注入重复**：difit 会跳过已存在的相同评论，不会重复导入
- **Enterprise Server PR**：需先 `gh auth login --hostname YOUR-ENTERPRISE-SERVER`

## 参考

- difit GitHub 仓库：https://github.com/yoshiko-pg/difit
- difit npm 包：https://www.npmjs.com/package/difit
- difit Skills（代理集成）：`npx skills add yoshiko-pg/difit`
- GitHub CLI 文档：https://cli.github.com/manual/
