# Import Students MVP 任务计划

## 目标

为 ContactLoop 增加安全的 CSV / XLSX 学生与 guardian 导入流程：上传、列映射、预览、重复处理、确认写入 Supabase，并支持一个学生对应多个 guardians。

## 当前阶段

阶段 2：Import Students 实施（待开始）

## 阶段

- [completed] 阶段 1：确认现有数据模型、认证和导入边界
- [in_progress] 阶段 2：Import Students 实施计划已确认，准备开始解析器与 Auth 基础
- [pending] 阶段 3：扩展 Supabase schema、RLS 和批量导入 RPC / client API
- [pending] 阶段 4：实现 Students 页面入口、四步导入 UI 与 empty/onboarding 状态
- [pending] 阶段 5：测试、构建和浏览器回归验证

## 已知限制与决策点

- 当前项目没有 `npm test` 脚本，但可以使用 `node --test tests/*.test.js`。
- 当前项目存在 demo RLS 和匿名数据，不能直接满足 `teacher_id = auth.uid()`。
- 当前 `students` 使用 `name` / `initials`，`guardians` 使用 `relation` / 必填 `phone`；导入方案需要兼容现有读写代码或提供迁移兼容层。
- 当前 `package.json` 没有 CSV/XLSX 解析依赖，需要决定是否增加可审计的解析库，或实现受限解析器。
