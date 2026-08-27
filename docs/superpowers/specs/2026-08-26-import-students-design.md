# ContactLoop Import Students 设计

## 目标

为老师提供稳定、安全的 CSV / XLSX 学生与 guardian 导入流程。老师可以上传文件、确认列映射、预览和修正数据、处理重复记录，最后将结构化数据写入 Supabase。一个 student 必须支持多个 guardians，真实试用数据必须按当前认证老师隔离。

## 发布与运行模式

同一套代码支持两个环境：

- `demo`：用于黑客松展示，跳过登录，使用固定展示数据，不写入真实 roster。
- `authenticated`：用于朋友和真实试用，使用 Supabase Email + Password Auth、teacher ownership 和严格 RLS。

通过环境变量选择模式和 Supabase project。Demo 与 trial 推荐使用不同 Supabase project；代码不分叉，学生数据不进入 GitHub。

## 认证与数据架构

### Auth

authenticated 模式启动时读取 Supabase Auth session。未登录用户看到 Email + Password 登录页，并可切换到创建账号。登录成功后才能加载 Dashboard、Students、Follow-ups 和 Contact Log。session 失效时清理页面状态并回到登录页。

demo 模式不显示登录页，继续使用固定 demo 数据。

### 数据模型

`students` 增加 `teacher_id`、`first_name`、`last_name`，保留现有 `name`、`initials`、`accent` 以兼容已有页面。

`guardians` 增加 `email`、`preferred_contact_method`，保留现有 `student_id`、`name`、`relation`、`phone`。

一个 student 通过 `guardians.student_id` 关联多个 guardians，不使用 `student.mom_name` / `student.dad_name` 等固定字段。

`contact_events`、`follow_ups`、AI summary 和 teacher notes 通过所属 student 的 `teacher_id` 进行访问控制。

### Ownership / RLS

- 新数据的 owner 必须由数据库从 `auth.uid()` 获取，前端不能传入 teacher_id 作为信任来源。
- authenticated 用户只能读取、修改自己的 students。
- guardian 只能通过自己所属的 student 被访问。
- follow-ups、contact events、AI 数据和 teacher notes 只能访问属于当前老师的 student。
- 删除现有匿名全表读写 policy，改为 authenticated + owner 条件。
- 旧 demo seed 数据如果没有 teacher_id，不出现在 authenticated 用户数据中；不把真实用户数据写进 demo project。

## Import Flow

导入流程使用 app 内的独立 screen，不加入 Sidebar 一级导航：

```text
Students → Import students → Upload → Match Columns → Review → Complete
```

### Step 1 — Upload

- 页面标题为 `Import students`，说明为 `Upload your existing student and guardian list.`
- 支持拖拽和 Browse files。
- 支持 `.csv` 和 `.xlsx`。
- 提供 `Download ContactLoop Template`。
- 原始文件只在浏览器内存中处理，不上传 Storage、不写日志、不打印到 console。

模板字段为：

```text
Student First Name
Student Last Name
Guardian Name
Relationship
Phone
Email
```

### Step 2 — Match Columns

前端先使用安全的本地别名做建议映射，例如：

```text
Child      → Student Full Name
Parent 1   → Guardian Name
Relation   → Relationship
Cell Phone → Phone
```

页面显示每个 source column 对应的 target field，并允许老师通过 dropdown 修改。

标准 target fields：

- Student First Name
- Student Last Name
- Student Full Name
- Guardian Name
- Relationship
- Phone
- Email

如果只有 Student Full Name，保留完整姓名，并按最后一个空格做简单 first / last 拆分；不使用 AI 猜测真实姓名。

无法确定的列标记为 `Needs review`。未确认必需映射前不能进入 Review。

第一版不接 AI。后续如果启用 AI，只发送 column header names，不发送 roster rows；AI 不得编造或修复姓名、电话、关系或缺失数据。

### Step 3 — Review

页面展示：

```text
Ready to import
24 students
31 guardians
2 rows need review
```

预览表格列：

```text
Student | Guardian | Relationship | Phone | Email | Status
```

状态规则：

- `Ready`：学生姓名、guardian 姓名和映射均确认，且没有明显重复。
- `Needs review`：缺少学生姓名、guardian 姓名、Relationship，或映射仍不明确。
- `Duplicate`：与当前老师的数据或导入内其他数据存在明显重复。

Phone / Email 缺失不编造数据；Relationship 缺失进入 Needs review。

Needs review 行可以展开编辑。Duplicate 行在 MVP 支持：

- Skip
- Import as new

第一版不实现 Update existing，避免意外覆盖真实资料。没有 Ready 记录时禁用 `Import ready records`。

### Duplicate Detection

按以下优先级识别明显重复：

1. 当前 teacher_id + 标准化 student name
2. student + guardian phone
3. guardian phone

导入内相同学生的多行按标准化学生姓名分组。例如 Emma Johnson 的两行会生成一个 student 和两个 guardians。

### Step 4 — Complete

成功后显示导入的 student / guardian 数量、`Your student list is ready.` 和 `View Students`。点击后回到 Students 页面并刷新真实数据。

## Supabase 写入

前端只发送老师确认后的结构化 Ready rows，排除 Skip rows 和未修正的严重错误。

新增 `import_students` RPC：

- 从 `auth.uid()` 获取 teacher_id。
- 在一次数据库事务中按分组创建 students 和 guardians。
- 不接收前端 teacher_id 作为 owner。
- 发生严重错误时整体失败，避免 student / guardian 半写入。
- 返回导入统计和必要的已创建记录信息。

原始 CSV / XLSX 在 RPC 成功或失败后都从浏览器状态释放，不长期保存。

## Students 与 Dashboard UI

有学生时 Students 右上角显示：

```text
[ + Add Student ] [ Import Students ]
```

没有学生时显示 empty state：

```text
Add your students to get started

Import a spreadsheet or add students manually.

[ Import CSV / Excel ]
[ Add student manually ]
```

当当前用户没有任何学生时，Dashboard 显示一次 onboarding CTA：

```text
Set up ContactLoop

Import your student and guardian list to start tracking parent communication.

[ Import students → ]
```

CTA 由真实 students 数量决定，导入成功和刷新后自动消失，不依赖 localStorage。Demo seed data 非空时不显示 CTA。

## 隐私与错误处理

- 原始 roster 文件不上传、不保存、不进入 public console。
- 预览数据只在当前老师的浏览器中显示。
- 不发送整份 roster 到 AI；如使用 AI，只发送 headers。
- 不支持的文件、空文件和解析错误停留在 Upload 并给出明确提示。
- 无法识别列或严重缺失字段停留在 Match Columns / Review。
- RPC 失败时保留 Review 状态和预览数据，不丢失老师修改。
- 不自动覆盖重复记录，不编造缺失字段。

## 测试与验收

新增纯函数测试覆盖：CSV 解析、XLSX 行标准化、alias mapping、full name 拆分、多 guardian 分组、缺失字段、duplicate detection、import payload。

集成和回归验证覆盖：Auth 门槛、Students empty state、Dashboard onboarding、导入成功后的 CTA 消失、RPC owner 来源、RLS、刷新后数据持久化、`npm run build` 和现有 Node 测试。

本次 MVP 不包含 PDF、OCR、SIS、Google Classroom、PowerSchool 或自动 district sync。
