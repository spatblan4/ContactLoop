# FastAPI Contact Brief Lambda 接入实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让已登录老师通过 FastAPI 为自己拥有的 Demo 学生调用已有 Contact Brief Lambda，并在 UI 中获得真实 Strands / Bedrock 摘要。

**Architecture:** 浏览器只向 FastAPI 发送 bearer token、student UUID 与日期范围。FastAPI 验证学生归属后，以服务器端 `CONTACT_BRIEF_ENDPOINT` 调用已有 Lambda 的 `/contact-brief` 路径。Lambda 保持不变，从同一 Supabase 读取数据；前端沿用当前 draft / 审核流程。

**Tech Stack:** FastAPI、SQLAlchemy、httpx、Pydantic、Vite、现有 AWS Lambda、Strands / Amazon Bedrock。

## Global Constraints

- 不创建、部署、覆盖或修改 `contactloop-contact-brief` Lambda、AWS IAM、Bedrock 模型或 Supabase Edge Function。
- 不把 Lambda URL、Supabase service-role key、AWS 凭据或老师 token 放入 `VITE_*`、浏览器存储、测试输出或源码。
- `POST /api/v1/ai/contact-brief/generate` 必须先调用 `require_owned_student`。
- 所有自动测试必须 monkeypatch Lambda 客户端；测试不得真实调用 Lambda 或 Bedrock。
- 实际 Bedrock 调用仅在实现完成后，由用户在 UI 中明确点击 Generate summary 触发。
- 不改动 main，不 push，不 merge，不删除数据或项目文件。

---

### Task 1: 建立服务器端 Lambda 客户端与配置

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/services/contact_brief_client.py`
- Create: `backend/tests/test_contact_brief_client.py`

**Interfaces:**
- Consumes: `settings.contact_brief_endpoint: str | None`。
- Produces: `invoke_contact_brief(payload: dict[str, object]) -> dict[str, object]`。
- Failure: `ContactBriefUnavailable`，消息不得包含 endpoint、凭据或上游原始响应体。

- [ ] **Step 1: 写失败测试**

```python
def test_contact_brief_client_posts_only_allowed_payload(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return httpx.Response(200, json={"provider": "aws-strands-bedrock", "brief": {}})

    monkeypatch.setattr(contact_brief_client.httpx, "post", fake_post)
    monkeypatch.setattr(settings, "contact_brief_endpoint", "https://lambda.example.test")

    result = invoke_contact_brief({"student_id": "student-1", "date_from": "2026-08-01T00:00:00Z", "date_to": "2026-09-08T00:00:00Z", "include_notes": True})

    assert result["provider"] == "aws-strands-bedrock"
    assert captured["url"] == "https://lambda.example.test/contact-brief"
    assert captured["json"] == {"student_id": "student-1", "date_from": "2026-08-01T00:00:00Z", "date_to": "2026-09-08T00:00:00Z", "include_notes": True}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `../.venv/bin/python -m pytest tests/test_contact_brief_client.py -q -p no:cacheprovider`

Expected: FAIL，因为客户端和配置尚不存在。

- [ ] **Step 3: 最小实现**

```python
class ContactBriefUnavailable(Exception):
    pass

def invoke_contact_brief(payload: dict[str, object]) -> dict[str, object]:
    endpoint = settings.contact_brief_endpoint
    if not endpoint:
        raise ContactBriefUnavailable("Contact Brief is not configured on this server.")
    try:
        response = httpx.post(
            f"{endpoint.rstrip('/')}/contact-brief",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
    except httpx.HTTPError as exc:
        raise ContactBriefUnavailable("Unable to reach the Contact Brief service.") from exc
    if response.is_error:
        raise ContactBriefUnavailable("Contact Brief generation is temporarily unavailable.")
    body = response.json()
    if not isinstance(body, dict):
        raise ContactBriefUnavailable("Contact Brief returned an invalid response.")
    return body
```

Add `contact_brief_endpoint: str | None = None` to `Settings`.

- [ ] **Step 4: 运行测试确认通过**

Run: `../.venv/bin/python -m pytest tests/test_contact_brief_client.py -q -p no:cacheprovider`

Expected: PASS；没有网络请求。

### Task 2: 用所有权检查启用 FastAPI 端点

**Files:**
- Modify: `backend/app/api/v1/ai_briefs.py`
- Create: `backend/tests/test_contact_brief_generation.py`

**Interfaces:**
- Consumes: `POST /api/v1/ai/contact-brief/generate` JSON `student_id`、`date_from`、`date_to`、`include_notes`。
- Produces: 原样返回现有 Lambda 的结构化结果。
- Security: 未登录 `401`；跨老师学生 `404`；所属学生才调用 `invoke_contact_brief`。

- [ ] **Step 1: 写失败测试**

```python
def test_contact_brief_generation_rejects_other_teachers_student(client, second_auth, make_student):
    student = make_student(guardians=[])
    response = client.post(
        "/api/v1/ai/contact-brief/generate",
        json={"student_id": student["id"], "date_from": "2026-08-01T00:00:00Z", "date_to": "2026-09-08T00:00:00Z", "include_notes": True},
        headers=second_auth["headers"],
    )
    assert response.status_code == 404

def test_contact_brief_generation_forwards_only_owned_student(client, make_student, monkeypatch):
    student = make_student(guardians=[])
    captured = {}
    monkeypatch.setattr(ai_briefs, "invoke_contact_brief", lambda payload: captured.update(payload) or {"provider": "aws-strands-bedrock", "review_status": "pending", "stats": {}, "brief": {}})

    response = client.post(
        "/api/v1/ai/contact-brief/generate",
        json={"student_id": student["id"], "date_from": "2026-08-01T00:00:00Z", "date_to": "2026-09-08T00:00:00Z", "include_notes": True},
    )

    assert response.status_code == 200
    assert captured["student_id"] == student["id"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `../.venv/bin/python -m pytest tests/test_contact_brief_generation.py -q -p no:cacheprovider`

Expected: FAIL，因为现有端点固定返回 `501`。

- [ ] **Step 3: 最小实现**

```python
class ContactBriefGenerateRequest(BaseModel):
    student_id: uuid.UUID
    date_from: datetime
    date_to: datetime
    include_notes: bool = True

@ai_router.post("/contact-brief/generate")
def generate_contact_brief(payload: ContactBriefGenerateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_owned_student(db, payload.student_id, user.id)
    try:
        return invoke_contact_brief(payload.model_dump(mode="json"))
    except ContactBriefUnavailable as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
```

- [ ] **Step 4: 运行安全测试确认通过**

Run: `../.venv/bin/python -m pytest tests/test_contact_brief_generation.py tests/test_owner_authorization.py -q -p no:cacheprovider`

Expected: PASS；测试中无 Lambda / Bedrock 网络调用。

### Task 3: 启用本地 UI，并验证真实 Lambda

**Files:**
- Modify: `.env`（本地忽略文件，仅添加 provider 开关与既有 Lambda URL）
- Test: `tests/ai-provider.test.js`
- Test: `tests/api-client.test.js`

**Interfaces:**
- Local frontend config: `VITE_CONTACT_BRIEF_PROVIDER=aws-strands-bedrock`。
- Local backend config: `CONTACT_BRIEF_ENDPOINT` is set only in ignored `backend/.env` from the already-known Lambda Function URL; its value is never recorded in this plan or source.
- Browser continues to call `http://127.0.0.1:8000/api/v1/ai/contact-brief/generate`.

- [ ] **Step 1: 运行既有前端路由测试**

The existing `tests/api-client.test.js` test named `invokeContactBrief posts to the AI contact brief endpoint` already asserts the complete required behavior:

```javascript
assert.equal(requests[0].url, 'http://localhost:8000/api/v1/ai/contact-brief/generate');
assert.equal(requests[0].init.method, 'POST');
```

- [ ] **Step 2: 运行前端测试确认通过**

Run: `npm test -- --test-name-pattern='Contact Brief'`

Expected: PASS；测试不访问网络。

- [ ] **Step 3: 设置仅本机配置并重启服务**

```env
# backend/.env
# Add CONTACT_BRIEF_ENDPOINT by copying the existing Function URL from the
# already-deployed Contact Brief configuration. Do not commit this value.
CONTACT_BRIEF_ENDPOINT=

# .env
VITE_CONTACT_BRIEF_PROVIDER=aws-strands-bedrock
```

Restart FastAPI and Vite. Confirm only booleans: backend endpoint configured, provider equals `aws-strands-bedrock`。

- [ ] **Step 4: 运行完整自动验证**

Run:

```bash
../.venv/bin/python -m pytest tests -q -p no:cacheprovider
npm test
npm run build
```

Expected: all tests and build pass.

- [ ] **Step 5: 用户控制的真实演示验证**

在已登录的 ContactLoop UI 中打开 **Emma Johnson**，点击 **Generate summary** 一次。确认卡片出现真实内容、标记为 `Needs teacher review`，且可由当前老师批准。若 Lambda 返回错误，记录 HTTP 状态和安全错误信息；不修改 Lambda 或 AWS 配置。
