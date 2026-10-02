"""Prompt 模板体系。

所有材料生成 prompt 统一注入三层上下文：
1. 角色设定：资深软著申请顾问（熟悉 2026-03-15 新版申请表与 AI 声明新规）；
2. 合规红线：三重一致性、人类实质性创作、禁止出现的内容；
3. 驳回知识库规避清单：内置种子规则 + 用户沉淀规则（打回过的问题下次必须规避）。
"""
from typing import Any, Dict, List

from .. import llm

SYSTEM = (
    "你是中国软件著作权登记申请领域最资深的材料撰写顾问，熟悉中国版权保护中心的审查标准，"
    "包括2026年3月15日起启用的新版《计算机软件著作权登记申请表》与AI声明制度、"
    "三重一致性校验（申请表/源程序/文档的名称版本功能必须一致）、以及非正常申请的8类驳回红线。"
    "你写的一切材料："
    "①内容必须与给定的软件名称、版本号、功能描述严格一致；"
    "②必须体现具体的、有细节的技术实现与人类设计决策，禁止空话套话；"
    "③不得出现任何真实客户名称、真实单位名称、真实个人信息；"
    "④不得出现'AI''人工智能生成''大模型''语言模型'等字样，也不得出现任何暗示内容由AI生成的表述；"
    "⑤语言风格朴实专业，像有经验的工程师手动撰写。"
)


def kb_rules_block(rules: List[Dict[str, Any]]) -> str:
    """把知识库规则渲染进 prompt 的规避清单文本。"""
    if not rules:
        return ""
    lines = ["【历史驳回问题规避清单（此前申请因以下问题被补正/驳回，本次材料必须规避）】"]
    for i, r in enumerate(rules, 1):
        problem = (r.get("problem") or "").strip()
        solution = (r.get("solution") or "").strip()
        line = f"{i}. {problem}"
        if solution:
            line += f" → 规避方法：{solution}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def _project_block(ctx: Dict[str, Any]) -> str:
    p = ctx["project"]
    parts = [
        f"软件全称：{p.get('full_name', '')}",
        f"版本号：{p.get('version', '')}",
        f"开发完成日期：{p.get('completion_date') or '待定'}",
        f"首次发表日期：{p.get('publish_date') or '未发表'}",
        f"开发方式：{p.get('dev_type', '独立开发')}",
    ]
    if p.get("short_name"):
        parts.append(f"软件简称：{p['short_name']}")
    if p.get("main_functions"):
        parts.append(f"用户描述的主要功能：{p['main_functions']}")
    if p.get("tech_stack"):
        parts.append(f"技术栈：{p['tech_stack']}")
    return "\n".join(parts)


def _code_block(ctx: Dict[str, Any]) -> str:
    a = ctx.get("code_analysis") or {}
    lines = [f"源代码规模：共 {a.get('total_lines', 0)} 行"]
    for f in (a.get("files") or [])[:25]:
        idents = "、".join((f.get("identifiers") or [])[:20])
        lines.append(f"- {f.get('filename')}（{f.get('lines')}行）主要函数/类：{idents or '无'}")
    return "\n".join(lines)


def _user(messages: List[Dict[str, str]], text: str) -> List[Dict[str, str]]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]


# ---------------- 代码分析 ----------------

def code_analysis_messages(ctx: Dict[str, Any]) -> List[Dict[str, str]]:
    text = f"""请阅读以下软件的源代码结构信息，输出 JSON（不要输出其他文字）：

{{"software_positioning": "一句话说明这是什么软件",
"modules": [{{"name": "模块名", "description": "该模块做什么、涉及哪些函数", "functions": ["函数名"]}}],
"architecture": "2-3句话概括技术架构与分层",
"highlights": ["体现独创性的技术点1", "技术点2", "技术点3"],
"suggestions": ["审查前建议人工补充修改的地方"]}}

要求：
- modules 是软件的功能模块划分（3-8个），模块名要像产品功能名（如"订单管理模块"），不要用文件名；
- 功能模块必须能从给出的函数/类名中找到依据，不得编造不存在的功能；
- highlights 侧重设计思路、算法处理、性能或可靠性措施等独创性表达。

{_project_block(ctx)}

源代码结构：
{_code_block(ctx)}

{ctx.get('kb_text', '')}"""
    return _user([], text)


# ---------------- 操作说明书（有界面软件） ----------------

MANUAL_CHAPTERS = [
    {"key": "preface", "title": "前言", "hint": (
        "包含：编写目的（帮助用户了解软件的用途与操作方法）、软件概况（名称、版本、开发单位/个人、"
        "主要用途一段话）、适用对象、文中约定（如【截图】标记说明）。约300-500字。")},
    {"key": "overview", "title": "软件概述", "hint": (
        "包含：开发背景与目标、主要功能列表（逐条列出每个功能模块及其作用，与给定模块划分一致）、"
        "技术架构简介（分层/组件/数据流，两三段）。约600-900字。")},
    {"key": "environment", "title": "运行环境", "hint": (
        "硬件环境（CPU/内存/存储最低配置与推荐配置，表格）、软件环境（操作系统/依赖运行时/数据库/浏览器版本）、"
        "网络环境说明。要与技术栈一致。约400-600字。")},
    {"key": "install", "title": "安装与启动", "hint": (
        "安装前置条件、获取安装包、安装步骤（编号步骤，每步一句话）、启动与初始化、"
        "卸载方法。每步标注【截图占位：xxx】。约500-800字。")},
    {"key": "faq", "title": "常见问题与处理", "hint": (
        "列出6-10个使用中的常见问题（问题现象、原因分析、解决步骤），覆盖安装、启动、"
        "功能使用、数据等方面。约600-900字。")},
]


def manual_chapter_messages(ctx: Dict[str, Any], title: str, hint: str) -> List[Dict[str, str]]:
    text = f"""请为《{ctx['project'].get('full_name', '')} {ctx['project'].get('version', '')}》的操作说明书撰写「{title}」章节。

写作要求：
{hint}
- Markdown 格式，章节标题用「## {title}」，小节用 ###；
- 操作步骤用编号列表，每一步都具体可执行；
- 涉及界面的地方必须插入截图占位标记，格式单独一行：【截图占位：界面名称】；
- 严禁出现具体真实单位、客户名称。

{_project_block(ctx)}

功能模块划分：
{ctx.get('modules_text', '')}

{ctx.get('kb_text', '')}"""
    return _user([], text)


def manual_module_messages(ctx: Dict[str, Any], module: Dict[str, Any]) -> List[Dict[str, str]]:
    text = f"""请为《{ctx['project'].get('full_name', '')} {ctx['project'].get('version', '')}》的操作说明书撰写功能操作章节「{module['name']}」。

要求：
- Markdown，一级标题「## {module['name']}」；
- 内容包含：### 功能说明（该功能解决什么问题、入口在哪里）、### 操作步骤（编号步骤，覆盖完整操作流：进入→填写/配置→执行→结果确认，每步具体）、### 结果与注意事项；
- 全章至少 500 字，操作步骤不少于 6 步；
- 每个关键界面后单独一行插入：【截图占位：界面名称】（本模块至少 3 处）；
- 界面元素名称要具体（按钮名、字段名、菜单名），与模块功能相符；
- 严禁出现具体真实单位、客户名称。

{_project_block(ctx)}

本模块信息：{module.get('description', '')}，涉及函数：{"、".join((module.get('functions') or [])[:15])}

{ctx.get('kb_text', '')}"""
    return _user([], text)


# ---------------- 设计说明书（无界面软件） ----------------

DESIGN_CHAPTERS = [
    {"key": "intro", "title": "引言", "hint": "编写目的、软件定位、术语定义。约300-500字。"},
    {"key": "arch", "title": "总体设计", "hint": (
        "设计目标、总体架构（分层描述：接入层/服务层/数据层等，文字详述每层职责与交互）、"
        "技术选型及理由。约800-1200字。")},
    {"key": "modules", "title": "模块设计", "hint": (
        "逐个模块写：模块职责、内部处理流程（编号步骤）、关键函数说明、模块间依赖。"
        "必须与给定模块划分一致。约1200-2000字。")},
    {"key": "data", "title": "数据设计", "hint": (
        "核心数据实体及字段说明（表格）、数据流转与存储方案、关键算法/处理逻辑的文字流程图"
        "（输入→处理→输出）。约800-1200字。")},
    {"key": "iface", "title": "接口设计", "hint": (
        "核心接口列表（表格：接口名/方法/入参/出参/说明），错误处理与重试机制，"
        "无接口的后台/工具软件则写输入输出约定。约600-1000字。")},
    {"key": "deploy", "title": "部署与运行设计", "hint": (
        "部署架构、启动流程、日志与监控、异常处理与降级策略。约500-800字。")},
]


def design_chapter_messages(ctx: Dict[str, Any], title: str, hint: str) -> List[Dict[str, str]]:
    text = f"""请为《{ctx['project'].get('full_name', '')} {ctx['project'].get('version', '')}》的设计说明书撰写「{title}」章节。

写作要求：
{hint}
- Markdown 格式，章节标题用「## {title}」，小节用 ###；
- 必须体现具体设计决策与理由（为什么这样设计），体现人类的设计思考；
- 表格用 Markdown 表格。

{_project_block(ctx)}

功能模块划分：
{ctx.get('modules_text', '')}

{ctx.get('kb_text', '')}"""
    return _user([], text)


# ---------------- 申请表字段 ----------------

def form_messages(ctx: Dict[str, Any]) -> List[Dict[str, str]]:
    text = f"""请为软件著作权登记申请表生成以下字段，输出 JSON：

{{"development_purpose": "开发目的（不少于500字）",
"main_functions_desc": "主要功能与技术特点描述（不少于500字，逐条列出功能并说明技术实现）",
"technical_features": "技术特点摘要（200-300字）",
"target_users": "面向的使用对象或应用领域（100-200字）",
"hardware_env": "运行硬件环境要求（一句话）",
"software_env": "运行软件环境要求（一句话）",
"programming_language": "开发编程语言（从代码推断）",
"source_lines_note": "源程序量描述，格式如'32101行'（必须带'行'字）"}}

要求：
- development_purpose 与 main_functions_desc 都必须不少于 500 字，内容具体（解决什么问题、
  为什么这么做、核心功能怎么用），禁止空话套话堆砌；
- 所有内容必须与给定代码结构吻合，不编造代码里不存在的功能；
- source_lines_note 的行数使用给定的真实统计行数。

{_project_block(ctx)}

源代码结构：
{_code_block(ctx)}
源代码总行数：{ctx.get('total_lines', 0)}

{ctx.get('kb_text', '')}"""
    return _user([], text)


# ---------------- AI 声明 ----------------

def declaration_messages(ctx: Dict[str, Any]) -> List[Dict[str, str]]:
    text = f"""请为本次软件著作权登记生成「AI使用情况声明及人类实质性创作说明」正文，输出 JSON：

{{"ai_usage_summary": "如实说明AI在开发中的使用范围与方式（150-300字）",
"human_contribution": "人类实质性创作说明：需求设计、架构决策、代码审查修改、测试调优等（300-500字）",
"originality_statement": "独创性声明（100-200字，承诺材料真实、内容具备独创性、愿意承担相应责任）",
"evidence_list": ["支撑证据1：如Git版本管理记录", "证据2", "证据3"]}}

要求：
- 口径为「AI辅助开发 + 人类实质性创作」，与申请表AI声明选项一致；如实、克制，不夸大也不回避；
- human_contribution 必须结合本项目的具体功能与模块写具体的设计决策场景；
- 语气正式，适合直接附在申请材料中。

{_project_block(ctx)}

功能模块：
{ctx.get('modules_text', '')}

{ctx.get('kb_text', '')}"""
    return _user([], text)


# ---------------- 开发过程记录（证据链） ----------------

def evidence_messages(ctx: Dict[str, Any]) -> List[Dict[str, str]]:
    git_log = (ctx.get("git_log") or "").strip()
    text = f"""请为《{ctx['project'].get('full_name', '')} {ctx['project'].get('version', '')}》生成「软件开发过程记录」文档（Markdown），作为创作过程证据材料。

包含：
## 一、开发阶段划分（表格：阶段/时间范围/主要工作/产出）
## 二、需求与设计过程（需求分析、方案设计、评审修改的叙述）
## 三、编码与迭代过程（分阶段叙述核心模块的实现与演进）
## 四、测试与修复记录（表格：日期/发现问题/修复措施/验证结果）
## 五、版本管理说明（工具、提交频率、分支策略）

要求：
- 时间线必须落在 开发完成日期 之前，阶段之间衔接合理；
- 内容必须围绕本软件的具体模块展开，具体到模块名与功能点。

{_project_block(ctx)}

功能模块：
{ctx.get('modules_text', '')}

Git 提交记录（如有，请据此还原真实时间线）：
{git_log[:3000] if git_log else '（未提供，请按合理节奏虚构阶段划分，日期用区间占位）'}

{ctx.get('kb_text', '')}"""
    return _user([], text)


# ---------------- 驳回案例归因（知识库闭环入口） ----------------

RULE_CATEGORIES = ("格式规范", "材料一致性", "AI声明与原创性", "功能描述不足", "材料缺失", "其他")

def kb_analyze_messages(rejection_text: str, scope_hint: str) -> List[Dict[str, str]]:
    text = f"""以下是一份软件著作权申请的{scope_hint}原文。请归因分析并沉淀为可复用的规避规则，输出 JSON：

{{"summary": "一句话概括被打回的原因",
"category": "归类，只能取：格式规范/材料一致性/AI声明与原创性/功能描述不足/材料缺失/其他",
"rules": [
  {{"problem": "被驳回的具体问题（一句可执行的陈述）",
    "solution": "下次如何规避（具体做法）",
    "check_type": "none 或 regex（问题能用正则自动检查时才填 regex）",
    "check_target": "regex 检查对象：full_name/version/main_functions/manual/form/source 之一（非 regex 填空字符串）",
    "check_pattern": "regex 模式（非 regex 填空字符串）"}}
]}}

要求：
- 把通知书里的每个独立问题拆成一条规则（1-6条）；
- solution 要具体到怎么改材料；
- 只有当问题确实能用正则判断时才给 regex（例如'版本号格式应为V1.0'→ ^V\\d+(\\.\\d+)+$ 之类），
  拿不准就填 none。

{scope_hint}原文：
{rejection_text[:6000]}"""
    return _user([], text)


# ---------------- LLM 软审查 ----------------

def review_soft_messages(ctx: Dict[str, Any], manual_excerpt: str, form_summary: str) -> List[Dict[str, str]]:
    text = f"""你是软著审查预检员。请根据以下材料判断本申请若提交是否会被补正/驳回，输出 JSON：

{{"issues": [
  {{"level": "blocker 或 warning",
    "category": "材料一致性/AI声明与原创性/功能描述不足/格式规范/其他",
    "message": "问题描述",
    "suggestion": "修改建议"}}
]}}

重点检查：
1. 三重一致性：申请表功能描述、说明书目录、源代码结构三者是否逻辑闭环（名称/版本/功能对应）；
2. AI 痕迹：源代码摘录是否存在模板化注释、风格单一、无设计意图注释等易被判为AI生成的特征；
3. 功能描述是否少于500字、是否与代码不符；
4. 说明书是否有实质操作内容（而非套话）。

{ctx.get('kb_text', '')}

{_project_block(ctx)}

申请表字段摘要：
{form_summary[:2000]}

说明书摘录：
{manual_excerpt[:3000]}

源代码摘录（多处抽样）：
{ctx.get('code_samples', '')[:5000]}"""
    return _user([], text)
