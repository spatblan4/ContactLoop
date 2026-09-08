import { readFile, writeFile } from 'node:fs/promises';

const articleFiles = [
  'docs/builder-articles/01-why-i-built-contactloop.md',
  'docs/builder-articles/02-building-contactloop.md',
  'docs/builder-articles/03-ai-and-teacher-judgment.md',
];

const groups = [
  ['accounts', '资格与账号', [
    ['account-devpost', '加入 Devpost 黑客松', '登录后点击 Join Hackathon。', false],
    ['account-representative', '确认个人或团队代表身份', '团队参赛时指定一名 Representative。', false],
    ['account-eligibility', '确认年龄与地区资格', '依据官方 Rules 核对居住地与法定成年要求。', false],
    ['account-aws', '准备 AWS 账号', '确认能访问项目使用的 AWS 服务。', false],
    ['account-builder-id', '准备 AWS Builder ID', 'Devpost 提交时需要填写。', false],
    ['account-track', '最终选择 Good Neighbor Agents', 'ContactLoop 当前定位最匹配学校与教育社区。', false],
  ]],
  ['product', '可运行产品', [
    ['product-audience', '明确教师用户与重复沟通问题', '已在产品文案、视频脚本和文章中定义。', true],
    ['product-real-call', '真实 Twilio 拨号', '你已确认端到端真实测试电话跑通。', true],
    ['product-writeback', '通话结果自动回写', 'Webhook 与同步链路已有代码和测试。', true],
    ['product-association', '事件关联学生与监护人', '联系事件模型已实现关联。', true],
    ['product-followup', '未成功联系保持为 open follow-up', 'Follow-ups 页面和领域测试已覆盖。', true],
    ['product-topics', '区分 planned 与 discussed topics', '未接通电话不会被描述成已讨论。', true],
    ['product-agent', 'Strands + Bedrock 生成 Contact Brief', 'AWS provider、三个窄工具与结构化输出已实现。', true],
    ['product-review', '教师编辑、审核与批准', 'Needs Teacher Review 到 Teacher Approved 流程已实现。', true],
    ['product-errors', '基本错误处理', '通话、AI provider、网络与语音错误均有处理或测试。', true],
  ]],
  ['technical', '技术材料', [
    ['tech-strands', '核心流程使用 Strands Agents SDK', 'Agent 调用统计、笔记/主题与跟进工具。', true],
    ['tech-architecture', '准备架构图', '已有 docs/architecture.html。', true],
    ['tech-services', '记录 AWS 与第三方服务职责', 'Strands、Bedrock、Twilio、Supabase 边界已有说明。', true],
    ['tech-secrets', '服务凭据保留在服务端', '浏览器只调用 provider endpoint。', true],
    ['tech-setup', '完成可复现安装与测试说明', 'README 已记录环境、安装、运行、测试与构建步骤。', true],
    ['tech-agentcore', '决定是否部署 Amazon Bedrock AgentCore', '非硬性要求，但可增强技术实现评分。', false],
    ['tech-live-demo', '最终验证公开 Live Demo', '使用无痕窗口走完整评委路径。', false],
  ]],
  ['repository', '公开仓库', [
    ['repo-public', '确认 GitHub 仓库公开', '用退出登录的浏览器验证可访问。', false],
    ['repo-source', '完整源代码与必要资源', '源代码、Supabase functions 和 AWS provider 已在仓库中。', true],
    ['repo-readme', '完成英文 README 与运行说明', 'README 已覆盖产品、架构、设置、测试与安全边界。', true],
    ['repo-license', '添加 MIT License', 'LICENSE 已使用 ContactLoop contributors 版权声明。', true],
    ['repo-disclosure', '披露赛前已有工作', 'README 已区分赛前构想与 8 月 26 日起的仓库实现。', true],
    ['repo-privacy', '扫描 tracked files 的凭据与隐私风险', '结果已记录在 docs/submission/privacy-scan.md。', true],
  ]],
  ['devpost', 'Devpost 提交', [
    ['devpost-description', '完成英文项目介绍草稿', 'docs/devpost-submission.md 已按 Devpost 常用字段成稿。', true],
    ['devpost-pitch', '完成项目名与一句话 Pitch', 'ContactLoop 定位已与 README 和文章统一。', true],
    ['devpost-media', '上传 Logo、封面与截图', '只使用无真实个人信息的 Demo 数据。', false],
    ['devpost-repo', '添加公开仓库链接', '确认评委无需登录即可查看。', false],
    ['devpost-architecture', '上传架构图', '图中文字保持英文且可读。', false],
    ['devpost-builder', '填写 AWS Builder ID', '提交页必填信息。', false],
    ['devpost-track', '选择最终赛道', '建议 Good Neighbor Agents。', false],
    ['devpost-demo', '添加 Live Demo 与测试说明', '如需登录，提供免费测试凭据。', false],
    ['devpost-articles', '添加三篇 Builder 文章链接', '文章发布并验证后再填写。', false],
    ['devpost-submit', '正式提交并保存确认页', '截止：2026-09-14 5:00 PM PDT。', false],
  ]],
  ['video', 'Demo 视频', [
    ['video-script', '完成英文脚本初稿', '现有精简脚本约 4 分钟。', true],
    ['video-record', '录制真实端到端工作流', '展示拨号、回写、Agent、Brief 和审核。', false],
    ['video-story', '讲清问题、用户与重要性', '前三十秒建立教师的真实痛点。', false],
    ['video-tech', '展示 Strands 工具与 AWS 架构', '让评委看见非简单聊天机器人的实现。', false],
    ['video-review', '展示教师审核与批准', '突出 human-in-the-loop。', false],
    ['video-duration', '成片不超过 5 分钟', '以导出文件的实际时长为准。', false],
    ['video-upload', '公开上传 YouTube 或 Vimeo', '使用退出登录窗口确认播放权限。', false],
    ['video-devpost', '把视频链接添加到 Devpost', '提交预览中再次测试播放。', false],
  ]],
  ['articles', 'Builder 加分文章', [
    ['article-one', '第一篇创始故事完成', '827 词；采用克制披露版本。', true],
    ['article-two', '第二篇技术构建完成', '1,218 词；覆盖 Strands、Bedrock、Twilio、Supabase。', true],
    ['article-three', '第三篇可信 AI 原则完成', '937 词；突出教师判断与事实边界。', true],
    ['article-factcheck', '三篇文章完成事实核验', '已建立 evidence matrix 并扫描敏感披露。', true],
    ['article-images', '选择隐私安全截图', '不得出现真实学生、电话或服务信息。', false],
    ['article-publish', '在 AWS Builder 公开发布三篇', '建议 9 月 13 日集中发布。', false],
    ['article-verify', '退出登录验证三个公开链接', '检查标题、图片、代码块和链接。', false],
    ['article-link', '将三个链接填入 Devpost', '发布后立即填写，不留到最后一小时。', false],
  ]],
];

const escapeHtml = value => value.replace(/[&<>]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[char]);
const inline = value => escapeHtml(value)
  .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  .replace(/`(.+?)`/g, '<code>$1</code>')
  .replace(/\[(.+?)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2">$1</a>');

function markdownToHtml(markdown) {
  const lines = markdown.split('\n').slice(1);
  const output = [];
  let paragraph = [];
  let list = false;
  let code = false;
  let codeLines = [];
  const flushParagraph = () => {
    if (paragraph.length) output.push(`<p>${inline(paragraph.join(' '))}</p>`);
    paragraph = [];
  };
  const closeList = () => { if (list) output.push('</ol>'); list = false; };
  for (const line of lines) {
    if (line.startsWith('```')) {
      flushParagraph(); closeList();
      if (code) { output.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`); codeLines = []; }
      code = !code; continue;
    }
    if (code) { codeLines.push(line); continue; }
    if (!line.trim()) { flushParagraph(); closeList(); continue; }
    const heading = line.match(/^(#{2,3})\s+(.+)$/);
    if (heading) { flushParagraph(); closeList(); const level = heading[1].length; output.push(`<h${level}>${inline(heading[2])}</h${level}>`); continue; }
    const quote = line.match(/^>\s+(.+)$/);
    if (quote) { flushParagraph(); closeList(); output.push(`<blockquote>${inline(quote[1])}</blockquote>`); continue; }
    const item = line.match(/^\d+\.\s+(.+)$/);
    if (item) { flushParagraph(); if (!list) { output.push('<ol>'); list = true; } output.push(`<li>${inline(item[1])}</li>`); continue; }
    paragraph.push(line.trim());
  }
  flushParagraph(); closeList();
  return output.join('\n');
}

const articleData = await Promise.all(articleFiles.map(async path => {
  const markdown = await readFile(path, 'utf8');
  const [titleLine] = markdown.split('\n');
  return { title: titleLine.replace(/^#\s+/, ''), html: markdownToHtml(markdown) };
}));
const wordCounts = [827, 1218, 937];

const checklistHtml = groups.map(([key, name, items]) => `<section class="group" data-check-group="${key}"><header><h3>${name}</h3><span class="group-count"></span></header><ul>${items.map(([id, label, note, checked]) => `<li><input id="${id}" data-check-id="${id}" data-default-checked="${checked}" type="checkbox"${checked ? ' checked' : ''}><div><label for="${id}">${label}</label><small>${note}</small><span class="state">${checked ? '已核验' : '待完成'}</span></div></li>`).join('')}</ul></section>`).join('\n');
const articlesHtml = articleData.map((article, index) => `<details class="article-card"><summary><span class="number">0${index + 1}</span><span><b>${article.title}</b><small>${wordCounts[index].toLocaleString()} words · Draft ready</small></span></summary><div class="article-inner"><div class="article-actions"><span class="copy-status" role="status"></span><button type="button" class="button dark" data-copy-source="article-${index + 1}">复制全文</button></div><article class="article-content" id="article-${index + 1}"><h2 class="sr-only">${article.title}</h2>${article.html}</article></div></details>`).join('\n');

const html = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%23173c32'/%3E%3Cpath d='M9 9h14v4H13v6h10v4H9z' fill='%23c9f25f'/%3E%3C/svg%3E"><title>ContactLoop · 黑客松最终交付中心</title>
<style>
:root{--paper:#f1ecda;--card:#fffdf5;--ink:#173c32;--muted:#65766e;--line:#aebbae;--acid:#c9f25f;--amber:#dfa039;--shadow:#173c3217;--serif:Georgia,"Times New Roman",serif;--sans:"Trebuchet MS","Avenir Next",sans-serif;--mono:"SFMono-Regular",Consolas,monospace}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--paper);background-image:linear-gradient(#173c3208 1px,transparent 1px),linear-gradient(90deg,#173c3208 1px,transparent 1px),radial-gradient(circle at 8% 2%,#c9f25f55,transparent 27rem);background-size:24px 24px,24px 24px,auto;font:16px/1.55 var(--sans)}button,input{font:inherit}button{cursor:pointer}a{color:inherit}.shell{width:min(1300px,calc(100% - 36px));margin:auto;padding:28px 0 80px}.masthead{display:grid;grid-template-columns:1fr 300px;gap:22px}.hero,.deadline,.progress,.group,.readiness,.articles{border:1px solid var(--ink);background:var(--card);box-shadow:7px 7px 0 var(--shadow)}.hero{position:relative;overflow:hidden;padding:42px}.hero:after{content:"CL";position:absolute;right:-18px;bottom:-70px;color:#173c3208;font:900 190px/1 var(--serif)}.kicker{color:#6c8c16;font:800 11px var(--mono);letter-spacing:.16em;text-transform:uppercase}h1{position:relative;z-index:1;margin:14px 0 12px;font:700 clamp(42px,7vw,84px)/.88 var(--serif);letter-spacing:-.065em}.hero p{position:relative;z-index:1;max-width:670px;margin:0;color:var(--muted)}.deadline{display:flex;flex-direction:column;justify-content:space-between;padding:28px;background:var(--ink);color:white}.deadline strong{display:block;margin:25px 0 8px;font:700 58px/.84 var(--serif)}.deadline time{color:var(--acid);font:700 14px var(--mono)}.progress{display:grid;grid-template-columns:150px 1fr auto;gap:22px;align-items:center;margin-top:18px;padding:23px 27px}.progress-number{font:800 52px/.9 var(--serif)}.track{height:12px;margin-top:8px;border:1px solid var(--ink);background:#e2dfd1}.fill{height:100%;width:0;background:var(--acid);transition:width .2s}.muted{color:var(--muted)}.buttons{display:flex;flex-wrap:wrap;gap:8px}.button{min-height:40px;padding:9px 13px;border:1px solid var(--ink);background:var(--card);color:var(--ink);font-weight:800;box-shadow:3px 3px 0 var(--shadow)}.button:hover{transform:translate(-1px,-1px)}.button.dark{background:var(--ink);color:white}.button:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--amber);outline-offset:3px}.section-title{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:52px 0 16px}.section-title h2{margin:4px 0 0;font:700 clamp(32px,5vw,52px)/.95 var(--serif);letter-spacing:-.045em}.section-title p{max-width:470px;margin:0;color:var(--muted)}.checklist{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}.group{overflow:hidden}.group>header{display:flex;justify-content:space-between;align-items:center;padding:16px 18px;border-bottom:1px solid var(--ink)}.group h3{margin:0;font:700 21px var(--serif)}.group-count{border:1px solid var(--ink);border-radius:99px;padding:3px 8px;font:700 11px var(--mono)}.group ul{list-style:none;margin:0;padding:0}.group li{display:grid;grid-template-columns:27px 1fr;gap:11px;padding:14px 17px;border-bottom:1px dashed var(--line)}.group li:last-child{border:0}.group li:has(input:checked){background:#f5fbdc}.group input{width:20px;height:20px;margin:2px 0;accent-color:var(--ink)}.group label{font-weight:800;cursor:pointer}.group small{display:block;margin-top:3px;color:var(--muted)}.state{display:inline-block;margin-top:6px;padding:2px 7px;border-radius:99px;background:#f2dfbb;color:#6b480e;font:800 10px var(--mono);text-transform:uppercase}.group input:checked+div .state{background:#ddecaa;color:#30450d}.readiness{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-top:15px;padding:20px 24px}.readiness strong{font:700 22px var(--serif)}.readiness p{margin:3px 0 0}.badge{flex:none;border:1px solid var(--ink);padding:8px 11px;background:var(--amber);font:900 12px var(--mono);text-transform:uppercase}.badge.done{background:var(--acid)}.articles{overflow:hidden}.article-toolbar{display:flex;justify-content:space-between;align-items:center;gap:15px;padding:17px 20px;background:var(--ink);color:white}.article-toolbar p{margin:0;color:#cbd8d1}.article-toolbar .button{border-color:#94aaa0;background:transparent;color:white}.article-card{border-bottom:1px solid var(--ink)}.article-card:last-child{border:0}.article-card summary{display:grid;grid-template-columns:55px 1fr 34px;gap:17px;align-items:center;padding:22px 25px;cursor:pointer;list-style:none}.article-card summary::-webkit-details-marker{display:none}.article-card summary:after{content:"+";font:400 36px/1 var(--serif);transition:transform .2s}.article-card[open] summary:after{transform:rotate(45deg)}.number{font:800 29px var(--serif);color:#6c8c16}.article-card summary b{display:block;font:700 22px/1.18 var(--serif)}.article-card summary small{display:block;margin-top:5px;color:var(--muted);font:700 11px var(--mono);text-transform:uppercase}.article-inner{border-top:1px dashed var(--line);padding:25px clamp(18px,6vw,80px) 48px}.article-actions{display:flex;justify-content:flex-end;align-items:center;margin-bottom:20px}.copy-status{margin-right:12px;color:#607d13;font:700 12px var(--mono)}.article-content{max-width:760px;margin:auto;font:18px/1.72 var(--serif)}.article-content h2{margin:2em 0 .6em;font:700 30px/1.12 var(--serif)}.article-content h3{margin:1.7em 0 .4em;font:700 22px var(--serif)}.article-content p{margin:0 0 1.1em}.article-content blockquote{margin:1.6em 0;padding:13px 20px;border-left:6px solid #789822;background:#f1f4da;font-style:italic}.article-content pre{overflow:auto;padding:17px;background:var(--ink);color:#f0f8e8;font:13px/1.6 var(--mono)}.article-content code{font-family:var(--mono);font-size:.88em}.footer{display:flex;justify-content:space-between;margin-top:22px;color:var(--muted);font-size:12px}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@media(max-width:880px){.masthead{grid-template-columns:1fr}.deadline{min-height:220px}.checklist{grid-template-columns:1fr}.progress{grid-template-columns:120px 1fr}.progress .buttons{grid-column:1/-1}.section-title,.readiness,.article-toolbar{align-items:flex-start;flex-direction:column}}@media(max-width:560px){.shell{width:calc(100% - 20px);padding-top:10px}.hero{padding:28px 21px}.progress{grid-template-columns:1fr;padding:20px}.section-title{display:block}.section-title p{margin-top:9px}.article-card summary{grid-template-columns:38px 1fr 26px;padding:17px 13px;gap:9px}.article-card summary b{font-size:19px}.article-inner{padding:20px 14px 38px}.article-content{font-size:16px}.footer{display:block}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}@media print{body{background:white}.shell{width:100%;padding:0}.buttons,.article-actions{display:none}.hero,.deadline,.progress,.group,.readiness,.articles{box-shadow:none}.article-card{break-before:page}.article-card>summary{display:none}.article-card:not([open])>.article-inner{display:block}}
</style></head><body><main class="shell"><div class="masthead"><header class="hero"><div class="kicker">AWS Agents for Humans · Final Delivery Desk</div><h1>ContactLoop<br>交付中心</h1><p>把资格、产品、仓库、视频、Devpost 与三篇 Builder 文章放在同一张桌面上。勾选会保存在当前浏览器；默认状态只依据现有证据。</p></header><aside class="deadline"><div><div class="kicker">Submission deadline</div><strong>SEP<br>14</strong><span>不要把上传和发布留到最后一小时。</span></div><time datetime="2026-09-14T17:00:00-07:00">5:00 PM · PDT · 2026</time></aside></div>
<section class="progress" aria-labelledby="progressHeading"><div class="progress-number" id="progressPercent">0%</div><div><strong id="progressHeading">整体完成度</strong><span class="muted" id="progressCount">0 / 0 项完成</span><div class="track" aria-hidden="true"><div class="fill" id="progressFill"></div></div></div><div class="buttons"><button class="button" id="resetProgress" type="button">重置为核验状态</button><a class="button dark" href="#articles">查看三篇文章</a></div></section>
<div class="section-title"><div><div class="kicker">01 · Submission checklist</div><h2>最终交付清单</h2></div><p>绿色代表已完成且有证据；琥珀色代表仍需你在外部平台执行或确认。你可以继续手动勾选。</p></div><div class="checklist" id="checklist">${checklistHtml}</div>
<section class="readiness" aria-live="polite"><div><strong id="readinessTitle">正在核对交付状态</strong><p class="muted" id="readinessText">页面会根据勾选进度给出下一步提示。</p></div><span class="badge" id="readinessBadge">Not ready</span></section>
<div class="section-title" id="articles"><div><div class="kicker">02 · Builder article library</div><h2>三篇文章</h2></div><p>点击标题展开全文。复制按钮会复制干净的文章文本，方便粘贴到 AWS Builder 编辑器。</p></div><section class="articles" aria-label="AWS Builder 文章草稿"><header class="article-toolbar"><p>3 drafts · 2,982 words · English</p><div class="buttons"><button class="button" id="expandAll" type="button">展开全部</button><button class="button" id="collapseAll" type="button">收起全部</button></div></header>${articlesHtml}</section>
<footer class="footer"><span>ContactLoop · submission working file</span><span>状态只保存在当前浏览器 · 最后更新 2026-09-08</span></footer></main>
<script>const storageKey='contactloop-submission-center-v2',checks=[...document.querySelectorAll('[data-check-id]')];function loadSavedState(){try{const value=JSON.parse(localStorage.getItem(storageKey)||'null');if(!value||typeof value!=='object'||Array.isArray(value))return;checks.forEach(input=>{if(typeof value[input.dataset.checkId]==='boolean')input.checked=value[input.dataset.checkId]})}catch{}}function saveState(){try{localStorage.setItem(storageKey,JSON.stringify(Object.fromEntries(checks.map(input=>[input.dataset.checkId,input.checked]))))}catch{}}function updateProgress(){const done=checks.filter(input=>input.checked).length,total=checks.length,percent=Math.round(done/total*100);progressPercent.textContent=percent+'%';progressCount.textContent=done+' / '+total+' 项完成';progressFill.style.width=percent+'%';document.querySelectorAll('[data-check-group]').forEach(group=>{const items=[...group.querySelectorAll('[data-check-id]')];group.querySelector('.group-count').textContent=items.filter(input=>input.checked).length+'/'+items.length});const ready=done===total;readinessBadge.textContent=ready?'Ready to submit':'Not ready';readinessBadge.classList.toggle('done',ready);readinessTitle.textContent=ready?'所有交付项目已勾选':'还有项目需要完成';readinessText.textContent=ready?'提交前再用无痕窗口检查所有公开链接，然后保存 Devpost 确认页。':'还有 '+(total-done)+' 项未完成。优先处理视频、公开链接、文章发布和 Devpost 外部动作。'}function resetToDefaults(){if(!window.confirm('恢复为证据核验后的默认状态？你手动保存的勾选进度会被覆盖。'))return;try{localStorage.removeItem(storageKey)}catch{}checks.forEach(input=>input.checked=input.dataset.defaultChecked==='true');saveState();updateProgress()}function setAllArticles(open){document.querySelectorAll('.article-card').forEach(card=>card.open=open)}async function copyArticle(button){const status=button.previousElementSibling,text=document.getElementById(button.dataset.copySource).innerText.trim();try{if(!navigator.clipboard?.writeText)throw Error();await navigator.clipboard.writeText(text);status.textContent='已复制'}catch{try{const area=document.createElement('textarea');area.value=text;area.readOnly=true;area.style.cssText='position:fixed;opacity:0';document.body.append(area);area.select();if(!document.execCommand('copy'))throw Error();area.remove();status.textContent='已复制'}catch{status.textContent='复制失败，请手动选择文章'}}setTimeout(()=>status.textContent='',2400)}checks.forEach(input=>input.addEventListener('change',()=>{saveState();updateProgress()}));document.querySelector('#resetProgress').addEventListener('click',resetToDefaults);document.querySelector('#expandAll').addEventListener('click',()=>setAllArticles(true));document.querySelector('#collapseAll').addEventListener('click',()=>setAllArticles(false));document.querySelectorAll('[data-copy-source]').forEach(button=>button.addEventListener('click',()=>copyArticle(button)));loadSavedState();updateProgress();</script></body></html>`;

await writeFile('docs/contactloop-submission-center.html', html);
await writeFile('public/contactloop-submission-center.html', html);
