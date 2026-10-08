"""Sourced knowledge, reconciled on startup without replacing user case rules."""
import json
from pathlib import Path

CHECKED_AT = "2026-10-08"
LAW = "https://www.ncac.gov.cn/xxfb/flfg/bmgz/202410/t20241015_869486.html"
ONLINE = "https://www.ccct.net.cn/html/bqzx/2023/0531/4368.html"
CASES = "https://help.aliyun.com/zh/copyright-and-patent-service/software-copyright-registration/support/amendments-of-software-copyright-registration/"


def rule(key, category, problem, solution, url, source_kind, reference):
    return dict(key=key, category=category, problem=problem, solution=solution,
                check_type="none", source_url=url, source_kind=source_kind,
                reference=reference, checked_at=CHECKED_AT)


SEED_RULES = [
    rule("materials", "材料缺失", "缺少申请表、鉴别材料或证明文件", "按项目实际情况逐项备齐，不以本平台预填稿代替官网申请表。", LAW, "官方规定", "第9条"),
    rule("pages", "格式规范", "鉴别材料取页范围不正确", "一般交存取前后各30页，不足60页提交全部；程序每页通常至少50行、文档30行。不得凑造代码。", LAW, "官方规定", "第10条"),
    rule("ownership", "材料缺失", "身份证明或权属证据不齐", "核对身份证明；涉及合作、委托、许可修改或继受时准备相应权属文件。", LAW, "官方规定", "第11条"),
    rule("confidential", "其他", "源码包含不宜公开的商业秘密", "先核对例外交存或封存途径，勿自行随意删改待交存材料。", LAW, "官方规定", "第12、13条"),
    rule("signature", "格式规范", "申请表格式、签章或译本有缺漏", "使用官方表格，完成签名或盖章，外文证明附中文译本。", LAW, "官方规定", "第17条"),
    rule("identity", "材料一致性", "文件名称或权利人署名不一致", "核对全部材料中的软件名称与署名；有差异时准备解释证明。", LAW, "官方规定", "第21条"),
    rule("deadline", "其他", "收到补正后错过处理期限", "登记办法规定30日内补正；记录通知及指定期限，逾期未补正视为撤回。", LAW, "官方规定", "第22条"),
    rule("online", "其他", "仍按旧流程邮寄纸质材料", "2023年6月起按系统提示在线填报和上传，当前细节以官网办理页面为准。", ONLINE, "官方通知转载", "版权中心2023-05-25通知"),
    rule("core", "材料一致性", "只提交框架代码，缺少业务实现", "逐项对照功能清单，提交体现真实业务的自有代码，核对依赖许可。", CASES, "服务商补正经验", "通用框架程序"),
    rule("correspondence", "材料一致性", "说明书功能与源程序不对应", "建立功能—文件—截图对应关系，删除未经实现的功能描述。", CASES, "服务商补正经验", "文档与源程序不符"),
    rule("ending", "格式规范", "源程序最后一个模块被截断", "核对末页来自真实代码结尾；不要通过补括号伪造完整性。", CASES, "服务商补正经验", "最后一页未结尾"),
    rule("manual", "功能描述不足", "操作步骤不连贯或截图不真实", "按实际入口、操作、结果编写，使用运行截图；无界面软件写设计说明。", CASES, "服务商补正经验", "说明文档与截图"),
    rule("upgrade", "材料缺失", "升级或修改软件未说明原版本情况", "核实既有登记和权利来源，按实际情况填写修改说明与授权文件。", CASES, "服务商补正经验", "升级版核实"),
    rule("language", "材料一致性", "申请表漏填实际编程语言", "逐一核对源码语言；只填实际使用的语言。", CASES, "服务商补正经验", "编程语言遗漏"),
]


def seed_if_empty(db):
    """升级旧内置规则，保留用户案例、用户修改与启停选择。"""
    legacy = set(json.loads(Path(__file__).with_name('legacy_seed_problems.json').read_text()))
    existing = db.list_rules()
    keys = set()
    for r in existing:
        cfg = db.jloads(r.get('check_config') or '{}', {})
        if cfg.get('seed_key'):
            keys.add(cfg['seed_key'])
        if r.get('case_id') is None and r.get('project_id') is None and r['problem'] in legacy:
            db.update_rule(r['id'], {'enabled': False})
    count = 0
    for r in SEED_RULES:
        if r['key'] in keys:
            continue
        cfg = {k: r[k] for k in ('source_url', 'source_kind', 'reference', 'checked_at')}
        cfg['seed_key'] = r['key']
        db.create_rule(None, None, r['category'], r['problem'], r['solution'], 'none', cfg)
        count += 1
    return count
