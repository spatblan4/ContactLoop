# ContactLoop 首页品牌区视觉增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增强 ContactLoop 首页顶部品牌区与首屏上下层级，让 logo、导航、hero 和下方信息区形成更协调的视觉重量。

**Architecture:** 只修改 `src/styles.css` 中首页相关样式，保留 `src/app.js` 的 DOM 结构、文案和交互。使用现有 CSS 变量、字体和 coral / ink / muted 色彩，桌面端增强品牌感，移动端通过已有 620px media query 回落尺寸。

**Tech Stack:** Vite、原生 HTML 模板字符串、CSS、现有 Space Grotesk / DM Sans / DM Mono 字体。

## Global Constraints

- 只修改首页相关 CSS；不修改 dashboard、Supabase、数据逻辑和现有交互。
- 优先复用现有颜色变量、字体和组件样式。
- 不新增依赖，不替换现有 hero 图片。
- 桌面端增强顶部视觉重量，但 hero 标题仍保持第一视觉焦点。
- 620px 以下不出现顶部横向溢出，logo、hero 标题和 CTA 保持可读、可操作。

---

### Task 1: 调整首页桌面端品牌区和首屏比例

**Files:**
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/styles.css:81-83`

**Interfaces:**
- Consumes: 现有 `.home-nav`、`.home-brand`、`.home-nav-links`、`.hero`、`.home-proof`、`.privacy-strip` 样式。
- Produces: 首页桌面端增强后的品牌区样式，保持现有首页 HTML 结构不变。

- [ ] **Step 1: 更新首页桌面端尺寸和层级样式**

  在现有首页规则中完成以下最小调整：`.home-nav` 高度约 96px 并加入轻微底部阴影；`.home-brand` 使用约 23px 字号、`.brand-mark` 使用约 40px 尺寸和 12px 间距；导航链接使用 14px 字号、32px 间距并增加轻量胶囊 hover 状态；hero 顶部 padding 略收紧、整体最小高度略增加；proof 和 privacy 的文字与垂直内边距小幅增加。

- [ ] **Step 2: 更新移动端回落规则**

  在现有 `@media(max-width:620px)` 首页规则中，为 `.home-nav`、`.home-brand` 和 `.home-brand .brand-mark` 明确回落尺寸，确保放大后的桌面样式不会挤压移动端；继续隐藏 `.home-nav-links a`，保持单列 hero。

- [ ] **Step 3: 检查 diff，确认只包含首页视觉改动**

  Run: `git diff -- src/styles.css`
  Expected: 只看到首页导航、hero、proof、privacy 和对应移动端规则的 CSS 变化，不出现 `src/app.js` 或业务逻辑改动。

### Task 2: 构建和视觉回归验证

**Files:**
- Modify: none
- Test: existing Vite build and local browser inspection

**Interfaces:**
- Consumes: Task 1 的首页 CSS。
- Produces: 构建成功证据，以及桌面端和移动端无明显溢出、层级协调的验证结果。

- [ ] **Step 1: 运行生产构建**

  Run: `npm run build`
  Expected: Vite exits with code 0 and produces the build output without CSS or JavaScript errors.

- [ ] **Step 2: 检查桌面端首页**

  使用项目现有 dev server 在约 1440px 宽视口打开首页，确认顶部品牌单元明显增强、右侧导航可读、hero 标题仍是第一视觉焦点，且 hero 图片与 proof 区没有重叠或异常裁切。

- [ ] **Step 3: 检查移动端首页**

  使用约 390px 宽视口打开首页，确认 logo 与字标仍在一行、导航链接隐藏、标题和 CTA 可读、页面没有横向滚动。

- [ ] **Step 4: 汇总验证结果**

  报告构建命令结果与桌面 / 移动端视觉检查结果；若发现溢出，只调整首页对应 media query，不扩大任务范围。
