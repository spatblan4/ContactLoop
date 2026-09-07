# Import Students MVP 任务计划

## 目标

为 ContactLoop 增加安全的 CSV / XLSX 学生与 guardian 导入流程：上传、列映射、预览、重复处理、确认写入 Supabase，并支持一个学生对应多个 guardians。

## 当前阶段

阶段 5：测试、构建和浏览器回归验证

## 阶段

- [completed] 阶段 1：确认现有数据模型、认证和导入边界
- [completed] 阶段 2：解析器、列映射、重复检测和 Auth 基础
- [completed] 阶段 3：扩展 Supabase schema、RLS 和批量导入 RPC / client API
- [completed] 阶段 4：实现 Students 页面入口、四步导入 UI 与 empty/onboarding 状态
- [in_progress] 阶段 5：测试、构建和浏览器回归验证

## 已知限制与决策点

- 已补充 `npm test` 脚本，底层使用 `node --test tests/*.test.js`。
- 当前项目存在 demo RLS 和匿名数据，不能直接满足 `teacher_id = auth.uid()`。
- 当前 `students` 使用 `name` / `initials`，`guardians` 使用 `relation` / 必填 `phone`；导入方案需要兼容现有读写代码或提供迁移兼容层。
- 当前 `package.json` 没有 CSV/XLSX 解析依赖，需要决定是否增加可审计的解析库，或实现受限解析器。

## 阶段 6：修复追踪页与部署

- [completed] 创建 `docs/repair-tracker.html`，记录 meeting brief 打印修复、验证证据和部署状态。
- [completed] 将追踪页与前端修复部署到已关联的 Vercel 项目。
- [completed] 验证部署地址可访问，记录 URL 和任何环境限制。

## 2026-09-07：dev + Supabase + 真实 Agent 整合

### 目标

保留 dev 的 FastAPI、REST API、认证与 CRUD 架构，以只含虚构 Demo 数据的 Supabase 作为唯一业务数据源，并让现有 Strands / Bedrock Agent 从同一份数据生成结果。

### 安全边界

- 不修改或合并 `main`。
- 不 push、merge、删除项目文件、覆盖现有 Lambda 或创建收费云资源。
- 不在日志、计划或提交中记录任何密钥。
- 在 schema 与 ID 映射统一前，不把 dev 直接连接到旧 Lambda。

### 阶段

- [completed] 阶段 A：确认实际分支、worktree、运行服务来源和本地配置边界
- [completed] 阶段 B：只读比较 FastAPI 模型、仓库 SQL 与旧 Supabase 实际字段
- [completed] 阶段 C：设计兼容迁移与安全认证边界，并完成 FastAPI owner 权限修复
- [completed] 阶段 C2：编写并完成本地审查 Supabase 增量兼容迁移；等待用户批准云端应用
- [pending] 阶段 D：经确认后配置 dev 后端连接 Supabase 并建立虚构 Demo 数据
- [pending] 阶段 E：验证登录 → 学生 → 联系记录 → 真实 Agent 建议
- [pending] 阶段 F：整理验证证据；是否合并回 main 由用户另行决定

### 当前阻塞条件

- dev 当前没有本地 `.env`，也没有 `SUPABASE_DB_URL`；切换 FastAPI 到 Supabase 需要数据库连接串。
- 旧 Supabase schema 与 FastAPI 模型不兼容，不能只改连接字符串：需要先建立迁移方案并确认目标项目。
