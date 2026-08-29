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
