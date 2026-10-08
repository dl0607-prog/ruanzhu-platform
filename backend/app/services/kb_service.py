"""驳回知识库服务：案例归因 → 规则沉淀 → 规避上下文注入。

闭环：上传补正/驳回通知 → AI 归因拆解为规则（可正则执行的直接进审查引擎，
其余进生成 prompt 的规避清单）→ 下次生成/审查时自动生效。
"""
import re
from typing import Any, Dict, List, Optional

from .. import database as db
from .. import llm
from . import prompts

_KEYWORD_RULES = [
    (("页眉", "50行", "三十页", "30行", "页数", "空行", "打印", "页码", "行数", "字体"), "格式规范"),
    (("不一致", "名称", "版本号", "简称", "一致"), "材料一致性"),
    (("AI", "人工智能", "生成式", "大模型", "自动生成", "原创性", "独创"), "AI声明与原创性"),
    (("功能描述", "字数", "500", "描述不", "说明不"), "功能描述不足"),
    (("缺少", "未提交", "未提供", "补交", "缺失", "未附"), "材料缺失"),
]


def _fallback_rules(raw_text: str) -> Dict[str, Any]:
    """LLM 不可用时的兜底归因：按关键词分类，至少把原始问题完整存档。"""
    category = "其他"
    best = 0
    for words, cat in _KEYWORD_RULES:
        hits = sum(1 for w in words if w in raw_text)
        if hits > best:
            best, category = hits, cat
    text = re.sub(r"\s+", " ", raw_text).strip()
    return {
        "summary": text[:120] or "（空）",
        "category": category,
        "rules": [{"problem": text[:300] or "材料被退回，原因见原文",
                   "solution": "对照原文逐项修改；可在规则库中人工补充规避方法",
                   "check_type": "none", "check_target": "", "check_pattern": ""}],
    }


async def analyze_and_store(raw_text: str, source_type: str,
                            project_id: Optional[int]) -> Dict[str, Any]:
    scope_hint = "补正通知" if "补正" in (source_type or "") else "驳回通知"
    analysis: Dict[str, Any]
    rules_out: List[int] = []
    try:
        msgs = prompts.kb_analyze_messages(raw_text, scope_hint)
        analysis = await llm.chat_json(msgs, max_tokens=2500)
        if not isinstance(analysis, dict) or not analysis.get("rules"):
            raise llm.LLMError("empty")
    except Exception:
        analysis = _fallback_rules(raw_text)
    case_id = db.create_case(project_id, raw_text, source_type or scope_hint, analysis)
    for r in analysis.get("rules", [])[:6]:
        problem = str(r.get("problem", "")).strip()
        if not problem:
            continue
        check_type = "regex" if r.get("check_type") == "regex" and r.get("check_pattern") else "none"
        check_config: Dict[str, Any] = {}
        if check_type == "regex":
            check_config = {"target": str(r.get("check_target", "") or ""),
                            "mode": "forbid" if r.get("check_mode") == "forbid" else "match",
                            "pattern": str(r.get("check_pattern", "") or ""),
                            "value": 0}
        rules_out.append(db.create_rule(
            case_id=case_id, project_id=project_id,
            category=str(analysis.get("category", "其他")),
            problem=problem, solution=str(r.get("solution", "") or ""),
            check_type=check_type, check_config=check_config))
    return {"case_id": case_id, "analysis": analysis, "rule_ids": rules_out}


async def get_kb_context(project_id: Optional[int]) -> str:
    """生成注入 LLM prompt 的规避清单文本，并返回命中的规则列表供后续计数。"""
    rules = db.list_rules(project_id=project_id, enabled_only=True)
    return prompts.kb_rules_block(rules)


def active_rules(project_id: Optional[int]) -> List[Dict[str, Any]]:
    return db.list_rules(project_id=project_id, enabled_only=True)


def run_regex_rules(rules: List[Dict[str, Any]], targets: Dict[str, str],
                    project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """执行知识库中可正则化的规则，返回问题列表（targets: 字段名→文本）。"""
    issues: List[Dict[str, Any]] = []
    for r in rules:
        if r.get("check_type") != "regex":
            continue
        cfg = db.jloads(r.get("check_config") or "{}", {})
        target = cfg.get("target", "")
        mode = cfg.get("mode", "forbid")
        pattern = cfg.get("pattern", "")
        if target not in targets:
            continue
        text = targets[target] or ""
        if not text.strip():
            continue
        try:
            if mode == "min_length":
                # 纯文本长度校验（去空白后计字数），用于"不少于N字"类规则
                value = int(cfg.get("value") or 0)
                violated = value > 0 and len(re.sub(r"\s+", "", text)) < value
            else:
                if not pattern:
                    continue
                matched = re.search(pattern, text)
                violated = (mode == "forbid" and matched) or (mode == "match" and not matched)
        except (re.error, ValueError):
            continue
        if violated:
            if project_id is not None:
                db.incr_rule_hit(r["id"])
            issues.append({
                "level": "warning",
                "category": r.get("category", "其他"),
                "code": f"KB-{r['id']}",
                "message": "知识库规则命中：" + r.get("problem", ""),
                "suggestion": r.get("solution", ""),
                "source": "knowledge_base",
            })
    return issues
