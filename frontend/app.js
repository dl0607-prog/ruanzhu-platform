/* 软著工场 - 前端工作台（原生 JS，无构建依赖） */
const API = location.origin;
const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

/* ---------------- SVG 图标体系（线性风格，currentColor） ---------------- */
const ICONS = {
  home: '<path d="M3 10.8 12 3l9 7.8"/><path d="M5 9.6V21h14V9.6"/><path d="M9.5 21v-6.5h5V21"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  folder: '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5h4L12 7.5h6.5A2.5 2.5 0 0 1 21 10v8a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 18z"/>',
  code: '<path d="m8 7-5 5 5 5M16 7l5 5-5 5"/>',
  sparkles: '<path d="M12 3.5 13.9 9l5.5 1.9-5.5 1.9L12 18.3l-1.9-5.5-5.5-1.9L10.1 9z"/><path d="m18.8 15.8.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/>',
  shield: '<path d="M12 3l7.5 3v5.2c0 4.6-3.1 7.7-7.5 9.3-4.4-1.6-7.5-4.7-7.5-9.3V6z"/><path d="m8.8 11.8 2.2 2.2 4.4-4.5"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  download: '<path d="M12 3v12m0 0 4.5-4.5M12 15l-4.5-4.5"/><path d="M4 21h16"/>',
  upload: '<path d="M12 15V3m0 0 4.5 4.5M12 3 7.5 7.5"/><path d="M4 21h16"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5V5M12 19v2.5M2.5 12H5M19 12h2.5M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8"/>',
  moon: '<path d="M20.6 13.2A8.5 8.5 0 1 1 10.8 3.4a7 7 0 0 0 9.8 9.8z"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  trash: '<path d="M4 7h16"/><path d="M9.5 7V4.5h5V7"/><path d="m6 7 1 13.5h10L18 7"/><path d="M10 11v6M14 11v6"/>',
  eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
  clipboard: '<rect x="5" y="4.5" width="14" height="17" rx="2"/><path d="M9 4.5V3h6v1.5"/><path d="M9 11.5h6M9 15.5h4"/>',
  bot: '<rect x="4.5" y="8" width="15" height="11.5" rx="2.5"/><path d="M12 8V4.8"/><circle cx="12" cy="3.8" r="1.1"/><path d="M9 13.2h.01M15 13.2h.01"/><path d="M9.5 16.7h5"/>',
  archive: '<rect x="3" y="4" width="18" height="4.5" rx="1"/><path d="M5 8.5V19a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19V8.5"/><path d="M10 12.5h4"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v5h-5"/>',
  alert: '<path d="M10.3 4.1 2.5 17.5a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 4.1a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4.5"/><path d="M12 17.4h.01"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="m8.2 12.3 2.6 2.6 5-5.2"/>',
  filetext: '<path d="M14 2.5H6.5A1.5 1.5 0 0 0 5 4v16a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 20V8z"/><path d="M14 2.5V8h5"/><path d="M9 13h6M9 17h4"/>',
  filecode: '<path d="M14 2.5H6.5A1.5 1.5 0 0 0 5 4v16a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 20V8z"/><path d="M14 2.5V8h5"/><path d="m10 12.5-2 2.3 2 2.3M14 12.5l2 2.3-2 2.3"/>',
  layers: '<path d="M12 2.5 2.5 8 12 13.5 21.5 8z"/><path d="m2.5 13 9.5 5.5L21.5 13"/>',
  listcheck: '<path d="M4 6h9M4 12h9M4 18h6"/><path d="m15.5 17 2 2 3.5-4"/>',
  camera: '<path d="M3 19V9a1.5 1.5 0 0 1 1.5-1.5H7l1.8-2.5h6.4L17 7.5h2.5A1.5 1.5 0 0 1 21 9v10z"/><circle cx="12" cy="13.5" r="3.2"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 1.8"/>',
  folderopen: '<path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h4l2 2.5h8A1.5 1.5 0 0 1 20 9v1H6.8a2 2 0 0 0-1.9 1.4L3 16.5z"/><path d="m3.4 16 1.6-5a2 2 0 0 1 1.9-1.4H21a1 1 0 0 1 1 1.3l-1.6 5.4A2 2 0 0 1 18.5 18H5a2 2 0 0 1-1.9-1.4z"/>',
};

function icon(name, size) {
  const s = size || 16;
  const body = ICONS[name] || ICONS.filetext;
  return `<svg viewBox="0 0 24 24" width="${s}" height="${s}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
}

function hydrateIcons(root) {
  $$("[data-icon]", root).forEach(el => { el.innerHTML = icon(el.dataset.icon); });
}

/* ---------------- 全局状态 ---------------- */
const state = {
  projects: [],
  currentId: null,
  tab: "info",
  health: null,
};

const DOC_META = {
  analysis: { name: "代码结构分析", ico: "code" },
  manual: { name: "操作说明书", ico: "book" },
  design: { name: "设计说明书", ico: "filetext" },
  form: { name: "申请表预填", ico: "clipboard" },
  declaration: { name: "AI 使用声明", ico: "bot" },
  evidence: { name: "开发过程记录", ico: "archive" },
};

const TABS = [
  ["info", "基本信息", "listcheck"],
  ["code", "源代码", "filecode"],
  ["gen", "材料生成", "sparkles"],
  ["review", "合规审查", "shield"],
  ["kb", "驳回知识库", "refresh"],
  ["export", "导出下载", "download"],
];

/* 申请状态流转（"批发"管理多件申请） */
const STATUS_META = {
  draft:      { label: "草稿",     color: "gray" },
  ready:      { label: "材料就绪", color: "blue" },
  submitted:  { label: "已提交",   color: "orange" },
  correction: { label: "补正中",   color: "red" },
  registered: { label: "已登记",   color: "green" },
  rejected:   { label: "已驳回",   color: "red" },
};

/* ---------------- 基础工具 ---------------- */
function toast(msg, isErr) {
  const t = $("#toast");
  t.textContent = "";
  const icoBox = document.createElement("span");
  icoBox.className = "ico";
  icoBox.innerHTML = icon(isErr ? "alert" : "check");   // 静态 SVG，无用户数据
  const txt = document.createElement("span");
  txt.textContent = msg;                                 // 文本节点，杜绝注入
  t.append(icoBox, txt);
  t.className = "toast" + (isErr ? " err" : "");
  t.style.display = "flex";
  clearTimeout(t._timer);
  t._timer = setTimeout(() => (t.style.display = "none"), isErr ? 6000 : 3200);
}

function setPage(title, crumb) {
  $("#page-title").textContent = title;
  $("#page-crumb").textContent = crumb;
}

async function api(path, opts = {}) {
  if (!path.startsWith("/api/")) throw new Error("非法的 API 路径");
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    let detail = res.status;
    try { detail = (await res.json()).detail || detail; } catch (e) {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ---------------- 极简 Markdown 渲染 ---------------- */
function md2html(md) {
  const lines = String(md || "").split("\n");
  let html = "", inList = false, inTable = false;
  const closeList = () => { if (inList) { html += "</ul>"; inList = false; } };
  const closeTable = () => { if (inTable) { html += "</tbody></table>"; inTable = false; } };
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) { closeList(); closeTable(); continue; }
    if (line.startsWith("|")) {
      const cells = line.split("|").slice(1, -1).map(c => c.trim());
      if (cells.every(c => /^:?-{2,}:?$/.test(c))) continue;
      if (!inTable) { closeList(); html += "<table><tbody>"; inTable = true; }
      html += "<tr>" + cells.map(c => "<td>" + inline(c) + "</td>").join("") + "</tr>";
      continue;
    }
    closeTable();
    const shot = line.match(/^【截图占位[:：](.+?)】$/);
    if (shot) { closeList(); html += `<div class="shot">${icon("camera")} 截图占位：${esc(shot[1])}</div>`; continue; }
    if (/^###\s/.test(line)) { closeList(); html += `<h3>${inline(line.slice(4))}</h3>`; continue; }
    if (/^##\s/.test(line)) { closeList(); html += `<h2>${inline(line.slice(3))}</h2>`; continue; }
    if (/^#\s/.test(line)) { closeList(); html += `<h1>${inline(line.slice(2))}</h1>`; continue; }
    if (/^[-*+]\s/.test(line)) {
      if (!inList) { html += "<ul>"; inList = true; }
      html += `<li>${inline(line.slice(2))}</li>`;
      continue;
    }
    closeList();
    html += `<p>${inline(line)}</p>`;
  }
  closeList(); closeTable();
  return html;
  function inline(s) {
    return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  }
}

/* ---------------- SSE 读取 ---------------- */
async function consumeSSE(res, onEvent) {
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, idx); buf = buf.slice(idx + 2);
      if (chunk.startsWith("data: ")) {
        try { onEvent(JSON.parse(chunk.slice(6))); } catch (e) {}
      }
    }
  }
}

/* ---------------- 侧边栏与路由 ---------------- */
async function refreshProjects() {
  const d = await api("/api/projects");
  state.projects = d.projects;
  renderSidebar();
}

function renderSidebar() {
  const list = $("#proj-list");
  if (!state.projects.length) {
    list.innerHTML = `<div class="proj-empty">暂无申请项目</div>`;
    return;
  }
  list.innerHTML = state.projects.map(p => `
    <div class="proj-item ${p.id === state.currentId ? "active" : ""}" data-id="${p.id}" title="${esc(p.full_name || "")}">
      <span class="pname">${esc(p.full_name || "未命名")}</span>
      <span class="v">${esc(p.version || "")}</span>
    </div>`).join("");
  $$(".proj-item", list).forEach(el => el.onclick = () => openProject(+el.dataset.id));
}

function openProject(id) {
  state.currentId = id;
  state.tab = "info";
  renderSidebar();
  location.hash = "#/project/" + id;
  loadProjectView();
}

async function loadProjectView() {
  if (!state.currentId) return showDashboard();
  let p;
  try { p = await api("/api/projects/" + state.currentId); }
  catch (e) { state.currentId = null; return showDashboard(); }
  setPage(`${p.full_name} ${p.version}`, "项目工作台 · 生成 → 审查 → 导出");
  $("#main-area").innerHTML = projectViewHTML(p);
  hydrateIcons($("#main-area"));
  bindProjectEvents(p);
  renderTab(p);
}

function currentProject() { return state.projects.find(p => p.id === state.currentId); }

/* ---------------- 仪表盘 ---------------- */
async function showDashboard() {
  location.hash = "#/";
  state.currentId = null;
  setPage("项目总览", "一站式生成能通过审查的软著申请材料");
  renderSidebar();
  let rules = [];
  try { rules = (await api("/api/kb/rules")).rules; } catch (e) {}
  const ps = state.projects;
  const llmOn = !!(state.health && state.health.llm_configured);
  const docsDone = p => Object.keys(p.docs || {}).length;
  $("#main-area").innerHTML = `
    <div class="hero">
      <h2>把 AI 写的代码，变成能通过审查的软著申请</h2>
      <p>导入源代码后自动生成全套材料：源程序鉴别材料（每页50行 · 前30后30截取）、操作/设计说明书、申请表预填（功能描述≥500字）、AI 声明与开发过程记录；内置 2026-03-15 新规合规预检，被打回还能把问题沉淀进知识库，下次自动规避。</p>
      <div class="hero-actions">
        <button class="btn-hero" id="btn-hero-new">${icon("plus", 15)} 新建软著申请</button>
        <button class="btn-hero ghost" id="btn-hero-how">${icon("arrow", 15)} 了解工作流程</button>
      </div>
    </div>
    <div class="stat-row">
      <div class="stat"><div class="stat-ico blue">${icon("folder", 19)}</div><div><div class="num">${ps.length}</div><div class="lbl">申请项目</div></div></div>
      <div class="stat"><div class="stat-ico purple">${icon("shield", 19)}</div><div><div class="num">${rules.length}</div><div class="lbl">规避规则</div></div></div>
      <div class="stat"><div class="stat-ico orange">${icon("refresh", 19)}</div><div><div class="num">${rules.filter(r => r.hit_count > 0).length}</div><div class="lbl">已命中规则</div></div></div>
      <div class="stat"><div class="stat-ico ${llmOn ? "green" : "orange"}">${icon("sparkles", 19)}</div><div><div class="num" style="font-size:17px;padding-top:3px;">${llmOn ? esc((state.health.llm_model || "").slice(0, 16)) : "未配置"}</div><div class="lbl">AI 引擎</div></div></div>
    </div>
    <div class="steps">
      <div class="step-card"><div class="s-head"><span class="s-no">1</span><span class="s-title">${icon("filecode", 15)} 导入代码</span></div>
        <div class="s-desc">粘贴或上传（zip）AI 项目的源码，自动剔除依赖目录、去空行、按每页 50 行排版。</div></div>
      <div class="step-card"><div class="s-head"><span class="s-no">2</span><span class="s-title">${icon("sparkles", 15)} AI 生成全套</span></div>
        <div class="s-desc">分析代码模块，逐章节生成说明书、申请表（功能≥500字）、AI 声明、开发过程记录。</div></div>
      <div class="step-card"><div class="s-head"><span class="s-no">3</span><span class="s-title">${icon("shield", 15)} 提交前预检</span></div>
        <div class="s-desc">三重一致性、名称版本格式、AI 痕迹词、材料齐备等硬校验，blocker 清零再提交。</div></div>
      <div class="step-card"><div class="s-head"><span class="s-no">4</span><span class="s-title">${icon("refresh", 15)} 驳回回流</span></div>
        <div class="s-desc">把补正/驳回通知贴进来，AI 归因沉淀为规避规则，之后生成与审查自动生效。</div></div>
    </div>
    <div class="card">
      <h3>${icon("folderopen", 16)} 我的申请项目 <span class="hint">在左侧选择项目进入工作台</span></h3>
      ${ps.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>软件名称</th><th>版本</th><th>状态</th><th>开发方式</th><th>代码行数</th><th>材料进度</th><th>创建时间</th><th></th></tr></thead><tbody>
        ${ps.map(p => { const sm = STATUS_META[p.status] || STATUS_META.draft; return `<tr>
          <td><a href="#/project/${p.id}" onclick="openProject(${p.id});return false;">${esc(p.full_name)}</a></td>
          <td><span class="tag blue">${esc(p.version)}</span></td>
          <td><span class="tag ${sm.color}">${sm.label}</span></td>
          <td>${esc(p.dev_type)}</td><td>${(p.code_lines_total || 0).toLocaleString()}</td>
          <td><span class="pbar"><i style="width:${Math.round(docsDone(p) / 6 * 100)}%"></i></span>${docsDone(p)} / 6</td>
          <td class="muted">${esc((p.created_at || "").slice(0, 10))}</td>
          <td><button class="btn btn-danger-ghost btn-sm" data-del="${p.id}">${icon("trash", 13)} 删除</button></td>
        </tr>`; }).join("")}</tbody></table></div>`
      : `<div class="empty"><div class="big">${icon("folderopen", 46)}</div>还没有申请项目。<br>点击「新建申请」，填写软件信息、导入 AI 生成的源代码，<br>平台将一站式生成软著申请全套材料并预检合规。</div>`}
    </div>`;
  hydrateIcons($("#main-area"));
  const newBtns = [["#btn-hero-new"], ["#btn-new"]];
  newBtns.forEach(([sel]) => { const b = $(sel); if (b) b.onclick = () => openProjectModal(null); });
  const how = $("#btn-hero-how");
  if (how) how.onclick = () => { const el = $(".steps"); if (el) el.scrollIntoView({ behavior: "smooth", block: "center" }); };
  $$("[data-del]").forEach(b => b.onclick = async () => {
    if (!confirm("确认删除该申请项目及其全部材料？")) return;
    await api("/api/projects/" + b.dataset.del, { method: "DELETE" });
    toast("已删除");
    refreshProjects().then(showDashboard);
  });
}

/* ---------------- 新建/编辑项目弹窗 ---------------- */
function openProjectModal(p) {
  const m = document.createElement("div");
  m.className = "modal-mask";
  m.innerHTML = `<div class="modal" style="width:660px;">
    <div class="modal-head"><h3>${p ? "编辑项目信息" : "新建软著申请"}</h3><button class="modal-close">${icon("x")}</button></div>
    <div class="modal-body">
      <div class="form-grid">
        <div class="field full"><label><b>*</b>软件全称（建议以 系统/软件/平台 结尾，禁用"中国/国家"等词）</label>
          <input id="f-full" placeholder="如：企业数据智能同步系统" value="${esc(p ? p.full_name : "")}"></div>
        <div class="field"><label>软件简称（可选）</label><input id="f-short" value="${esc(p ? p.short_name : "")}"></div>
        <div class="field"><label>版本号（V1.0 格式）</label><input id="f-ver" value="${esc(p ? p.version : "V1.0")}"></div>
        <div class="field"><label>开发完成日期</label><input type="date" id="f-comp" value="${esc(p ? p.completion_date : "")}"></div>
        <div class="field"><label>首次发表日期（未发表留空）</label><input id="f-pub" placeholder="未发表" value="${esc(p ? p.publish_date : "")}"></div>
        <div class="field"><label>开发方式</label><select id="f-dev">
          ${["独立开发", "合作开发", "委托开发"].map(x => `<option ${p && p.dev_type === x ? "selected" : ""}>${x}</option>`).join("")}</select></div>
        <div class="field"><label>著作权人（名称）</label><input id="f-owner" value="${esc(p ? p.owner_name : "")}"></div>
        <div class="field"><label>主体类型</label><select id="f-otype">
          <option ${p && p.owner_type === "企业" ? "selected" : ""}>企业</option>
          <option ${!p || p.owner_type === "个人" ? "selected" : ""}>个人</option></select></div>
        <div class="field"><label>AI 使用情况（决定 AI 声明口径）</label><select id="f-ai">
          <option value="ai_assisted" ${!p || p.ai_usage === "ai_assisted" ? "selected" : ""}>AI 辅助开发 + 人工实质性修改（推荐口径）</option>
          <option value="ai_heavy" ${p && p.ai_usage === "ai_heavy" ? "selected" : ""}>AI 参与较多，人工做了核心设计与重构</option></select></div>
        <div class="field"><label>技术栈（可选）</label><input id="f-tech" placeholder="如：Python FastAPI + Vue3" value="${esc(p ? p.tech_stack : "")}"></div>
        <div class="field full"><label>主要功能描述（给 AI 的功能说明，越具体生成质量越高）</label>
          <textarea id="f-func" placeholder="例如：这是一个把电商订单从多个平台同步到本地 ERP 的工具，包含订单拉取、字段映射、冲突处理、日志报表四个模块…">${esc(p ? p.main_functions : "")}</textarea></div>
        <div class="field full"><label>Git 提交记录（可选，粘贴 git log --oneline 用于过程证据）</label>
          <textarea id="f-git" style="min-height:70px;" placeholder="a1b2c3d 初版订单拉取模块&#10;e4f5g6h 字段映射与冲突处理">${esc(p ? p.git_log : "")}</textarea></div>
      </div>
      <div class="row mt" style="justify-content:flex-end;">
        <button class="btn btn-ghost" id="m-cancel">取消</button>
        <button class="btn btn-primary" id="m-save">${p ? "保存修改" : "创建并进入工作台"}</button>
      </div>
    </div></div>`;
  document.body.appendChild(m);
  $(".modal-close", m).onclick = () => m.remove();
  $("#m-cancel", m).onclick = () => m.remove();
  m.onclick = e => { if (e.target === m) m.remove(); };
  $("#m-save", m).onclick = async () => {
    const body = {
      full_name: $("#f-full", m).value.trim(),
      short_name: $("#f-short", m).value.trim(),
      version: $("#f-ver", m).value.trim() || "V1.0",
      completion_date: $("#f-comp", m).value,
      publish_date: $("#f-pub", m).value.trim(),
      dev_type: $("#f-dev", m).value,
      owner_name: $("#f-owner", m).value.trim(),
      owner_type: $("#f-otype", m).value,
      main_functions: $("#f-func", m).value.trim(),
      tech_stack: $("#f-tech", m).value.trim(),
      ai_usage: $("#f-ai", m).value,
      git_log: $("#f-git", m).value.trim(),
    };
    if (!body.full_name) return toast("软件全称不能为空", true);
    try {
      if (p) { await api("/api/projects/" + p.id, { method: "PUT", body }); toast("已保存"); m.remove(); refreshProjects().then(loadProjectView); }
      else { const r = await api("/api/projects", { method: "POST", body }); toast("项目已创建"); m.remove(); await refreshProjects(); openProject(r.id); }
    } catch (e) { toast(e.message, true); }
  };
  setTimeout(() => $("#f-full", m).focus(), 60);
}

/* ---------------- 项目工作台 ---------------- */
function projectViewHTML(p) {
  const sm = STATUS_META[p.status] || STATUS_META.draft;
  return `
  <div class="row spread" style="margin-bottom:14px;">
    <div class="row"><span class="tag ${sm.color}">${sm.label}</span>
      <span class="muted">申请状态 · 流转：草稿 → 材料就绪 → 已提交 → 补正中 / 已登记</span></div>
    <select id="status-select" class="btn btn-ghost" style="padding:7px 12px;">
      ${Object.entries(STATUS_META).map(([k, v]) =>
        `<option value="${k}" ${p.status === k ? "selected" : ""}>${v.label}</option>`).join("")}
    </select>
  </div>
  <div class="tabs">${TABS.map(([k, n, ic]) => `<div class="tab ${state.tab === k ? "active" : ""}" data-tab="${k}">${icon(ic, 14.5)}${n}</div>`).join("")}</div>
  <div id="tab-body"></div>
  <input type="file" id="hidden-file" multiple style="display:none;" accept=".py,.js,.ts,.vue,.java,.go,.rs,.c,.cpp,.h,.cs,.php,.rb,.kt,.swift,.sql,.sh,.html,.css,.json,.yaml,.yml,.xml,.zip">`;
}

function bindProjectEvents(p) {
  $$(".tab").forEach(t => t.onclick = () => { state.tab = t.dataset.tab; loadProjectView(); });
  const statusSel = $("#status-select");
  if (statusSel) statusSel.onchange = async () => {
    try {
      await api(`/api/projects/${p.id}/status`, { method: "PATCH", body: { status: statusSel.value } });
      p.status = statusSel.value;
      toast("状态已更新");
      refreshProjects();
    } catch (e) { toast(e.message, true); statusSel.value = p.status || "draft"; }
  };
  $("#hidden-file").onchange = async e => {
    const fs = e.target.files;
    if (!fs.length) return;
    const fd = new FormData();
    for (const f of fs) fd.append("files", f);
    toast("正在解析上传…");
    const res = await fetch(`${API}/api/projects/${p.id}/code/upload`, { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) return toast(data.detail || "上传失败", true);
    toast(`已导入 ${data.files_stored} 个文件，共 ${data.total_lines} 行 → 将生成 ${data.pages_submitted} 页源代码文档`);
    refreshProjects().then(() => { state.tab = "code"; loadProjectView(); });
  };
}

function renderTab(p) {
  const body = $("#tab-body");
  ({ info: tabInfo, code: tabCode, gen: tabGen, review: tabReview, kb: tabKB, export: tabExport }[state.tab] || tabInfo)(p, body);
}

/* ---- Tab: 基本信息 ---- */
function tabInfo(p, body) {
  body.innerHTML = `
  <div class="card">
    <h3>${icon("listcheck", 16)} 项目信息 <span class="hint">名称/版本修改后请重新生成材料，保证三重一致性</span></h3>
    <div class="form-grid">
      <div class="field full"><label><b>*</b>软件全称</label><input id="e-full" value="${esc(p.full_name)}"></div>
      <div class="field"><label>软件简称</label><input id="e-short" value="${esc(p.short_name)}"></div>
      <div class="field"><label>版本号</label><input id="e-ver" value="${esc(p.version)}"></div>
      <div class="field"><label>开发完成日期</label><input type="date" id="e-comp" value="${esc(p.completion_date)}"></div>
      <div class="field"><label>首次发表日期</label><input id="e-pub" value="${esc(p.publish_date)}"></div>
      <div class="field"><label>开发方式</label><select id="e-dev">${["独立开发", "合作开发", "委托开发"].map(x => `<option ${p.dev_type === x ? "selected" : ""}>${x}</option>`).join("")}</select></div>
      <div class="field"><label>著作权人</label><input id="e-owner" value="${esc(p.owner_name)}"></div>
      <div class="field"><label>技术栈</label><input id="e-tech" value="${esc(p.tech_stack)}"></div>
      <div class="field full"><label>主要功能描述</label><textarea id="e-func">${esc(p.main_functions)}</textarea></div>
      <div class="field full"><label>AI 使用情况</label><select id="e-ai">
        <option value="ai_assisted" ${p.ai_usage === "ai_assisted" ? "selected" : ""}>AI 辅助开发 + 人工实质性修改</option>
        <option value="ai_heavy" ${p.ai_usage === "ai_heavy" ? "selected" : ""}>AI 参与较多，人工核心设计重构</option></select></div>
      <div class="field full"><label>Git 提交记录（过程证据）</label><textarea id="e-git" style="min-height:80px;">${esc(p.git_log)}</textarea></div>
    </div>
    <div class="row mt" style="justify-content:flex-end;"><button class="btn btn-primary" id="e-save">保存</button>
    <button class="btn btn-ghost" id="e-edit2">在弹窗中完善</button></div>
  </div>`;
  $("#e-save").onclick = async () => {
    await api("/api/projects/" + p.id, { method: "PUT", body: {
      full_name: $("#e-full").value.trim(), short_name: $("#e-short").value.trim(),
      version: $("#e-ver").value.trim(), completion_date: $("#e-comp").value,
      publish_date: $("#e-pub").value.trim(), dev_type: $("#e-dev").value,
      owner_name: $("#e-owner").value.trim(), main_functions: $("#e-func").value.trim(),
      tech_stack: $("#e-tech").value.trim(), ai_usage: $("#e-ai").value, git_log: $("#e-git").value.trim(),
    }});
    toast("已保存"); refreshProjects().then(loadProjectView);
  };
  $("#e-edit2").onclick = () => openProjectModal(p);
}

/* ---- Tab: 源代码 ---- */
async function tabCode(p, body) {
  body.innerHTML = `
  <div class="card">
    <h3>${icon("upload", 16)} 导入源代码 <span class="hint">粘贴或上传 AI 生成的项目源码（支持多文件 / zip 包）</span></h3>
    <div class="field"><textarea id="paste-code" style="min-height:170px;font-family:var(--font-mono);font-size:12px;" placeholder="把源代码粘贴到这里（会作为一个文件导入；多文件建议打包 zip 上传）"></textarea></div>
    <div class="row mt">
      <button class="btn btn-primary" id="btn-paste">${icon("code", 15)} 导入粘贴的代码</button>
      <button class="btn btn-ghost" id="btn-upload">${icon("upload", 15)} 上传文件 / zip 包</button>
      <span class="muted">导入时自动：剔除依赖目录、去空行、统一缩进、按每页50行分页</span>
    </div>
  </div>
  <div class="card"><h3>${icon("filecode", 16)} 代码概况 <span class="hint">对应源程序鉴别材料</span></h3><div id="code-stats"><div class="empty">加载中…</div></div></div>`;
  $("#btn-paste").onclick = async () => {
    const text = $("#paste-code").value;
    if (!text.trim()) return toast("请先粘贴代码", true);
    try {
      const r = await api(`/api/projects/${p.id}/code`, { method: "POST", body: { files: [{ filename: "pasted_code.txt", content: text }] } });
      toast(`已导入，共 ${r.total_lines} 行 → ${r.pages_submitted} 页`);
      refreshProjects().then(() => tabCode(p, body));
    } catch (e) { toast(e.message, true); }
  };
  $("#btn-upload").onclick = () => $("#hidden-file").click();
  const st = await api(`/api/projects/${p.id}/code/stats`).catch(() => null);
  const el = $("#code-stats");
  if (!el) return;
  if (!st || !st.total_lines) { el.innerHTML = `<div class="empty"><div class="big">${icon("filecode", 46)}</div>尚未导入源代码</div>`; return; }
  el.innerHTML = `
    <div class="stat-row" style="margin-bottom:12px;">
      <div class="stat"><div class="stat-ico blue">${icon("code", 19)}</div><div><div class="num">${st.total_lines.toLocaleString()}</div><div class="lbl">清洗后总行数</div></div></div>
      <div class="stat"><div class="stat-ico purple">${icon("book", 19)}</div><div><div class="num">${st.pages_submitted}</div><div class="lbl">将提交页数（每页50行）</div></div></div>
      <div class="stat"><div class="stat-ico orange">${icon("layers", 19)}</div><div><div class="num" style="font-size:17px;padding-top:3px;">${st.mode === "all" ? "全部提交" : "前30+后30"}</div><div class="lbl">截取方式</div></div></div>
      <div class="stat"><div class="stat-ico ${st.last_line_ok ? "green" : "orange"}">${icon(st.last_line_ok ? "check" : "alert", 19)}</div><div><div class="num" style="font-size:17px;padding-top:3px;">${st.last_line_ok ? "通过" : "待确认"}</div><div class="lbl">末页结束符检查</div></div></div>
    </div>
    ${st.total_lines < 3000 ? `<div class="issue warning"><span class="lv">建议</span><div><div class="msg">源代码 ${st.total_lines} 行，少于 3000 行</div><div class="fix">2026 审查口径建议自研核心代码不少于 3000 行，可补充核心功能模块的实现代码。</div></div></div>` : ""}
    <div class="table-wrap"><table class="table"><thead><tr><th>文件</th><th style="width:120px;">行数</th></tr></thead><tbody>
      ${(st.files || []).map(f => `<tr><td>${esc(f.filename)}</td><td>${f.lines}</td></tr>`).join("")}
    </tbody></table></div>`;
}

/* ---- Tab: 材料生成 ---- */
function tabGen(p, body) {
  const docs = p.docs || [];
  body.innerHTML = `
  <div class="card" style="border-color:var(--accent);background:linear-gradient(180deg,var(--accent-soft),var(--card) 55%);">
    <h3>${icon("sparkles", 16)} 一键生成全套申请材料 <span class="hint">分析代码 → 说明书 → 申请表 → AI声明 → 过程记录 → 审查 → 导出</span></h3>
    <div class="radio-cards" id="doc-kind-cards">
      <div class="radio-card active" data-kind="manual">
        <div class="rt">${icon("book", 15)} 有操作界面 →《操作说明书》</div>
        <div class="rd">管理后台、Web 应用、桌面/移动端工具：逐模块写操作步骤，插入截图占位框。</div>
      </div>
      <div class="radio-card" data-kind="design">
        <div class="rt">${icon("layers", 15)} 无界面 →《设计说明书》</div>
        <div class="rd">引擎、算法库、接口服务、脚本工具：写总体 / 模块 / 数据 / 接口设计。</div>
      </div>
    </div>
    <div class="row mt">
      <button class="btn btn-primary btn-big" id="btn-all">${icon("sparkles", 16)} 开始一键生成</button>
      <span class="muted">全程需要已配置 LLM；逐章节生成约需数分钟，可随时关闭页面</span>
    </div>
    <div class="progress-panel mt" id="prog" style="display:none;"></div>
  </div>
  <div class="grid-2">
    <div class="card">
      <h3>${icon("code", 16)} 单项生成</h3>
      <div class="row">
        <button class="btn btn-ghost" data-gen="analysis">${icon("refresh", 14)} 重新分析代码</button>
        <button class="btn btn-ghost" data-gen="form">${icon("clipboard", 14)} 申请表字段</button>
        <button class="btn btn-ghost" data-gen="declaration">${icon("bot", 14)} AI 声明</button>
        <button class="btn btn-ghost" data-gen="evidence">${icon("archive", 14)} 过程记录</button>
      </div>
      <div class="muted mt">单项生成也会自动注入知识库规避规则；说明书走上方一键流程（含代码分析）。</div>
    </div>
    <div class="card">
      <h3>${icon("filetext", 16)} 已生成材料（${docs.length}/6）<span class="hint">生成后可直接编辑，人工修改是合规加分项</span></h3>
      ${docs.length ? docs.map(d => {
        const meta = DOC_META[d.doc_type] || { name: d.doc_type, ico: "filetext" };
        const editable = ["manual", "design", "evidence"].includes(d.doc_type);
        return `
        <div class="doc-item">
          <div><div class="t">${icon(meta.ico, 17)} ${esc(d.title || meta.name)}</div>
          <div class="m">${d.size} 字 · 更新于 ${esc(d.updated_at || "")}</div></div>
          <div class="row">
            <button class="btn btn-ghost btn-sm" data-view="${d.doc_type}">${icon("eye", 13)} 预览</button>
            ${editable ? `<button class="btn btn-ghost btn-sm" data-edit="${d.doc_type}">${icon("listcheck", 13)} 编辑</button>` : ""}
            <button class="btn btn-danger-ghost btn-sm" data-rmdoc="${d.doc_type}">${icon("trash", 13)}</button>
          </div>
        </div>`; }).join("") : `<div class="empty">尚未生成任何材料</div>`}
    </div>
  </div>
  <div class="card">
    <h3>${icon("camera", 16)} 界面截图库 <span class="hint">上传后按名称匹配【截图占位】，导出 docx 与打印视图自动嵌入真实截图</span></h3>
    <div id="shot-placeholders" class="row"></div>
    <div class="row mt">
      <input id="shot-label" class="inline-input" style="flex:1;min-width:240px;" placeholder="界面名称，如：订单列表页（与截图占位名称一致即可自动匹配）">
      <button class="btn btn-primary btn-sm" id="btn-shot-upload">${icon("upload", 14)} 上传截图</button>
      <input type="file" id="shot-file" accept="image/png,image/jpeg,image/webp,image/gif,image/bmp" style="display:none;">
    </div>
    <div id="shot-list" class="row mt" style="gap:14px;"></div>
  </div>`;
  loadShots(p);
  $$("#doc-kind-cards .radio-card").forEach(c => c.onclick = () =>
    $$("#doc-kind-cards .radio-card").forEach(x => x.classList.toggle("active", x === c)));
  const selectedKind = () => {
    const active = $("#doc-kind-cards .radio-card.active");
    return active ? active.dataset.kind : "manual";
  };
  const prog = $("#prog");
  const log = (html) => { prog.style.display = "block"; prog.insertAdjacentHTML("beforeend", html + "<br>"); prog.scrollTop = prog.scrollHeight; };
  $("#btn-all").onclick = async () => {
    if (!(state.health && state.health.llm_configured)) return toast("请先在根目录 .env 配置 LLM_API_KEY（支持 GLM/DeepSeek/通义等）", true);
    prog.innerHTML = ""; prog.style.display = "block";
    $("#btn-all").disabled = true;
    try {
      const res = await fetch(`${API}/api/projects/${p.id}/generate/all?doc_kind=${selectedKind()}`, { method: "POST" });
      await consumeSSE(res, ev => {
        const cls = ev.status === "done" ? "ok" : ev.status === "error" ? "err" : "run";
        log(`<span class="${cls}">[${ev.step}]</span> ${esc(ev.message)}`);
        if (ev.status === "error" && ev.step === "pipeline") toast(ev.message, true);
      });
      toast("一键生成流程结束");
    } catch (e) { log(`<span class="err">连接中断：${esc(e.message)}</span>`); }
    $("#btn-all").disabled = false;
    refreshProjects().then(loadProjectView);
  };
  $$("[data-gen]", body).forEach(b => b.onclick = async () => {
    const kind = b.dataset.gen;
    b.disabled = true;
    try {
      if (kind === "analysis") { await api(`/api/projects/${p.id}/generate/analysis`, { method: "POST" }); toast("代码分析完成"); }
      else await api(`/api/projects/${p.id}/generate/${kind}`, { method: "POST", body: {} });
      refreshProjects().then(loadProjectView);
    } catch (e) { toast(e.message, true); b.disabled = false; }
  });
  $$("[data-view]", body).forEach(b => b.onclick = () => previewDoc(p.id, b.dataset.view));
  $$("[data-edit]", body).forEach(b => b.onclick = () => editDoc(p.id, b.dataset.edit));
  $$("[data-rmdoc]", body).forEach(b => b.onclick = async () => {
    if (!confirm("确认删除该材料？")) return;
    await api(`/api/projects/${p.id}/docs/${b.dataset.rmdoc}`, { method: "DELETE" });
    refreshProjects().then(loadProjectView);
  });
}

/* ---- 截图库：上传 / 匹配占位 / 删除 ---- */
async function loadShots(p) {
  const d = await api(`/api/projects/${p.id}/shots`).catch(() => ({ shots: [] }));
  const box = $("#shot-list");
  if (!box) return;
  box.innerHTML = d.shots.length ? d.shots.map(s => `
    <div class="shot-item">
      <img src="${esc(API + s.url)}" alt="${esc(s.label)}">
      <div class="shot-label" title="${esc(s.label)}">${esc(s.label)}</div>
      <button class="btn btn-danger-ghost btn-sm" data-delshot="${+s.id}">删除</button>
    </div>`).join("") : `<div class="muted">尚未上传截图。说明书里的【截图占位】导出时会保留为虚线框，上传同名截图后自动替换。</div>`;
  $$("[data-delshot]", box).forEach(b => b.onclick = async () => {
    await api(`/api/projects/${p.id}/shots/${b.dataset.delshot}`, { method: "DELETE" });
    loadShots(p);
  });
  // 从已生成的说明书中提取未替换的截图占位，点击可快速填入名称
  const phBox = $("#shot-placeholders");
  if (!phBox) return;
  const docTypes = (p.docs || []).map(d => d.doc_type);
  const docType = docTypes.includes("manual") ? "manual" : docTypes.includes("design") ? "design" : null;
  let labels = [];
  if (docType) {
    const doc = await api(`/api/projects/${p.id}/docs/${docType}`).catch(() => null);
    labels = [...String((doc || {}).content || "").matchAll(/【截图占位[:：](.+?)】/g)].map(m => m[1].trim());
  }
  phBox.innerHTML = labels.length
    ? `<span class="muted">说明书中待替换的占位（${labels.length} 个，点击填入名称）：</span>` +
      labels.map(l => `<span class="tag orange" data-ph="${esc(l)}" style="cursor:pointer;">${esc(l)}</span>`).join("")
    : (docType ? `<span class="muted">说明书中没有截图占位标记</span>` : `<span class="muted">生成说明书后，这里会列出全部待替换的截图占位</span>`);
  $$("[data-ph]", phBox).forEach(t => t.onclick = () => { $("#shot-label").value = t.dataset.ph; });
  const fileInput = $("#shot-file");
  $("#btn-shot-upload").onclick = () => fileInput.click();
  fileInput.onchange = async () => {
    const f = fileInput.files[0];
    if (!f) return;
    const label = $("#shot-label").value.trim() || f.name.replace(/\.[^.]+$/, "");
    const fd = new FormData();
    fd.append("file", f);
    fd.append("label", label);
    toast("正在上传截图…");
    const res = await fetch(`${API}/api/projects/${p.id}/shots`, { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) return toast(data.detail || "上传失败", true);
    toast(`截图已入库：${data.label}`);
    fileInput.value = "";
    loadShots(p);
  };
}

/* ---- 材料在线编辑（AI 生成后人工修改，可重新导出） ---- */
async function editDoc(pid, docType) {
  try {
    const d = await api(`/api/projects/${pid}/docs/${docType}`);
    const m = document.createElement("div");
    m.className = "modal-mask";
    m.innerHTML = `<div class="modal" style="width:880px;">
      <div class="modal-head"><h3>编辑：${esc(DOC_META[docType] ? DOC_META[docType].name : docType)}</h3>
        <button class="modal-close">${icon("x")}</button></div>
      <div class="modal-body">
        <div class="row" style="justify-content:flex-end;margin-bottom:10px;">
          <button class="btn btn-ghost btn-sm" id="ed-preview">${icon("eye", 13)} 预览</button>
          <button class="btn btn-ghost btn-sm" id="ed-source">${icon("code", 13)} 编辑源码</button>
        </div>
        <textarea id="ed-content" style="width:100%;min-height:420px;font-family:var(--font-mono);font-size:12.5px;line-height:1.8;border:1px solid var(--line-strong);border-radius:10px;padding:12px;background:var(--card-2);color:var(--text);resize:vertical;">${esc(d.content)}</textarea>
        <div id="ed-preview-box" class="md" style="display:none;max-height:460px;overflow-y:auto;border:1px solid var(--line);border-radius:10px;padding:16px;background:var(--card-2);"></div>
        <div class="row mt" style="justify-content:flex-end;">
          <span class="muted">保存后同步生效于 docx 导出与打印视图；保持【截图占位：名称】格式可自动嵌入截图</span>
          <button class="btn btn-primary" id="ed-save">保存修改</button>
        </div>
      </div></div>`;
    document.body.appendChild(m);
    $(".modal-close", m).onclick = () => m.remove();
    m.onclick = e => { if (e.target === m) m.remove(); };
    $("#ed-preview", m).onclick = () => {
      $("#ed-content", m).style.display = "none";
      const box = $("#ed-preview-box", m);
      box.innerHTML = md2html($("#ed-content", m).value);
      box.style.display = "block";
    };
    $("#ed-source", m).onclick = () => {
      $("#ed-preview-box", m).style.display = "none";
      $("#ed-content", m).style.display = "block";
    };
    $("#ed-save", m).onclick = async () => {
      try {
        await api(`/api/projects/${pid}/docs/${docType}`, { method: "PUT", body: { content: $("#ed-content", m).value } });
        toast("已保存，导出与打印将使用新内容");
        m.remove();
        refreshProjects().then(loadProjectView);
      } catch (e) { toast(e.message, true); }
    };
  } catch (e) { toast(e.message, true); }
}

async function previewDoc(pid, docType) {
  try {
    const d = await api(`/api/projects/${pid}/docs/${docType}`);
    const meta = d.meta || {};
    let contentHTML;
    if (docType === "analysis" || docType === "form" || docType === "declaration") {
      const data = meta.data || JSON.parse(d.content || "{}");
      contentHTML = `<div class="table-wrap"><table class="table"><tbody>${Object.entries(data).map(([k, v]) =>
        `<tr><td style="width:180px;font-weight:600;">${esc(k)}</td><td>${esc(typeof v === "object" ? JSON.stringify(v) : v).slice(0, 2000)}</td></tr>`).join("")}</tbody></table></div>`;
    } else contentHTML = md2html(d.content);
    openModal(DOC_META[docType] ? DOC_META[docType].name : docType, contentHTML);
  } catch (e) { toast(e.message, true); }
}

function openModal(title, html) {
  const m = document.createElement("div");
  m.className = "modal-mask";
  m.innerHTML = `<div class="modal"><div class="modal-head"><h3>${esc(title)}</h3><button class="modal-close">${icon("x")}</button></div>
    <div class="modal-body md">${html}</div></div>`;
  document.body.appendChild(m);
  $(".modal-close", m).onclick = () => m.remove();
  m.onclick = e => { if (e.target === m) m.remove(); };
}

/* ---- Tab: 合规审查 ---- */
async function tabReview(p, body) {
  body.innerHTML = `
  <div class="card">
    <h3>${icon("shield", 16)} 提交前合规预检 <span class="hint">内置 2026 新规 + 知识库规则 + AI 软审查</span></h3>
    <div class="row">
      <button class="btn btn-primary btn-big" id="btn-review">${icon("shield", 16)} 运行合规审查</button>
      <span class="muted">检查：三重一致性 / 名称版本格式 / AI 痕迹 / 功能描述字数 / 材料齐备 / 知识库规则</span>
    </div>
    <div id="review-result" class="mt"></div>
  </div>
  <div class="card"><h3>${icon("clock", 16)} 历史审查记录</h3><div id="review-history"><div class="empty">加载中…</div></div></div>`;
  const reports = await api(`/api/projects/${p.id}/reports`).catch(() => ({ reports: [] }));
  $("#review-history").innerHTML = reports.reports.length ? `<div class="table-wrap"><table class="table">
    <thead><tr><th>时间</th><th>结论</th><th>阻断项</th><th>提醒项</th><th></th></tr></thead><tbody>
    ${reports.reports.map(r => `<tr><td>${esc(r.created_at)}</td>
      <td><span class="tag ${r.passed ? "green" : "red"}">${r.passed ? "通过" : "未通过"}</span></td>
      <td>${r.blockers}</td><td>${r.warnings}</td>
      <td><button class="btn btn-ghost btn-sm" data-rep="${r.id}">${icon("eye", 13)} 查看</button></td></tr>`).join("")}
    </tbody></table></div>` : `<div class="empty">暂无记录</div>`;
  $$("[data-rep]", body).forEach(b => b.onclick = async () => {
    const r = await api(`/api/projects/${p.id}/reports/${b.dataset.rep}`);
    renderReport(r.issues || JSON.parse(r.result_json || "[]"), r.passed);
  });
  $("#btn-review").onclick = async () => {
    const btn = $("#btn-review"); btn.disabled = true; btn.textContent = "审查中…";
    $("#review-result").innerHTML = `<div class="empty">正在按 2026 新规逐项检查…</div>`;
    try {
      const r = await api(`/api/projects/${p.id}/review`, { method: "POST", body: { include_llm: true } });
      renderReport(r.issues, r.passed);
      if (!state.health.llm_configured) toast("提示：未配置 LLM，仅执行硬校验（配置后可加 AI 软审查）");
    } catch (e) { $("#review-result").innerHTML = ""; toast(e.message, true); }
    btn.disabled = false; btn.innerHTML = `${icon("shield", 16)} 运行合规审查`;
  };
  function renderReport(issues, passed) {
    const blockers = issues.filter(i => i.level === "blocker");
    const warnings = issues.filter(i => i.level === "warning");
    $("#review-result").innerHTML = `
      <div class="issue ${passed ? "pass" : "blocker"}">
        <span class="lv">${passed ? "可提交" : "暂缓提交"}</span>
        <div><div class="msg">${passed ? "阻断项已清零，材料达到可提交状态" : `仍有 ${blockers.length} 个阻断项，修复后再提交`}</div>
        <div class="fix">阻断 ${blockers.length} · 提醒 ${warnings.length}。最终以版权中心审查为准；提交前建议用真实 Git 记录复核开发过程。</div></div>
      </div>
      ${blockers.concat(warnings).map(i => `
        <div class="issue ${i.level}">
          <span class="lv">${i.level === "blocker" ? "阻断" : "提醒"}</span>
          <div><div class="msg">${esc(i.message)}</div><div class="fix">${icon("arrow", 12)} ${esc(i.suggestion || "—")}${i.source === "knowledge_base" ? `　<span class="tag blue">知识库规则</span>` : i.source === "llm" ? `　<span class="tag orange">AI 软审查</span>` : ""}</div></div>
        </div>`).join("")}`;
  }
}

/* ---- Tab: 驳回知识库 ---- */
function catColor(c) {
  return { "格式规范": "blue", "材料一致性": "orange", "AI声明与原创性": "red", "功能描述不足": "orange", "材料缺失": "gray", "其他": "gray" }[c] || "gray";
}

async function tabKB(p, body) {
  const rules = await api(`/api/kb/rules?project_id=${p.id}`).then(d => d.rules).catch(() => []);
  const cases = await api("/api/kb/cases").then(d => d.cases).catch(() => []);
  body.innerHTML = `
  <div class="card" style="border-color:var(--warn);background:linear-gradient(180deg,var(--warn-soft),var(--card) 55%);">
    <h3>${icon("refresh", 16)} 驳回流：把打回的问题变成下次的免疫力 <span class="hint">核心闭环：补正通知 → AI 归因 → 规避规则 → 自动生效</span></h3>
    <div class="field"><textarea id="kb-raw" style="min-height:115px;" placeholder="把版权中心的补正通知书 / 驳回通知原文粘贴到这里……（例如：经审查，你申请登记的软件存在以下问题：一、……）"></textarea></div>
    <div class="row mt">
      <select id="kb-type" class="btn btn-ghost" style="padding:8px 12px;"><option>补正通知</option><option>驳回通知</option><option>人工经验</option></select>
      <button class="btn btn-primary" id="kb-analyze">${icon("sparkles", 15)} AI 归因并沉淀规则</button>
      <span class="muted">归因后生成的规则立即注入所有材料生成与合规审查</span>
    </div>
    <div id="kb-result" class="mt"></div>
  </div>
  <div class="card">
    <h3>${icon("shield", 16)} 规避规则库（${rules.length} 条）<span class="hint">含平台内置规则 + 历次驳回沉淀规则</span></h3>
    <div class="table-wrap"><table class="table"><thead><tr><th style="width:96px;">分类</th><th>问题</th><th>规避方法</th><th style="width:66px;">检查</th><th style="width:56px;">命中</th><th style="width:126px;">操作</th></tr></thead><tbody>
    ${rules.map(r => `<tr>
      <td><span class="tag ${catColor(r.category)}">${esc(r.category)}</span></td>
      <td>${esc(r.problem)}</td>
      <td style="color:var(--text-2);">${esc(r.solution || "—")}</td>
      <td>${r.check_type === "regex" ? `<span class="tag blue">自动</span>` : `<span class="tag gray">提示</span>`}</td>
      <td>${r.hit_count}</td>
      <td><button class="btn btn-ghost btn-sm" data-toggle="${r.id}">${r.enabled ? "停用" : "启用"}</button>
          <button class="btn btn-danger-ghost btn-sm" data-del="${r.id}">${icon("trash", 13)}</button></td>
    </tr>`).join("")}
    </tbody></table></div>
  </div>
  <div class="card"><h3>${icon("archive", 16)} 归因案例（${cases.length}）</h3>
    ${cases.length ? cases.map(c => `
      <div class="kbd-line"><span class="tag ${catColor(c.analysis && c.analysis.category)}">${esc(c.source_type)}</span>
      <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${esc(c.analysis && c.analysis.summary || c.raw_text)}</span>
      <span class="muted">${esc((c.created_at || "").slice(0, 10))}</span></div>`).join("") : `<div class="empty">暂无驳回案例 —— 提交被退回后把通知贴到上方</div>`}
  </div>`;
  $("#kb-analyze").onclick = async () => {
    const raw = $("#kb-raw").value.trim();
    if (!raw) return toast("请先粘贴补正/驳回通知原文", true);
    const btn = $("#kb-analyze"); btn.disabled = true; btn.textContent = "AI 归因中…";
    try {
      const r = await api("/api/kb/analyze", { method: "POST", body: { raw_text: raw, source_type: $("#kb-type").value, project_id: p.id } });
      const a = r.analysis || {};
      $("#kb-result").innerHTML = `
        <div class="issue info">
          <span class="lv">归因</span>
          <div><div class="msg">${esc(a.summary || "")}（${esc(a.category || "")}）</div>
          <div class="fix">已沉淀 ${r.rule_ids.length} 条规避规则，之后生成材料与审查时自动规避。</div></div></div>
        ${(a.rules || []).map(x => `<div class="kbd-line"><b>${esc(x.problem)}</b><span class="muted">${esc(x.solution || "")}</span></div>`).join("")}`;
      toast("已沉淀规避规则");
      loadProjectView();
    } catch (e) { toast(e.message, true); }
    btn.disabled = false; btn.innerHTML = `${icon("sparkles", 15)} AI 归因并沉淀规则`;
  };
  $$("[data-toggle]", body).forEach(b => b.onclick = async () => {
    if (!/^\d+$/.test(b.dataset.toggle)) return;
    const rule = rules.find(r => r.id === +b.dataset.toggle);
    if (!rule) return;
    await api(`/api/kb/rules/${+b.dataset.toggle}`, { method: "PATCH", body: { enabled: !rule.enabled } });
    tabKB(p, body);
  });
  $$("[data-del]", body).forEach(b => b.onclick = async () => {
    if (!confirm("确认删除该规则？")) return;
    if (!/^\d+$/.test(b.dataset.del)) return;
    await api(`/api/kb/rules/${b.dataset.del}`, { method: "DELETE" });
    tabKB(p, body);
  });
}

/* ---- Tab: 导出下载 ---- */
async function tabExport(p, body) {
  const files = await api(`/api/projects/${p.id}/files`).catch(() => ({ files: [] }));
  const docTypes = (p.docs || []).map(d => d.doc_type);
  const manualType = docTypes.includes("manual") ? "manual" : docTypes.includes("design") ? "design" : null;
  const printBtn = (type, enabled) => enabled
    ? `<button class="btn btn-ghost btn-sm" data-print="${type}">${icon("filetext", 13)} 打印/PDF</button>` : "";
  body.innerHTML = `
  <div class="card">
    <h3>${icon("download", 16)} 下载申请材料 <span class="hint">docx 可直接打印；"打印/PDF"打开 A4 排版视图后另存为 PDF</span></h3>
    <div class="grid-2">
      <div class="doc-item"><div><div class="t">${icon("filecode", 17)} 源程序鉴别材料（docx）</div><div class="m">每页50行 · 页眉含名称版本 · 自动页码 · 前30后30截取</div></div>
        <div class="row">${printBtn("source", true)}
        <button class="btn btn-primary btn-sm" data-dl="source">下载</button></div></div>
      <div class="doc-item"><div><div class="t">${icon("book", 17)} 操作/设计说明书（docx）</div><div class="m">含截图自动嵌入 · 每页约30行 · 下载后替换剩余占位打印</div></div>
        <div class="row">${printBtn(manualType, !!manualType)}
        <button class="btn btn-primary btn-sm" data-dl="manual">下载</button></div></div>
      <div class="doc-item"><div><div class="t">${icon("clipboard", 17)} 申请表预填清单（docx）</div><div class="m">对照官网申请表逐项复制 · 附 AI 声明全文</div></div>
        <div class="row">${printBtn("form", docTypes.includes("form"))}
        <button class="btn btn-primary btn-sm" data-dl="form">下载</button></div></div>
      <div class="doc-item"><div><div class="t">${icon("archive", 17)} 开发过程记录（docx）</div><div class="m">创作过程证据链材料，备查</div></div>
        <div class="row">${printBtn("evidence", docTypes.includes("evidence"))}
        <button class="btn btn-primary btn-sm" data-dl="evidence">下载</button></div></div>
      ${docTypes.includes("declaration") ? `<div class="doc-item"><div><div class="t">${icon("bot", 17)} AI 使用声明</div><div class="m">2026 新规材料，附申请表提交</div></div>
        <div class="row">${printBtn("declaration", true)}</div></div>` : ""}
    </div>
    <div class="row mt" style="justify-content:center;">
      <button class="btn btn-primary btn-big" data-dl="bundle">${icon("download", 16)} 下载全套材料包（zip，含材料清单与提交检查）</button>
    </div>
    ${files.files.length ? `<div class="mt"><div class="muted" style="margin-bottom:6px;">导出目录中的文件：</div>
      ${files.files.map(f => `<div class="kbd-line">${icon("filetext", 14)} <a href="${esc(API + "/api/projects/" + p.id + "/files/" + encodeURIComponent(f))}" download style="color:var(--accent);text-decoration:none;">${esc(f)}</a></div>`).join("")}</div>` : ""}
  </div>
  <div class="card">
    <h3>${icon("listcheck", 16)} 提交前人工核对（平台已自动检查大部分，剩下需要你动手）</h3>
    <div class="kbd-line"><span class="tag blue">1</span><span>在官网 cpservice.org 在线填写申请表并<b>带流水号打印</b>（预填清单逐项复制）</span></div>
    <div class="kbd-line"><span class="tag blue">2</span><span>打开说明书 docx，把剩余的【截图占位框】替换为<b>真实界面截图</b>（已上传截图的会自动嵌入）</span></div>
    <div class="kbd-line"><span class="tag blue">3</span><span>全部材料<b>单面打印</b>，签字/盖章页不要漏（申请表签名页、营业执照盖章）</span></div>
    <div class="kbd-line"><span class="tag blue">4</span><span>合规审查页 <b>blocker 清零</b> 后再提交；AI 声明口径与实际开发过程一致</span></div>
  </div>`;
  $$("[data-print]", body).forEach(b => b.onclick = () => {
    if (!/^(source|manual|design|form|declaration|evidence)$/.test(b.dataset.print)) return;
    window.open(`${API}/api/projects/${p.id}/print/${b.dataset.print}`, "_blank");
  });
  const DL_KINDS = ["source", "manual", "form", "evidence", "bundle"];
  $$("[data-dl]", body).forEach(b => b.onclick = () => {
    const kind = b.dataset.dl;
    if (!DL_KINDS.includes(kind)) return;
    const url = kind === "bundle" ? `${API}/api/projects/${p.id}/export/bundle` : `${API}/api/projects/${p.id}/export/${kind}`;
    fetch(url).then(res => {
      if (!res.ok) return res.json().then(d => { throw new Error(d.detail || "导出失败"); });
      return res.blob().then(blob => {
        const dispo = res.headers.get("content-disposition") || "";
        let name = "download.docx";
        const m = dispo.match(/filename\*?=(?:UTF-8'')?"?([^";]+)/i);
        if (m) name = decodeURIComponent(m[1]);
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob); a.download = name; a.click();
        URL.revokeObjectURL(a.href);
      });
    }).catch(e => toast(e.message, true));
  });
}

/* ---------------- 主题 ---------------- */
function initTheme() {
  const btn = $("#btn-theme");
  if (!btn) return;
  const paint = () => { btn.innerHTML = icon(document.documentElement.dataset.theme === "dark" ? "sun" : "moon"); };
  btn.onclick = () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("rz-theme", next); } catch (e) {}
    paint();
  };
  paint();
}

/* ---------------- 启动 ---------------- */
async function boot() {
  hydrateIcons();
  initTheme();
  // 单文件预览模式（standalone/index.html 直接 file:// 打开）给出明确提示
  if (location.protocol === "file:") {
    const b = document.createElement("div");
    b.className = "demo-banner";
    b.innerHTML = "当前为<b>单文件预览模式</b>（file:// 直接打开）：数据接口不可用，仅展示界面骨架。完整功能请运行 <b>./start.sh</b> 后访问 <b>http://127.0.0.1:8310</b>。";
    document.body.prepend(b);
  }
  try { state.health = await api("/api/health"); } catch (e) {}
  const h = state.health;
  $("#llm-badge").innerHTML = h && h.llm_configured
    ? `<span class="badge-llm on">${icon("check", 12)} AI 已连接 · ${esc(h.llm_model || "")}</span>`
    : `<span class="badge-llm off" title="在项目根目录 .env 配置 LLM_API_KEY 后可使用 AI 生成">${icon("alert", 12)} AI 未配置</span>`;
  try { await refreshProjects(); }
  catch (e) {
    $("#proj-list").innerHTML = `<div class="proj-empty">服务未连接</div>`;
    setPage("服务未连接", "请确认后端已启动（./start.sh）");
  }
  const m = location.hash.match(/^#\/project\/(\d+)/);
  if (m && state.projects.some(p => p.id === +m[1])) { state.currentId = +m[1]; loadProjectView(); }
  else showDashboard();
}

$("#btn-new-top").onclick = () => openProjectModal(null);
$("#btn-new-side").onclick = () => openProjectModal(null);
$("#btn-home").onclick = () => showDashboard();
window.openProject = openProject;
boot();
