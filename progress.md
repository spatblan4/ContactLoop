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
