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
