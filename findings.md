# Import Students MVP 发现记录

## 项目现状

- 首页和 dashboard/students/follow-ups/contact log 都由 `src/app.js` 的模板字符串渲染。
- 数据访问集中在 `src/lib/supabase.js`。
- `supabase/schema.sql` 当前的 `students` 没有 `teacher_id`，字段是 `name`、`initials`、`accent`。
- `supabase/schema.sql` 当前的 `guardians` 没有 `teacher_id`，字段是 `student_id`、`name`、`relation`、`phone`，没有 email。
- 当前 RLS policy 使用 `to anon using (true)` / `with check (true)`，与数据归属验收标准冲突。
- 当前 app 没有看到登录 / `supabase.auth.getUser()` 的调用。
- 当前 `createStudent` 为 student 和 guardian 分两次写入，导入需要批量、可回滚或至少避免半写入。
- `package.json` 只包含 `@supabase/supabase-js`，没有 CSV/XLSX parser。

## 已确认

- 用户选择接入现有 Supabase Auth，并用 Email + Password 登录。
- 导入流程应使用 Auth 当前用户作为 teacher owner，不能继续依赖匿名全表读写。

## 新架构决策待确认

- 用户指出项目同时有 Hackathon demo 和真实朋友 / 用户试用两种场景。
- 不建议为了 demo 立刻新建第二个数据库；更合适的是同一套前端支持 `demo` 与 `authenticated` 两种运行模式。
- Demo 模式可使用现有展示数据和无登录体验，但不能用于真实用户或真实学生资料。
- Trial / production 模式必须启用 Supabase Auth、teacher_id 和严格 RLS。
- 如果未来需要隔离 demo seed 数据与真实试用数据，再建立 staging/demo Supabase project 与 production project；这属于部署隔离，不是导入功能本身的前置条件。
- 用户指出从黑客松到评奖约有较长反馈窗口，希望同事尽早试用；因此推荐并行环境，而不是先 demo 后 trial 的串行发布。
- 同一套代码通过环境变量区分 demo / trial；demo 与 trial 使用不同 Supabase project 或至少不同数据源，避免真实资料进入演示数据。
- GitHub 建议作为代码版本管理和部署来源，但 Supabase 中的数据不应放进 GitHub。
- 推荐 main 保持稳定的共享代码，并以环境变量分别连接 demo / trial Supabase；长期维护一个 demo branch 容易和 main 漂移。
- 如黑客松确实需要不同文案或固定演示流程，可短期保留 `demo` branch，但不在 branch 中保存真实学生数据或 secrets。

## 2026-08-26 项目健康审计

- 审计计划已建立：`docs/superpowers/plans/2026-08-26-project-health-audit.md`。
- 当前工作区包含未提交的前后端、测试和部署相关改动，审计必须保留这些用户改动，不能用重置或覆盖方式清理。
- 目前已确认前端主要由 `src/app.js` 模板渲染，领域逻辑分散在 `src/lib/`，后端逻辑位于 `supabase/functions/`；后续需要逐条核对这些边界是否一致。
- 初步结构：前端约 240 行 `src/app.js` + 273 行 CSS，领域辅助模块约 1,100 行，Supabase Edge Functions 和共享代码约 470 行，测试约 1,100 行；数量不算失控，但 `app.js` 仍承担较多 orchestration 和 HTML 事件绑定。
- 已发现需要重点核对的风险信号：`src/app.js` 同时兼容旧 `topic` 与新 `planned_topic/discussed_topics`；Supabase load 使用缺表 fallback；语音链路依赖多个 Edge Function；项目根目录保留多个 Lambda zip / Python 旧实现。
- 当前搜索还发现 `.env.local`、Playwright 运行日志和编译缓存存在于项目目录；需要确认 `.gitignore` 是否覆盖，避免敏感配置或临时文件进入 Git。

### Initial defects to verify before changing code

- `src/lib/telephony.js` appears to reference `plannedTopic` inside `TwilioTelephonyProvider.startCall` without receiving it in the method arguments. This is a likely runtime defect in the real-call path and needs a regression test before repair.
- Student Detail and Contact Log may not use the same topic presentation: the newer schema has `planned_topic` and `discussed_topics`, while some detail/log helpers still expose the legacy `topic` field. This needs an end-to-end consistency check.
- The base schema plus multiple patches may be the only supported database setup, while the frontend assumes the patched schema. We need to document or consolidate this carefully; changing migrations without checking deployed state would be risky.
- Old deployment artifacts and compatibility modules are present. They should only be removed after import/reference checks prove they are not part of the current app or deployment workflow.
- `.gitignore` already excludes `.env.local`, Playwright logs, Python caches, and zip artifacts, so these are repository-local clutter rather than currently exposed tracked files.
- `src/app.js` still contains a legacy `legacyStudentsScreen()` renderer alongside the active `studentsScreen()` renderer. It is a cleanup candidate only after confirming there is no route or test dependency.
- The dashboard greeting/date contains a hard-coded demo date (`Tuesday, August 25, 2026`) while the rest of the dashboard uses live range calculations. This can make the UI disagree with the selected/current data period.
- AI summary editing still uses `window.prompt()` for adding list items. That is functional but inconsistent with the app's modal UX and is a likely usability debt, not a reason to remove the feature.
- Baseline verification currently passes all 59 Node tests and the Vite production build. The build emits only a bundle-size warning; there is no failing automated check yet.
- The passing tests cover domain helpers and SQL/source contracts, but they do not yet prove browser-level flows such as clicking Call Parent, saving a note, refreshing after a Supabase write, or the full voice upload/transcription path.

## Final audit results

- Fixed the missing AI Summary edit handler; Edit now opens the in-card editor, and add/edit/delete/cancel paths are covered by tests and browser smoke checks.
- Fixed follow-up consistency: only one open task is presented per student/guardian, and a latest Connected event suppresses a stale open follow-up from the actionable list.
- Replaced the native reschedule prompt with the application modal and added calendar-date validation; the Follow-ups actions now use one consistent interaction model.
- Unified Meeting Brief with the current data model: it uses `discussed_topics` only for discussed topics, includes confirmed `teacher_notes`, uses the same effective open-follow-up rule, and keeps technical/provider data out of the printable detail history.
- Removed the unused generic export binding and the duplicate AI-summary save implementation; dashboard date text is now derived from the current date.
- Final verification: 66/66 Node tests pass, Vite production build passes, `git diff --check` passes, and browser smoke checks cover the homepage/demo, dashboard filters and actions, Students search/add/import entry, Follow-ups grouping/actions, Contact Log filters/topic/detail/export entry, Student Detail notes and AI editor, planned-topic call entry, and Meeting Brief settings.
- External live integrations remain environment-dependent: real Twilio calls/status webhooks, deployed Supabase Edge Functions, Google Speech/Transcribe, and Bedrock/Strands cannot be claimed as locally verified without invoking the user's cloud services. Their request/response contracts are covered where testable.
- Remaining non-blocking cleanup: the production bundle is approximately 647 kB minified and Vite warns about chunk size. Code splitting can be a later performance task; it is not a functional defect.

## 2026-08-28 repair tracking

- The repository already contains a design spec for a local-first feature/bug tracker, but no tracker HTML existed under `docs/`.
- The tracker should remain dependency-free and must not read or mutate source files automatically; related files are recorded as plain text.
- Vercel project linkage exists in `.vercel/project.json` for `contactloop-beta`; deployment requires the locally authenticated Vercel CLI.
- Production deployment `dpl_GiHwY2tcsnmQH3X4ZE2THKRwvE6o` reached READY; `/docs/repair-tracker.html` is served through a rewrite to the public copy.

## 2026-09-07 dev / Supabase 兼容性审计

- 当前用户打开的项目根目录是 `main`，且包含未提交改动；未对其进行写入、切换或合并。
- 独立 `dev` worktree 位于 `/private/tmp/contactloop-dev-worktree-20260906`，工作区干净，`dev` 比 `origin/dev` 超前 11 个本地提交。
- 端口 5173 与 8000 的进程 cwd 均指向该 dev worktree（后端 cwd 为其 `backend/`），因此当前运行服务确实来自 dev。
- dev 后端配置优先级为 `SUPABASE_DB_URL` → `DATABASE_URL` → SQLite；当前 dev 仅有 `.env.example`，没有实际 `.env`，所以当前运行后端使用 SQLite fallback。
- FastAPI SQLAlchemy 模型包含统一审计/软删除字段：`updated_at`、`created_by`、`updated_by`、`deleted_at`；旧 Supabase 多数业务表缺少这些字段。
- 学生归属字段存在直接冲突：FastAPI 使用 `students.owner_id`，旧 Supabase auth patch 使用 `students.teacher_id`；旧 Supabase 实际上两者都没有。
- 旧 Supabase 实际字段通过匿名 key 的零行 REST 查询核对，未读取或输出任何学生记录。
- `students` 缺少：`first_name`、`last_name`、`teacher_id`、`owner_id` 和 FastAPI 审计字段。
- `guardians` 缺少：`email`、`preferred_contact_method` 和 FastAPI 审计字段。
- `contact_events` 已有 topic、Twilio、follow-up 等现有 Agent 所需字段，但缺少 FastAPI 的软删除/审计字段。
- `follow_ups` 缺少 `completed_at` 和 FastAPI 软删除/审计字段。
- `teacher_notes` 与 `ai_contact_briefs` 也缺少部分 FastAPI 审计字段。
- 后端使用 `Base.metadata.create_all()`，它只能创建缺失表，不能为既有表补列；因此仅设置 Supabase DSN 后启动会遇到 schema 不匹配。
- 现有 Contact Brief Agent 读取 `contact_events`、`teacher_notes`、`follow_ups`，并调用 `get_contact_stats` RPC；这些主要读取契约与旧 Supabase 结构大体兼容，但学生 ID 必须与 FastAPI 使用的同一套数据一致。
- 只读 OpenAPI schema 请求返回 401，但表的零行查询返回 200；采用逐列零行查询完成了兼容性核对。
- 一次 zsh 列拆分写法错误导致首轮逐列结果无效；已改用 zsh `${(s:,:)cols}` 数组拆分完成有效复核。
- dev 的 `/auth/register`、`/auth/login` 使用 FastAPI 自己的 `users` 与 `auth_tokens` 表，不是 Supabase Auth；若迁移到 Supabase Postgres，这两张表也会位于同一数据库中。
- `get_current_user_id` 是“尽力解析”，匿名请求会得到 `None` 而不是被拒绝；students 列表在匿名时不会按 owner 过滤。
- students 的详情、更新和删除端点按当前源码没有验证该 student 是否属于当前用户。其他资源仍需逐端点完成同类授权审计，不能把“有登录”直接等同于“所有 CRUD 已租户隔离”。
- dev 中有两类不同 AI：现有 Contact Brief Agent 针对单个 student，从 Supabase 读取并生成摘要；新 Outreach Plan Agent 针对整个已授权候选列表，回答“谁该联系/为什么/下一步”。
- FastAPI 的 Contact Brief 生成端点当前明确返回 501；前端旧路径仍可直接调用配置的 AWS Contact Brief endpoint。
- 历史发现（已被取代）：当时 FastAPI 的 Outreach Plan 端点需要 `OUTREACH_PLAN_ENDPOINT` 与服务 token。当前实现已改为在 FastAPI 内运行真实 Strands Agent，并直接调用 Amazon Bedrock；现有 `contactloop-contact-brief` Lambda 保持不变。
- 因此，在“不覆盖现有 Lambda、也不贸然新建 Lambda”的边界下，不能假设现有 Contact Brief Lambda 能直接充当 Outreach Plan Agent。可选方向需要用户确认：本地运行新 Outreach Agent用于现场 demo，或仅接入现有 Contact Brief 并把全班优先级作为后续功能。

## 2026-09-07 Supabase 增量兼容迁移审查

- 新增 `supabase/patch-fastapi-supabase-compat.sql`；它不包含删除记录、表、列或 truncate 操作。
- 迁移创建 FastAPI 自有的 `users` / `auth_tokens` 表，并为既有业务表补充 `owner_id`、审计/软删除字段、姓名和 guardian 补充字段、follow-up 完成时间及索引。
- 迁移不触碰现有 Agent 读取所依赖的业务记录或 RPC；`contact_events.discussed_topics` 保持既有 `text[]` 类型。
- FastAPI 模型已使用 PostgreSQL `text[]` variant 兼容该列，避免将历史 topics 转为 JSONB 的破坏性 schema 修改。
- 迁移启用 RLS 并移除业务表上的所有现有 policy，使浏览器不能直连业务表；FastAPI 使用后端数据库连接，现有 Lambda 使用服务端凭据。
- 迁移暂未连接、执行或应用至 Supabase；应用前必须再次只读核对数据范围并获用户明确批准。

## 2026-09-07 旧 Supabase 只读 Demo 范围核对

- 通过现有匿名只读配置查询，不读取或输出姓名、电话、备注或联系内容。
- 记录数量：students 4、guardians 4、contact_events 31、follow_ups 4、teacher_notes 6、ai_contact_briefs 5。
- students 的 4 个 UUID 与仓库固定 Demo seed UUID 一致：1111…、2222…、3333…、4444…。
- guardians、contact_events、follow_ups、teacher_notes、ai_contact_briefs 的所有 `student_id` 均属于上述 4 个 UUID；未发现另一套学生 ID。
- 结论：从 ID 范围和数量证据看，当前旧 Supabase 可作为虚构 Demo 数据的兼容迁移候选。该结论不等同于已执行迁移，云端数据尚未改动。
