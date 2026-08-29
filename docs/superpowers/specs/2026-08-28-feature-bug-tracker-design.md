# Feature / Bug Progress Tracker 设计

## 目标

创建一个无需构建、无需后端、双击即可打开的单文件 HTML，用来集中追踪 ContactLoop 项目的功能、Bug、剩余问题和知识库。现有 `progress.md`、`findings.md`、`task_plan.md` 将被整理为初始数据。

## 方案

采用浏览器本地优先的单文件应用：HTML 内嵌 CSS、JavaScript 和初始化数据，使用 `localStorage` 持久化。通过 JSON 导入/导出实现备份和跨浏览器迁移。本次不接入 Supabase，不改变现有应用运行逻辑。

视觉方向为项目控制台：深色墨蓝背景、暖色高亮、清晰的状态色和轻量网格纹理。桌面端使用侧边分类导航和主内容区，窄屏时自动堆叠；重点突出项目健康度、开放风险和最近更新。

## 信息架构

- 总览：项目进度摘要、各类型数量、状态分布、开放风险和最近更新。
- Features：功能记录列表，可按状态、优先级、关键词筛选。
- Bugs：Bug 列表，展示严重程度、复现/验证状态和关联文件。
- Remaining Issues：未完成事项和技术债，展示阻塞关系与下一步。
- Knowledge Base：决策、架构发现、部署限制和验证结论。

## 数据模型

工作项（Feature、Bug、Issue）字段：

- `id`、`type`、`title`、`description`
- `status`：Backlog、In progress、Blocked、Done
- `priority`：Low、Medium、High、Critical
- `tags`、`owner`、`dueDate`、`relatedFiles`
- `notes`、`updatedAt`

知识条目字段：

- `id`、`title`、`topic`、`summary`、`details`
- `relatedFiles`、`tags`、`updatedAt`

应用状态包括当前 section、搜索词、状态筛选、优先级筛选、编辑中的记录和持久化数据。

## 交互与数据流

1. 首次打开时检测固定的 localStorage key；不存在时写入内置初始数据。
2. 用户通过导航切换四类记录；列表根据搜索词、状态和优先级实时过滤。
3. 点击新增或编辑打开同一套表单；保存时校验标题和类型必填，并更新 `updatedAt`。
4. 删除操作要求浏览器确认；删除后立即刷新统计和列表。
5. 导出生成包含版本号和全部数据的 JSON 文件；导入前校验 JSON 结构，成功后替换当前本地数据并刷新页面状态。
6. 所有写操作集中经过一个持久化函数，避免界面状态和 localStorage 不一致。

## 错误处理与边界

- localStorage 不可用时显示明确提示，并允许当前页面临时使用内存数据。
- 导入 JSON 解析失败或缺少必要字段时拒绝导入，不覆盖已有数据。
- 日期为空时不显示截止日期；过期未完成事项在总览中标记风险。
- 相关文件以纯文本保存，不自动修改源码。
- 删除不可撤销，因此必须确认；导入替换前也必须确认。

## 验证标准

- HTML 文件可直接打开，无外部依赖和控制台致命错误。
- 初次加载包含项目现有记录的可读摘要。
- 四类记录可切换、搜索和筛选。
- 新增、编辑、删除会同步更新列表、统计和 localStorage。
- 刷新页面后记录仍然存在。
- JSON 导出文件可重新导入并恢复数据。
- 720px 以下布局可用，表单和按钮具备键盘焦点与基本 aria 标签。

## 范围控制

本次不实现登录、云同步、多人协作、自动读取 Markdown、GitHub API 集成或源码自动修改。未来如需多人协作，可在不改变 UI 数据模型的前提下替换持久化层。
