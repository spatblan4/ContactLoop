# ContactLoop FastAPI + Supabase 权限设计

## 目标

在 2026-09-14 黑客松截止日前交付同一套可演示、可供同事安全试用的 ContactLoop：浏览器只访问 FastAPI，FastAPI 使用 Supabase Postgres 作为唯一数据库，现有 Contact Brief Lambda 读取同一份虚构 Demo 数据。

## 固定架构

```text
Browser → FastAPI REST API → Supabase Postgres
                              ↑
Existing Contact Brief Lambda ┘

FastAPI → local Strands / Bedrock Outreach Agent
```

- FastAPI 是唯一业务 API，负责登录、授权、CRUD、输入校验和传给 Agent 的最小数据范围。
- Supabase 在本阶段只承担托管 Postgres；不引入第二套 Supabase Auth。
- 保留 FastAPI 现有 `users` / `auth_tokens` 登录机制，表也存入 Supabase Postgres。
- 前端不得持有数据库连接串或 service-role key，也不直接写业务表。
- 现有 `contactloop-contact-brief` Lambda 不覆盖、不改名；新 Outreach Agent 先在本机运行，不创建 Lambda。

## Demo 与试用

- 一个固定 Demo 账号拥有 4 位虚构学生及虚构联系记录，用于黑客松演示。
- 每位同事使用独立账号；所有业务数据通过 `students.owner_id` 隔离。
- Beta 阶段要求同事只使用虚构或脱敏数据，完成更完整的隐私与部署审计前不录入真实学生资料。
- Demo 和同事试用走同一套 FastAPI 与数据库代码，不维护假的前端数据通路。

## API 授权规则

- `/auth/register`、`/auth/login`、健康和 meta 接口可匿名访问。
- students、guardians、contact events、follow-ups、teacher notes、AI briefs、dashboard、imports、voice 和 Agent 接口必须携带有效 FastAPI bearer token。
- 创建 student 时由 FastAPI 写入当前用户的 `owner_id`，客户端不能指定 owner。
- 所有资源访问沿 `resource.student_id → students.owner_id` 校验当前用户。
- 跨账号访问与不存在资源统一返回 404，避免暴露记录是否存在。
- 列表、聚合和 Agent 候选数据必须先按 owner 过滤。

## Supabase 兼容原则

- 使用增量迁移：补列、补表、补索引，不删除现有 Agent 使用的表、字段或 `get_contact_stats` RPC。
- FastAPI 与 Contact Brief Lambda 使用同一批 Demo student UUID。
- FastAPI 数据库连接串仅保存在后端环境变量中。
- 应用迁移前只读检查旧数据范围；任何删除、覆盖或替换必须再次取得用户明确许可。

## 实施顺序

1. 在 SQLite 上以测试驱动修复所有 owner 授权边界。
2. 生成并审查 Supabase 兼容迁移 SQL。
3. 只读确认旧 Supabase 数据范围。
4. 经确认后应用迁移并建立 Demo 账号和统一 Demo 数据。
5. 配置 FastAPI 使用 Supabase Postgres，验证登录与 CRUD。
6. 用统一 UUID 验证现有 Contact Brief Lambda 的真实 Bedrock 输出。
7. 本机接通真实 Outreach Agent，验证“谁该联系、上次发生什么、何时跟进”。

## 验收标准

- 匿名请求不能访问任何业务数据。
- 用户 A 不能读取、修改或删除用户 B 的任何资源。
- Demo 账号能完成登录、学生、联系记录、follow-up 和真实 Contact Brief 流程。
- 同事账号只能看到自己的数据。
- 前后端完整测试通过，现有 Lambda 未被覆盖，没有新建收费云资源，没有 push 或 merge。
