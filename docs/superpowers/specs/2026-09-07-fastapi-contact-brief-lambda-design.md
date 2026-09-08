# FastAPI Contact Brief Lambda 接入设计

## 目标

让已登录老师在 ContactLoop 中为自己拥有的 Demo 学生生成真实的 Strands / Amazon Bedrock Contact Brief，同时保留现有 `contactloop-contact-brief` Lambda、Supabase 数据和教师审核流程。

## 边界

- 只使用现有 Lambda；不创建、部署、覆盖或重命名任何 Lambda。
- FastAPI 是浏览器访问 AI 的唯一入口；浏览器不直接调用 Lambda 或 Supabase Edge Function。
- Lambda URL 只保存在 `backend/.env` 的服务器配置中，不放入 `VITE_*`、浏览器存储、源码或测试输出。
- Lambda 继续用其服务器端 Supabase service-role 凭据读取数据；FastAPI 不向 Lambda 转发数据库密钥、老师令牌、姓名或电话。
- 只允许虚构 Demo 数据；不查询或写入真实学生资料。
- 生成结果保持 `draft`，由现有前端和 FastAPI CRUD 流程保存、编辑、批准或删除。

## 数据流

```text
Browser (Bearer token + student UUID + date range)
  -> FastAPI POST /api/v1/ai/contact-brief/generate
  -> 验证当前老师拥有 student UUID
  -> 已有 contactloop-contact-brief Lambda
  -> 同一 Supabase Demo 数据 + Strands / Bedrock
  -> 结构化 Contact Brief
  -> Browser 现有教师审核与保存流程
```

## FastAPI 行为

`POST /api/v1/ai/contact-brief/generate` 接收：

```json
{
  "student_id": "11111111-1111-4111-8111-111111111111",
  "date_from": "2026-08-01T00:00:00Z",
  "date_to": "2026-09-08T00:00:00Z",
  "include_notes": true
}
```

FastAPI 在调用 Lambda 前必须使用现有 `require_owned_student` 检查 `student_id`。未登录返回 `401`；其他老师的学生返回 `404`；请求格式错误返回 `422`。Lambda 不可达或返回非成功状态时，FastAPI 返回不含密钥、数据库内容或 Lambda 内部堆栈的 `502`。

服务器端 Lambda 客户端把相同的四个字段转发至已有 Lambda 的 `/contact-brief` 路径。成功结果必须是已有 Lambda 的结构：`provider`、`review_status`、`stats` 与 `brief`。

## 前端行为

本地忽略的前端配置将 `VITE_CONTACT_BRIEF_PROVIDER` 设为 `aws-strands-bedrock`，使现有 “Generate summary” 按钮可用。前端仍调用 FastAPI，不读取或使用 Lambda URL。生成后沿用现有流程，以 `draft` 版本保存到 `ai_contact_briefs`，再由老师审核。

## 验证

1. SQLite 测试证明：未登录请求被拒绝、跨老师请求被拒绝、所属学生请求只转发允许字段。
2. 前端测试证明：启用 provider 时请求仍发向 `/api/v1/ai/contact-brief/generate`，不含 Lambda URL。
3. 使用 Emma Johnson 的统一 Demo UUID 发起一次真实 Lambda 请求；确认返回 `provider: aws-strands-bedrock` 和结构化 `brief`。
4. 在 UI 中点击 Generate summary，确认生成的内容显示为 `Needs teacher review`，再由当前老师保存/批准。

## 不在本次范围

- 新 Outreach Agent 的本机运行或部署。
- Lambda 代码、AWS IAM、Bedrock 模型、Supabase Edge Function 的修改。
- 将任何真实电话或学生资料导入 Demo 数据。
