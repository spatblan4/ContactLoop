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
