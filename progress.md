# Import Students MVP 进度

## 2026-08-26

- 已读取 brainstorming、planning-with-files-zh、frontend-design、karpathy-guidelines 规范。
- 已检查当前 app、Supabase schema、数据访问层和 package.json。
- 已确认当前项目处于 demo / anonymous RLS 状态，和用户要求的 teacher-owned RLS 存在基础冲突。
- 用户已确认：接入 Supabase Auth，使用 Email + Password 登录。
- 用户提出 Hackathon demo 与真实试用的取舍问题。
- 设计暂时调整为：同一套代码支持 demo / authenticated 两种模式；只有真实试用模式启用 Auth、teacher_id 和 RLS。
- 用户希望立即让同事试用，不等待黑客松结束。
- 当前建议改为并行环境：共享一套代码，demo 环境固定展示数据，trial 环境启用 Auth、RLS 和真实 Import Students；通过环境变量切换 Supabase URL / app mode。
- Git 分支建议：main 保持稳定共享代码；demo / trial 通过环境变量和不同 Supabase project 区分，而不是把数据放入 branch。
- 已创建本地初始 Git commit，并绑定 / 推送到 `https://github.com/spatblan4/ContactLoop` 的 `main`。
- 远程已有 README commit，已安全合并；当前 `main` 与 `origin/main` 同步。
- 下一步恢复 Import Students 设计：确认解析、列映射、预览和重复检测部分。
- 用户已确认 Import Students 的解析、映射、预览、重复检测、浏览器内临时处理和事务导入设计。
- 当前待确认最后一部分：四步 UI、认证门槛、empty/onboarding、错误处理和测试策略。
- 已完成 CSV / XLSX 解析、列映射建议、Needs review 校验、重复记录处理和多 guardian 分组。
- 已完成 Students 页面入口、空状态、Dashboard 首次 onboarding CTA、四步 Import UI 和本地编辑预览。
- 已完成 Auth helper、demo/authenticated 环境切换、owner-derived `import_students` RPC client，以及 authenticated trial 的 Supabase SQL patch。
- 已添加 `npm test`，当前 55 个测试全部通过；`npm run build` 已通过，仅有 bundle size warning。
- 已为旧 Demo 表结构增加读取 fallback，避免 demo 项目因新字段不存在而无法加载。

## 2026-08-26 项目健康审计

- 已读取并遵循系统化调试、TDD、验证、计划和代码审查规范。
- 已记录当前工作区状态：存在历史用户改动和未提交文件，后续只做证据驱动的审计与低风险修复。
- 下一步：建立完整模块/数据流地图并核对 Supabase 字段、状态和事件边界。
- 已记录一个疑似 Twilio provider 参数缺陷、Student Detail topic 展示一致性风险，以及 schema/deployment 漂移风险；尚未进行破坏性清理。
- 已确认 `.gitignore` 已覆盖本地环境变量、Playwright 日志、Python 缓存和 zip 构建产物；同时记录了 active/legacy Students renderer、硬编码 dashboard 日期和 `window.prompt()` 编辑入口作为后续核查项。
- 基线验证：`npm test` 通过 59/59；`npm run build` 通过，只有 bundle 超过 500 kB 的提示。下一步需要补浏览器级关键流程验证，并继续核对后端与页面的真实连接。

## 2026-08-27 项目健康审计完成

- 已完成 AI Summary 编辑处理器、Follow-up 去重/Connected 自动关闭判断、应用内 Reschedule 弹窗、动态日期、Meeting Brief teacher notes 同步和冗余绑定清理。
- 已补充相应的领域测试与回归测试；最终 `npm test` 通过 66/66。
- 已通过 `npm run build` 和 `git diff --check`；构建仅剩 bundle size warning。
- 已完成浏览器 smoke 验收：首页、Demo Dashboard、日期筛选、Call Parent 主题选择、Students 搜索/添加入口、Follow-ups 分组与菜单、Contact Log 筛选/详情/导出入口、Student Detail notes/AI 编辑器、Meeting Brief 设置和 Print 入口。
- 当前审计结论：本地 UI 与可确定性业务逻辑链路正常；真实 Twilio、Supabase 部署环境、Google Speech/Transcribe、Bedrock/Strands 仍需使用云端配置做一次 live integration test，不能用本地测试冒充已验证。

## 2026-08-28 meeting brief print fix

- Fixed print layout root cause in `src/styles.css`: print now resets the app shell to one column and restores desktop brief columns.
- Added a CSS contract regression test in `tests/meeting-brief.test.js`.
- Verification evidence: `npm test` 80/80 passed, `npm run build` passed, and `git diff --check` passed.
- Browser print CLI did not return a snapshot or evaluation result in this environment, so visual print-preview verification remains an explicit limitation.
- Current follow-up completed: publish the repaired frontend and the new repair tracker page to the linked Vercel project.

- Deployed production to `https://contactloop-beta.vercel.app`.
- Verified HTTP 200 for `/`, `/repair-tracker.html`, and `/docs/repair-tracker.html` (Vercel rewrite).
- Demo deployment also reached READY at `https://contactloop-demo.vercel.app`; verified HTTP 200 for the demo root and `/docs/repair-tracker.html`.
- Resolved demo `Invalid API key`: the prior deployment had a malformed build-time anon key; redeployed from `.env.demo.local`, and the real `students` REST query now returns HTTP 200.

## 2026-09-07 dev + Supabase + Agent 整合

- 确认主工作目录实际位于 `main` 且有用户未提交改动；未修改、切换或合并该分支。
- 确认真正的 `dev` 在独立临时 worktree，且当前 5173/8000 服务均从该 worktree 启动。
- 检查 dev 后端配置、SQLAlchemy 模型、仓库 Supabase SQL 和 Contact Brief Agent 的读取契约。
- 使用现有本地匿名配置执行零行只读 REST 查询，仅核对字段存在性，没有输出密钥或学生记录。
- 完成兼容性结论：旧 Supabase 与 FastAPI 模型不是即插即用；必须先处理 owner 字段、审计/软删除字段、认证用户映射和迁移方式。
- 遇到的错误：受限环境内 `ps` 返回 operation not permitted；改用 `lsof` 的 cwd 信息确认服务来源。
- 遇到的错误：Supabase OpenAPI 元数据请求返回 401；改用逐字段 `limit=0` 请求核对 schema。
- 遇到的错误：首轮 zsh 字段分隔未生效；修正为显式 zsh 数组拆分后完成复核。
- 下一步：先产出不破坏旧 Agent 读取契约的兼容迁移设计，再请求/配置数据库 DSN；尚未改动数据库、运行配置或云资源。
- 完成认证与 AI 路径审计：dev 本地 auth 与 Supabase Auth 是两套机制；发现部分 students 端点尚未强制 owner 校验，需要在声称“权限安全”前修复和测试。
- 确认现有 Contact Brief Lambda 与新 Outreach Plan Lambda 是两种不同协议；在禁止覆盖/新建 Lambda 的条件下，需要先确认比赛 demo 要展示哪一种真实 Agent 路径。

## 2026-09-07 owner 权限修复

- 固定最终架构：Browser → FastAPI → Supabase Postgres；保留 FastAPI auth，Supabase 本阶段只作为数据库。
- 新增集中 owner 校验，students 及所有关联资源必须属于当前 bearer token 用户。
- 所有业务 API 现在要求登录；`X-User-Id` 不再能建立身份或覆盖审计 owner。
- 匿名访问业务接口返回 401；跨账号资源 ID 统一返回 404。
- voice upload/transcription 的 student context 也验证 owner；dashboard、import 和 AI 路由强制登录。
- TDD 证据：新增测试在修复前准确失败；修复后后端 101/101、前端 129/129 通过，Vite build 与 `git diff --check` 通过。
- 仅保留两项第三方弃用 warning：Starlette TestClient/httpx 与 anyio BlockingPortal；不影响本次权限验收。

## 2026-09-07 Supabase 增量迁移草案

- 新增并本地验证 FastAPI/Supabase 兼容迁移和 SQL 契约测试。
- 迁移为只增加结构与收紧直连数据库 policy：不会删除或清空记录、表、列，也不会变更现有 Agent 的读取 RPC。
- 处理 `discussed_topics` 类型差异：保持旧 Supabase `text[]`，后端在 PostgreSQL 使用数组 variant。
- 验证：后端 102/102、前端 132/132、生产构建、SQL 契约和 `git diff --check` 均通过。
- 云端状态未变；下一步必须先向用户展示迁移审查结论，取得许可后再只读检查旧 Supabase 数据范围。
