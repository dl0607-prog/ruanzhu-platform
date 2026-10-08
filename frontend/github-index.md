# GitHub 参考项目索引

> 软著工场内置参考：所有仓库均已通过 GitHub API 逐个核实存在（星标数为核实当日数据）。这些项目全部是"一次性生成"型——生成完材料就结束，**没有任何一家做了「驳回知识库闭环」**，这正是软著工场的差异化壁垒。

## 一、全套材料生成器（AI 驱动）

### 1. [Fokkyp/SoftwareCopyright-Skill](https://github.com/Fokkyp/SoftwareCopyright-Skill) · ⭐ 5715 · Python
- **定位**：Claude/Cursor 形态的 Skills，读取本地项目自动生成全套 .docx 软著材料（申请表信息、操作手册、代码材料），号称"无须付费购买软著服务"。
- **值得借鉴**：把「代码材料只从开发者已有源码中抽取」作为产品原则（杜绝编造代码）；Skill 形态的分发方式；5715 星说明"免代办、自研自提"需求极大。
- **不足**：是 Skill 不是平台，无 Web 界面、无审查闭环、无驳回知识库、无 AI 声明（2026 新规必备材料）生成。

### 2. [duhbbx/miaozhu（秒著）](https://github.com/duhbbx/miaozhu) · ⭐ 104 · Python
- **定位**：最接近软著工场形态的 Web 应用（FastAPI + SQLite + Vue3 + Element Plus），填基本信息后 AI 分章节生成操作说明书、源程序文档、数据库设计文档，导出 Word/PDF，SSE 进度，支持任意 OpenAI 兼容 LLM。
- **值得借鉴**：SSE 章节级进度推送、Markdown 在线编辑+单章重新生成、并发控制（默认 5 LLM 并发）。
- **不足**：无代码分页引擎细节（50行/页硬要求）、无合规审查、无驳回知识库、无 AI 声明，README 明确"生成质量取决于模型"，不带审查视角。

### 3. [na57/chinese-copyright-application-skill](https://github.com/na57/chinese-copyright-application-skill) · ⭐ 186 · Python
- **定位**：完整工具包，从项目代码/文档自动提取信息，生成申请表、源代码文档（前后各 30 页）、用户手册和设计说明书。
- **值得借鉴**：明确区分「用户手册 vs 设计说明书」两种文档鉴别材料（有界面/无界面软件对应不同材料）——软著工场已内置此逻辑。
- **不足**：Skill 形态无平台化、无审查与知识库闭环。

### 4. [flanliulf/AI-Copyright-Application-Generator](https://github.com/flanliulf/AI-Copyright-Application-Generator) · ⭐ 92 · Python
- **定位**：AI 驱动，根据需求文档自动生成软著申请全部材料（技术文档、源代码等）。
- **值得借鉴**：以需求文档为输入源生成材料的工作流。
- **不足**：生成的是"材料草稿"而非合规文档，无格式引擎、无审查。

### 5. [peterfei/ai-agent-team](https://github.com/peterfei/ai-agent-team) · ⭐ 440 · JavaScript
- **定位**：AI 多智能体开发团队框架，内置 [.claude/skills/softcopyright/SKILL.md](https://github.com/peterfei/ai-agent-team/blob/main/.claude/skills/softcopyright/SKILL.md) 软著材料生成 Skill：分析源码生成软件说明书与源代码文档，支持 PDF 导出。
- **值得借鉴**：把软著生成作为"开发流水线的最后一个 Skill"，与 AI 开发流程无缝衔接——这正是软著工场的目标用户场景（只会 AI 写代码的人）。
- **不足**：仅一个 Skill 文件，无格式引擎细节、无审查、无知识库。

## 二、源代码抽取排版工具（专项解决 60 页源程序文档）

### 6. [fanbuz/codesucker](https://github.com/fanbuz/codesucker) · ⭐ 417 · TypeScript
- **定位**：拖入项目文件夹，离线生成 60 页软著源程序文档；注释清洗、自动排版，**导出前先帮你过一遍审查**，代码不出本机（隐私友好）。桌面应用，支持 macOS/Windows。
- **值得借鉴**："导出前自检"的产品思路（与本平台的合规预检同向）；本地离线处理保护代码隐私；60 页文档的排版细节值得对照。
- **不足**：只解决源程序文档一项，无说明书/申请表/AI 声明/知识库。

### 7. [luxel/ramile](https://github.com/luxel/ramile) · ⭐ 335 · Python
- **定位**：中国软件著作权代码自动提取工具，从项目中抽取代码生成鉴别材料。
- **值得借鉴**：代码抽取规则（文件过滤、目录排除）——软著工场的 zip 上传过滤逻辑同源。
- **不足**：单点工具，无全套材料能力。

### 8. [kenley2021/swcr](https://github.com/kenley2021/swcr) · ⭐ 219 · Python
- **定位**：软件著作权程序鉴别材料（源代码文件）生成器。
- **值得借鉴**：程序鉴别材料的命名与分页规范实现。
- **不足**：同单点工具，且较早维护频率低。

## 三、模板与教程（最全的免费模板库）

### 9. [AlexanderZhou01/China-software-copyright](https://github.com/AlexanderZhou01/China-software-copyright) · ⭐ 4541 · None
- **定位**：中国软著申请教程 + 全套原创模板（代码文档、使用说明、设计说明、合作开发协议、材料清单），附 SourceCounter 行数统计工具。
- **值得借鉴**：材料清单核对表；**补正高频错误清单**（双面打印、漏页码、源程序量漏"行"字、误选独立开发、说明文档出现具体用户数据、末页结束符写错、申请表缺流水号需换浏览器打印）；补正组电话 010-84195640 的实战经验。这些已全部沉淀进软著工场的内置种子知识库。
- **不足**：纯静态模板，需要人工逐字套用，无自动化。

### 10. [zephms/ccopyright-software-copyright-application](https://github.com/zephms/ccopyright-software-copyright-application) · ⭐ 250 · None
- **定位**：中国版权保护中心软件著作权申请流程教程（个人申请向）。
- **值得借鉴**：官网系统操作截图流程，适合第一次申请的流程核对。
- **不足**：教程仓库，无工具能力。

## 四、延伸阅读（政策与实战攻略）

- [2026 软著非正常申请严查升级：8 类行为直接驳回](https://www.163.com/dy/article/KPA07UB80511TE3C.html) —— AI 冒充自研、模板化批量、抄袭换皮等红线；补正率超 60%、驳回率同比 +40%。
- [2026 年 3 月 15 日起严禁 AI 生成文档（新规汇总）](https://post.m.smzdm.com/p/apq8wmg7) —— 新版申请表启用与 AI 声明制度。
- [软著申请 AI 声明补正交底：从被卡到一次通过全攻略](https://bbs.csdn.net/weixin_29091445/article/details/100351704) —— 补正被追问时用 Git 记录、开发日志、需求文档证明"人类实质性创作"。
- [软著新规下"人工独创"才是王道](https://zhuanlan.zhihu.com/p/2072615345819596615) —— 并非禁止 AI 辅助，严禁纯 AI 生成且未经人工实质性修改即提交；三重一致性校验。
- [AI 生成代码的软著权属认定：三步破解审核难题](https://juejin.cn/post/7533431517130588160) —— 建立代码版本管理、保存开发过程记录提升通过率。
- [2026 年计算机软件著作权源代码（程序鉴别材料）格式要求](https://blog.csdn.net/King____1/article/details/152415105) —— 前30+后30页、每页不少于50行、页眉须与申请表一致、文档每页30行（截图页除外）。
- [软著宝博客：10 大常见补正问题及应对指南](https://ruanzhubao.com/blogs) —— 文档与源程序不一致、独创性不足、材料格式不符等高频补正情形。

## 五、它们 vs 软著工场

| 能力 | 市面开源项目 | 软著工场 |
|---|---|---|
| 源程序 60 页文档（50行/页、去空行、页眉+页码、末页结束符） | ✅ 仅 codesucker/ramile/swcr 等单点工具 | ✅ 内置引擎 + 导出前自动校验 |
| AI 生成说明书 / 申请表 / 材料 | ✅ 有（生成完即止） | ✅ 有，且**自动注入规避清单** |
| 2026 新规合规预检（三重一致性/AI痕迹词/功能描述≥500字/日期逻辑） | ❌ 全无 | ✅ 内置 35 条规则硬校验 + LLM 软审查 |
| AI 使用情况声明生成 | ❌ 全无（2026-03-15 起必填材料） | ✅ 按"AI辅助+人类实质性创作"口径生成 |
| 开发过程记录（证据链材料） | ❌ 全无 | ✅ 可基于 git log 还原时间线 |
| **驳回知识库闭环**（补正通知→AI 归因→规则沉淀→下次自动规避） | ❌ 全无 | ✅ 核心壁垒，出厂自带 35 条规则，越用越强 |
| Web 平台化（非 Skill/脚本） | 仅秒著接近 | ✅ 完整工作台，一键全套流水线 |
