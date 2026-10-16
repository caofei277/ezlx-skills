---
name: icon-freedom
description: "图标自由：任意项目的图标治理全链路——多源检索(Remix/Tabler/iconfont.cn)、五维风格量化初筛、agent 视觉复审、用户圈选、SVG 规范化、本地字体构建(woff2/ttf+css)、替换页面散装 PNG 位图。当用户提到图标、icon、iconfont、图标库、换图标、加图标、图标不清晰/不专业/风格不统一、OSS PNG 图标矢量字体化、uni-app/Web 多端图标方案时使用。"
---

# icon-freedom — 项目图标自由全链路

给任何项目装上一条「检索 → 初筛 → 复审 → 圈选 → 规范化 → 构建 → 替换」的图标管线。
设计哲学（与用户沟通过定稿）：

1. **三层漏斗解决覆盖度**：主干库（Remix/Tabler 等成体系开源库）保证风格统一命中率 ~90%；
   iconfont.cn 全站检索（数百万）补通用缺口；行业特有概念走定制 SVG 自传源目录。
2. **风格判断不是玄学**：五维可量化（线性/面性、笔画比、圆角、栅格留白、墨水密度），
   机器初筛硬指标 → agent 视觉复审软判断 → 用户只做圈选。
3. **按需 = 构建期子集**：字体只含入库图标（几十 KB），本地打包进项目，运行时零流量。
4. **人只出现在圈选和发布**：其余全自动；圈选不可跳过（除非用户明示"你自己定"，此时须把决策记入 `.icons/decisions.md`）。

## Phase A — 盘点（每次接手新项目先做）

1. 识别技术栈：uni-app（`manifest.json`/`pages.json`）/ Vue·React Web / 小程序原生 / 其他。
2. 摸清图标现状三类：
   - 已有字体管线（`static/**/iconfont.css`、`@font-face`）
   - 组件库图标（uv-icon、uni-icons、element-plus icons…）
   - 散装位图（`<image src="https://…oss…png">`、`<img src="*.png">`）
3. 产出盘点清单（文件、数量、来源）+ 接入点建议（css 放哪、class 前缀防与组件库冲突）。
4. 找规格文件 `<仓库根>/.icons/spec.json`：没有 → 走 Phase B；有 → 直接进 Phase C
   （顺手看 `.icons/showcase.html` / `manifest.json`，有则项目已接入管线，存量一目了然）。

## Phase B — 定标（一次性；新项目或用户要求改风格时）

1. 问用户两件事：线性还是面性（或分场景）；参照哪套主干库。没偏好时默认推荐：
   **线性 / 24 栅格 / 笔画 2px（比 8.3%）/ round 圆角 / 单色 currentColor**（Remix line 风格），并说明理由。
2. 复制 `references/spec.template.json` → `.icons/spec.json`，改 `build.*` 为项目真实路径
   （uni-app 惯例 `src/static/icons-src` → `src/static/font/iconfont`）。
3. 从主干库挑 3~5 个代表图标做**参照集**，放 `build.reference_dir`（`_` 前缀目录不参与构建）。
   参照集是后续一切"风格像不像"的标尺。
4. 提交 spec + 参照集，向用户确认定标结果。

## Phase C — 增量供应循环（日常主流程；目标单图标 ≤15 分钟端到端）

触发：用户要图标（"加个退款图标""把我的页 PNG 换掉"）。**快速通道 5 步，中间步骤一律不手工跑：**

1. **需求清单化**：kebab-case 语义名（`refund`）+ 中文别名（showcase 检索用）；查 showcase/codepoints 查重。
2. **检索**：`fetch_icons.py --lib remix --names "refund-line,..." -o /tmp/cands`。
   首选 **Remix line**（fill 技术的轮廓形，免描摹直通）；Tabler/lucide 为 stroke 稿须描摹（管线自动处理，但多一步）。
   候选拉 4~6 个足够。**禁裸试 unpkg、禁 data API flat listing**（实测挂/超时）——只用 fetch_icons.py 的直链路由。
   主干库知名图标可跳过独立机器初筛（fetch 直链即合规），iconfont.cn 社区 MCP 或 WebSearch 自取的稿子才过 `icon_analyze.py`。
3. **圈选**：对比页（Gen UI HTML / render_sheet）一次生成呈报，agent 复审意见（推荐序+一句话淘汰理由）直接写在页上。**圈选不可省。**
4. **一键入库**：`icon_add.py <spec> <name> <候选.svg> --alias 中文 --source 出处`——
   自动检测 stroke/fill 并路由（stroke → trace.mjs 描摹 + fixorient.py 绕向修正）、构建、fontTools 三件套验证
   （contours>0 / bbox 嵌套同向绕向检测 / 码点入 cmap，任一失败即非 0 退出并给排查指引）、manifest.json 更新、showcase.html 再生成。
5. **替换页面引用**：`<image src="…oss….png">` → `<text class="{prefix}-{name}"></text>`，
   尺寸对齐原布局，颜色走 currentColor/主题变量（注意压过页面既有 text 选择器）。
   然后**一次性**项目构建 + 提交（字体产物 + 源 SVG + manifest + showcase + 页面改动**同笔 commit**）。

**速度军规**（实战教训固化，违者必绕远）：
- 入库后视觉验证 = showcase 截图（真浏览器）；**免全量项目构建**。项目构建只为出交付产物，入库验证通过后只跑一次。
- webfont 验证一律真浏览器：playwright 无浏览器时用 `p.chromium.launch(channel='chrome')` 直连系统 Chrome，
  **勿跑 `playwright install`**（百 MB 下载）。qlmanage 只验 SVG 不验 webfont，别用它走完验证。
- 描摹稿绕向问题、stroke 不被字体管线支持、参照集递归污染——三条已由 icon_add.py 自动规避，不要再人工排查一遍。
- 圈选等用户回复期间不空转：可先把 spec/manifest/showcase 骨架备好。

## 硬规则（禁令）

- **线性↔面性不可互转**：指**视觉风格**（轮廓形 vs 实心剪影），不是涂料技术。fill 技术的带孔洞轮廓形（Remix line 系）属视觉线性，`visualstyle.classify_fill` 渲染查孔自动放行；实心剪影才拒收。唯一救法是换图标或定制重画。
- **彩色图标不走字体管线**：明确告知用户改走位图/单独 SVG；字体只管单色功能图标。
- **圈选环节不可省**（用户授权除外）；每次圈选结论追加记录 `.icons/decisions.md`（日期、需求、选中、淘汰理由）。
- **不把在线 css 外链当方案**：小程序不认外链 css；默认本地打包字体。仅当项目确认只发 H5 且用户点名，才允许在线链接。
- **不写入用户 iconfont.cn 账号项目**：iconfont 无官方 API，写接口全属逆向，仅在用户明确要求时用社区工具，失败即止不硬怼。
- **字体产物与源 SVG 同笔 commit**；码点表（codepoints.json）绝不手工改。
- **css class 一律带项目前缀**（如 `icon-`），防与组件库图标冲突；接入样式管线（App.vue @import 等）是交付的一部分。
- **stroke 型源稿必须先转填充轮廓**（2026-10-16 荣格实证）：fantasticon→svgicons2svgfont **不吃 stroke**——要么 E_CONVERT_ERROR，要么静默产空字形（ttf 仅 ~2KB 是危险信号）。管线：`trace.mjs`（sharp 高分辨率栅格 + potrace 描摹，忠实保留圈选造型）→ `fixorient.py`（potrace 按 evenodd 输出全子路径同向，非 zero 语义下孔洞被填成实心块；按 shapely 嵌套深度令外环/孔洞反向，两方向变体浏览器实证均可穿孔，准入外环 shoelace 正）。参照集目录**勿放 src_dir 内**（fantasticon 递归扫描，`_` 前缀目录也会被打进字体）。
- **字体级验证三件套**（icon_add.py 已自动化，缺一不可）：① fontTools 查 `numberOfContours` >0；② 绕向 = **bbox 嵌套且同向才判罚**（nonzero 语义：嵌套同向会填死孔洞成实心块；独立兄弟轮廓同向合法，如双箭头——"符号必须混合"是过时口径，会误报）；③ 真浏览器渲染截图（qlmanage 只验 SVG 不验字体）。
- **视觉风格双判据**（visualstyle.classify_fill，rsvg-convert 渲染）：① 内孔（轮廓形强信号）② 墨水占比 <25%（✕/箭头/循环等**无内孔细线字形**靠此放行，孔洞判据单独会误判面性）。

## 脚本速查（scripts/）

```bash
# 主干库候选下载（remix=fill稿首选免描摹 / tabler、lucide=stroke稿自动走描摹）
python3 fetch_icons.py --lib remix --names "newspaper-line,article-line" -o /tmp/cands

# 五维分析（自取稿/存疑稿筛查；fetch 直链的主干库知名图标可跳过）
python3 icon_analyze.py .icons/spec.json a.svg b.svg > /tmp/report.json

# 对比页（人圈选）+ PNG 网格（agent 复审；PNG 需 cairosvg+PIL，缺则只有 html）
python3 render_sheet.py -o /tmp/sheet --refs 参照1.svg 参照2.svg --cands c1.svg c2.svg --report /tmp/report.json

# ★ 一键入库（日常主入口）：stroke/fill 自动路由 + 描摹 + 绕向修正 + 构建 + fontTools 三件套验证 + manifest + showcase
python3 icon_add.py .icons/spec.json refund /tmp/cands/refund-line.svg --alias 退款 --source remix/refund-line@4.9.1 [--force]

# 项目图标 H5 展示页再生成（单文件自包含，file:// 双击即开；icon_add.py 会自动调，手工改 manifest 后手动跑）
python3 build_showcase.py .icons/spec.json

# 单步工具（icon_add.py 已编排，仅排障时用）
python3 icon_normalize.py .icons/spec.json -o src/static/icons-src/refund.svg /tmp/candidate.svg
node trace.mjs <in.svg> <traced.svg> [960]
python3 fixorient.py <traced.svg> <variantA.svg> <variantB.svg>
node build_font.mjs --spec .icons/spec.json [--base64]
```

## 项目图标 H5 展示页（showcase）

每项目一份 `<spec目录>/showcase.html`：单文件自包含（woff2 base64 内嵌，file:// 双击即开，零外部请求）。
全量图标预览（40px + 实际 20px 双尺寸）、关键字检索（名称/中文别名/码点）、排序（**加入时间 新→旧 默认** | 名称）、
点卡片复制类名。数据源 = `codepoints.json` + `<spec目录>/manifest.json`（icon_add.py 自动维护：
name/alias/source/added_at/codepoint），随每次入库自动再生成——找图标先开它，别翻源码目录。

## 脚本速查（scripts/）

```bash
# 五维分析（多文件，输出 JSON 报告）
python3 icon_analyze.py .icons/spec.json a.svg b.svg > /tmp/report.json

# 规范化（REJECT 项会被拒绝并 exit 2）
python3 icon_normalize.py .icons/spec.json -o src/static/icons-src/refund.svg /tmp/candidate.svg

# 对比页（人圈选）+ PNG 网格（agent 复审；PNG 需 cairosvg+PIL，缺则只有 html）
python3 render_sheet.py -o /tmp/sheet --refs 参照1.svg 参照2.svg --cands c1.svg c2.svg --report /tmp/report.json

# 构建字体（首跑自动装 fantasticon 进技能目录；ICON_FREEDOM_NODE_DEPS 可覆盖依赖位置）
node build_font.mjs --spec .icons/spec.json [--base64]
```

## 多端要点（集成产物=图标字体，SVG 只是源稿）

字体是跨端兼容性最好的图标载体（这正是选字体而非直接嵌 SVG 的原因——SVG 各端支持参差）：

| 平台 | 兼容性 | 说明 |
|---|---|---|
| H5 | ✅ 已实测 | woff2 现代全支持，ttf 兜底老 webview；<4KB 自动被 vite 内联 base64 零请求 |
| APP（uni-app vue 页/webview 壳） | ✅ 同 H5 | nvue（原生渲染）页不适用，需 uni.loadFontFace——项目含 nvue 页时逐页确认 |
| 微信/各类小程序 | ✅ 有前提 | ①禁在线 css 外链→本地打包（默认即是）；②WXSS 对属性选择器无官方承诺→产物已自动追加显式基类，模板写 `class="{prefix}-font {prefix}-图标名"`；③`--base64` 内嵌免字体请求；④注意小程序包体积额度 |
| RN / Flutter / 原生 | ✅ 字体文件直接复用 | 同一个 ttf：RN `fontFamily`、Flutter `TextStyle(fontFamily)`、鸿蒙 Font 注册，字形码点表通用 |
| 后台 Web / 桌面 | ✅ | 同一份 css+字体直接引 |

- 产物 css 基类选择器为**标签无关**（`[class^="{prefix}-"]`），`<text>`/`<i>`/`<span>`/`<view>` 全适配；小程序端加写显式基类 `{prefix}-font`。
- 墨水密度等渲染类指标：优先用 visualstyle 的 rsvg-convert 路线（本机已具备）；cairosvg+PIL 可选装，缺了不阻塞流程。

## 图标库来源（三层漏斗，已全部贯通）

1. **主干库**（fetch_icons.py，日常够用）：remix（fill 轮廓形免描摹，同风格首选）/ tabler / lucide（stroke 自动描摹）。
2. **聚合源 iconify**（"大而全"通道）：一个接口 = **243 个图标集 / 20 万+ 图标**（fluent/material-symbols/ph/mdi/bootstrap/heroicons…），且支持**跨库语义搜索**：
   `fetch_icons.py --lib iconify --search "customer group"` → 挑名 → `--names "集合:图标名"` 取稿（stroke/fill 混杂，icon_add 自动路由；搜索仅英文关键词，中文先译英）。
3. **自定义 SVG**（行业特有概念）：icon_add.py 直接吃任意本地 SVG 文件，与库稿同一管线。
   iconfont.cn 社区 MCP（中文检索数百万稿）为规划中的第四路，环境配了 MCP 再接。

详细标准与容差见 `references/style-rules.md`；规格模板见 `references/spec.template.json`。
