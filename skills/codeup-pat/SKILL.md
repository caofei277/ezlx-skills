---
name: codeup-pat
description: 使用云效 Codeup 个人访问令牌（pt- 开头）调用 Codeup OpenAPI 与 git 操作：验证令牌、列出企业空间/代码组/仓库、创建代码组与代码库、克隆与推送。当用户提供 Codeup 令牌要求创建/查询仓库分组，或需要操作 codeup.aliyun.com 上的仓库时使用。含实测踩坑结论：正确的 API 网关域名、认证请求头，以及 302 跳登录 / MissingAccessKeyId / InvalidAction.NotFound 等报错的原因与出路。
metadata:
  display_name: Codeup 个人访问令牌调用指南
  version: "1"
  compatibility:
    - aliyun
    - codeup
    - yunxiao
    - git
---

# Codeup 个人访问令牌（PAT）调用指南

用户提供 Codeup 个人访问令牌（形如 `pt-xxxx_xxxx`）后，按本指南完成 API 调用与 git 操作。

## 安全铁律（先读）

1. **令牌绝不写入任何仓库文件、文档、issue、commit message**——文档与命令示例一律用 `$CODEUP_TOKEN` 或 `<TOKEN>` 占位。
2. 命令行传递令牌优先用环境变量；一次性 git URL 内嵌凭据仅限当场使用，**不得**把带令牌的 remote URL 持久化进 `.git/config`。
3. git 长期凭据放 `~/.netrc`（`chmod 600`），见下文「Git 通道」。
4. 令牌泄露（误提交/误贴出）→ 提醒用户立即到云效「个人设置 → 个人访问令牌」吊销重签。

## 两条通道（实测结论，勿走弯路）

| 通道 | 域名 | 认证方式 |
| --- | --- | --- |
| OpenAPI | `https://openapi-rdc.aliyuncs.com` | 请求头 `x-yunxiao-token: <TOKEN>` |
| Git | `https://codeup.aliyun.com` | `oauth2:<TOKEN>` 作为密码（Basic），或 `~/.netrc` |

**已实测走不通的路（不要再试）**：

- ❌ `codeup.aliyun.com/api/v4/...` + `PRIVATE-TOKEN` 头 → 302 跳登录页（GitLab 兼容 API 不收 PAT，Bearer/Basic 也不行）；
- ❌ `devops.cn-hangzhou.aliyuncs.com`（AK 签名网关）→ `MissingAccessKeyId`，PAT 无论放 query `accessToken`、`PRIVATE-TOKEN` 头还是 `x-yunxiao-token` 头都不认；旧版文档里的 `accessToken` query 参数只在该网关的 AK 流程下有效；
- ❌ `devops.aliyun.com`（云效控制台域）→ 302 跳 Web 登录，仅供浏览器会话；
- ✅ 唯一可用的 PAT 网关是 `openapi-rdc.aliyuncs.com`，路径前缀 `/oapi/v1/`。

## 本企业固定参考值（非机密，出现在仓库 URL 中）

```
organizationId = 681eb03aa06d934b014058f4
代码组/仓库 URL = https://codeup.aliyun.com/681eb03aa06d934b014058f4/<group>/<repo>.git
```

组织根的 namespace id（顶级代码组的 parentId）**不要硬编码**，用 namespaces 接口现查（见下）。

## 已验证接口清单

### 1. 验证令牌（whoami）

```bash
curl -s -H "x-yunxiao-token: $CODEUP_TOKEN" \
  "https://openapi-rdc.aliyuncs.com/oapi/v1/platform/user"
# → {"id":"...","name":"...","lastOrganization":"<organizationId>"}
```

### 2. 列命名空间（找组织根 id / 现有代码组）

```bash
curl -s -H "x-yunxiao-token: $CODEUP_TOKEN" \
  "https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/$ORG/namespaces?page=1&perPage=100"
```

返回字段：`id`、`parentId`、`pathWithNamespace`、`visibility`。**顶级代码组的 parentId 即组织根 namespace id**；新建顶级组时该 parentId 也可不传（默认建到组织根）。

### 3. 创建代码组

```bash
curl -s -X POST -H "Content-Type: application/json" -H "x-yunxiao-token: $CODEUP_TOKEN" \
  "https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/$ORG/groups" \
  -d '{
    "name": "显示名（可中文）",
    "path": "url-path",
    "visibility": "private",
    "description": "描述",
    "parentId": 0
  }'
# parentId 传组织根 id 或省略 → 顶级组；传某组 id → 子组
# visibility: private（私有）| internal（组织内公开）；返回顶层即含 id / pathWithNamespace / webUrl
```

### 4. 创建代码库

```bash
curl -s -X POST -H "Content-Type: application/json" -H "x-yunxiao-token: $CODEUP_TOKEN" \
  "https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/$ORG/repositories" \
  -d '{
    "name": "repo-name",
    "path": "repo-name",
    "namespaceId": 2088218,
    "visibility": "private",
    "description": "描述（建议写明派生来源与职责边界）",
    "readMeType": "EMPTY"
  }'
```

字段名注意：是 `visibility`（不是 `visibilityLevel`）、`readMeType`（EMPTY/USER_GUIDE）。

### 5. 列代码库

```bash
curl -s -H "x-yunxiao-token: $CODEUP_TOKEN" \
  "https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/$ORG/repositories?page=1&perPage=100&search=关键字"
```

## Git 通道

```bash
# 一次性操作：URL 内嵌凭据（用完即弃，不要写入 config）
git ls-remote "https://oauth2:$CODEUP_TOKEN@codeup.aliyun.com/$ORG/<group>/<repo>.git" HEAD

# 长期凭据：~/.netrc（权限 600）
# machine codeup.aliyun.com
# login oauth2
# password <TOKEN>
git ls-remote "https://codeup.aliyun.com/$ORG/<group>/<repo>.git" HEAD   # 自动走 netrc
```

约定：默认分支 `master`；clone 用 `https://codeup.aliyun.com/$ORG/<group>/<repo>.git`（netrc 已配置时免密）。

## 典型任务：建组 + 建仓 + 本地首推（完整流程）

```bash
ORG="681eb03aa06d934b014058f4"
BASE="https://openapi-rdc.aliyuncs.com"
AUTH=(-H "Content-Type: application/json" -H "x-yunxiao-token: $CODEUP_TOKEN")

# 1) 验令牌
curl -s "${AUTH[@]}" "$BASE/oapi/v1/platform/user"

# 2) 查组织根 namespace id（取顶级组的 parentId）
curl -s "${AUTH[@]}" "$BASE/oapi/v1/codeup/organizations/$ORG/namespaces?page=1&perPage=100"

# 3) 建顶级组 → 记下返回的 id
GROUP_ID=$(curl -s -X POST "${AUTH[@]}" "$BASE/oapi/v1/codeup/organizations/$ORG/groups" \
  -d '{"name":"项目名","path":"proj","visibility":"private","description":"..."}' | jq -r .id)

# 4) 建仓库（namespaceId=组 id）
curl -s -X POST "${AUTH[@]}" "$BASE/oapi/v1/codeup/organizations/$ORG/repositories" \
  -d "{\"name\":\"proj-api\",\"path\":\"proj-api\",\"namespaceId\":$GROUP_ID,\"visibility\":\"private\",\"description\":\"...\",\"readMeType\":\"EMPTY\"}"

# 5) 本地仓 → 首推
mkdir -p proj/proj-api && cd proj/proj-api
git init -q -b master
cp /path/to/README.md .
git add README.md && git commit -q -m "chore: 初始化仓库"
git remote add origin "https://codeup.aliyun.com/$ORG/proj/proj-api.git"
git push -qf -u origin master     # 注意 -f，见下方坑 2
```

## 踩坑记录（照做可省半小时排错）

1. **建仓后远端 master 已有自动生成的 "Initial commit"（模板 README）**——即使 `readMeType: EMPTY` 实测也会生成。本地首推直接 `git push -f -u origin master` 覆盖（仅限刚建的空仓），或先 `git pull --rebase --allow-unrelated-histories`。
2. **报 302 跳 `account.aliyun.com/login`** = 认证没被识别，检查是否用对了网关（openapi-rdc）和头（x-yunxiao-token），而不是在原域上换认证头重试。
3. **报 `MissingAccessKeyId`** = 你正在打 AK 签名网关（devops.cn-hangzhou.aliyuncs.com），PAT 在这个网关永远不通，换 openapi-rdc。
4. **报 `InvalidAction.NotFound`** = 域名对了但路径不对；PAT 风格路径前缀是 `/oapi/v1/...`，不是旧文档的 `/repository/create` 那套相对路径（那是 AK 网关的）。
5. **openapi-rdc 上未知路径会 302 到 help 文档页**，不是 404——看到 302 先看 Location 是不是 help.aliyun.com。
6. 分页接口的页大小参数名不统一：namespaces 用 `perPage`，部分旧接口用 `pageSize`。

## 适用边界

- 本指南覆盖：令牌验证、空间/组/库的查询与创建、git 读写。
- 未覆盖：合并请求、成员权限、WebHook、保护分支等管理类接口——同网关同认证头，按 `/oapi/v1/codeup/organizations/$ORG/...` 风格查官方文档「云效 OpenAPI → 代码管理」扩展即可。
