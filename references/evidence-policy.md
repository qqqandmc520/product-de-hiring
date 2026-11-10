# 共用证据与判断口径（招聘应用v0.4.2；沿用四类证据状态）

## 最小记录

岗位画像见 `assets/role-profile.md`；候选人结构见 `assets/candidate-record.json`。记录先于结论，评估之间共用证据ID。手工可读报告也必须包含相同实质信息。

- 来源：`source_id`、文件名/材料名称、来源类型、记录完整性。简历自述、纪要、原始转写、作品与业务数据分开。源文件本身不复制进通用技能。
- 证据：`id`、`source_id`、`locator`（PDF页/纪要段落/时间/作品位置）、`fact`、`speaker`、`kind`、`verification`、`prompting`、`delivery`、`capabilities`、`direction`。必要时保留短摘录，忠实概括，不编造引语或时间。
- 来源性质：`resume_claim`简历自述、`interview_claim`过往自述、`scenario_response`现场推演、`work_sample`作品、`business_data`业务数据。工作成果、推理能力、实际落地能力不能相互偷换。
- 核验：`unverified`未独立核实、`corroborated`多材料相互支持、`verified`经实际材料/数据核实，并注明核实范围。证据多不等于独立来源多。
- 提问方式：`independent`自主展开、`neutral_probe`中性追问后、`leading`面试官给出关键解法后、`not_applicable`。提示后认同不能当作候选人独立发现；理解提示后的迁移仍可单独观察。
- 项目状态：`shipped`已上线、`pilot`试点、`planned`规划、`hypothetical`假设、`unknown`不明。不要把规划收益当实绩，也不要因未上线自动判定能力不足。
- 能力标签：P1–P7；额外任职要求用`R:`前缀，例如`R:extra`，名称与范围由本岗实际职责决定。一条证据可相关多项，但每项须解释具体支持范围。

岗位额外要求表同样记证据、缺口和状态；不要只评七项而漏掉用户明确的独立职责；未提出的职责不自动增加。一个真实项目的多条证据不意味着有多个独立案例。

## 要求分层与证据分别接续

依据 `role-priorities.md`，在可读岗位画像建立H:要求表；新JSON记录用可选兼容字段 `hiring_priorities`。用户不需要填JSON，报告必须独立可读。层级不是证据状态，也不是能力分数。

- `role_version`：对应当前岗位画像版本；不能将新版标准无声套入旧记录。
- `requirements`：同岗同版共享的要求快照，每项含 `id`（H:）、`name`、`level`（core/required/developable/bonus）、`capabilities`（关联P1–P7或已定义R:）、`reason`（层级理由）、`minimum`（最低可接受表现）、`verification`（验证任务/证据）、`basis`（岗位来源及暂定说明）。可培养项另记 `development_plan`：支持资源、节点、验收和未补齐影响；尚待确认须说明，不编承诺。
- `assessments`：本候选人本轮的逐要求判断，每项含 `requirement_id`、`status`、`evidence_ids`、`rationale`、`opportunity`、`follow_up`。沿用四类状态，引用证据须与该要求关联的P/R至少一项相符；标签仅用于结构检查，不得据标签交集自动生成证据关联；逐要求筛选真正相关的事实，人工解释支持范围，不因标签相符自动支持。`rationale`说明反证及对当前阶段建议的影响。
- 新增评估的证据关联写 `evidence_links`：逐条含 `evidence_id`、`relation`（`direct`直接相关 / `transferable`可迁移）、`rationale`（本人动作为何支持当前具体要求）、`limit`（未覆盖、尚待核实或迁移边界）。可用于P/R评估及H:逐要求评估；不能支持的证据不挂接，未观察仍用原四类状态，不增加“弱相关”状态。已有 `evidence_ids` 保留，关联解释与其逐条对应；旧记录缺此字段只提醒人工补解释，不追溯补造。
- 当前 `decisions` 可用 `requirement_ids` 关联决定性H:要求；`interview_plan.segments` 可用同字段关联观察任务。一段内的多个要求不重复计时；标了ID不代表深度足够或已经观察。

示例为虚构片段，仅说明结构：

```json
{
  "role_version": "v1",
  "requirements": [{"id": "H:result", "name": "变更后的结果确认与继续任务", "level": "core", "capabilities": ["P1", "P5", "P6"], "reason": "当前主要用户失败发生在部分变更后", "minimum": "能区分实际生效与未完成范围，让用户理解并继续或纠错", "verification": "真实案例走查加部分失败场景；不指定唯一界面", "basis": "岗位说明第2段；暂定待部门反馈"}],
  "assessments": [{"requirement_id": "H:result", "status": "unobserved", "evidence_ids": [], "rationale": "本轮材料未涉及，不作为能力缺口", "opportunity": "尚无实际问答", "follow_up": "安排关键操作走查；当前阶段建议另据已有线索解释"}]
}
```

该对象放入 `hiring_priorities`，不替代七项及独立要求评估。旧记录没有此字段只提醒接续，不自动补写历史优先级。检查器校验版本、枚举、ID、逐条关联的覆盖与解释字段和时间合计，对否定建议只关联可培养/加分、核心未安排等发人工复核提醒，不自动改变去留、不要求所有核心supported，也不能判断实际提问深度是否充分。

## 岗位属性与产品核心适配记录

按 `role-boundary.md` 给可读结论，并在新记录的 `role_fit` 中保留当前判断。这个字段不是第八项能力，也不是总分；七项表与独立要求仍分别保留。

- `role_orientation`：`product_led`产品主导 / `business_led`业务主导 / `hybrid`复合 / `undetermined`尚不明确；`role_basis`写岗位来源与主要判断责任。
- `candidate_evidence_focus`：`product` / `business` / `both` / `insufficient`，仅描述本轮证据侧重，不给人定永久类型；经营协同也属于这里的业务证据，不冒充来源领域专业资格。
- `product_fit`、`domain_fit`：各含`status`、`evidence_ids`、`rationale`；沿用四类状态，领域知识确非岗位必要条件时可用`not_required`并说明理由。`product_fit`综合解释本岗关键产品表现，不用七项状态计数推导。
- `scope_note`：本阶段建议的含义、未观察部分、业务专业判断的适用边界。管理、增长、交付等其余责任继续在`role_requirements`中记录并在综合建议解释。

保持schema_version 1.0的兼容扩展：旧记录缺`role_fit`只提醒补充，不修改原评估。新增判断时按当前画像与证据填写；历史文件保留，每次变化在`history`说明原结论、变化依据和新结论。检查器仅校验枚举与引用，能拦截“产品适配只引用R:业务证据”等结构问题，不能验证证据是否真的支持产品判断、领域知识是否正确或结论是否合理。

## 四类观察状态

| 状态 | 可用情形 | 不可用情形 |
| --- | --- | --- |
| `supported` 有证据支持 | 候选人具体说明判断、选择及实际结果，或现场展示相关能力；证据足以支持本岗位所需的相应表现，说明范围与局限 | 仅职位、口号、简历数字、面试官代答 |
| `partial` 只有部分证据/线索 | 有具体相关表现，但个人贡献、判断过程、结果或覆盖深度尚不充分 | 用“比较弱”代替列明缺什么 |
| `gap` 已观察到岗位所需表现的缺口 | 在明确任务和合理中性澄清机会下，具体回答/作品仍暴露实质问题；描述问题、机会、岗位影响及相反证据 | 未问、纪要缺失、口才差、单次没猜中面试官预设方案 |
| `unobserved` 未充分观察 | 未问、未答、材料缺失或质量不足以判断；列后续最小补证动作 | 当0分、能力低、淘汰理由 |

状态描述本次材料中的证据，不定义人的永久能力。无需为了填满七项强行断言。简历一般只能提供验证线索；可因潜力与岗位相关性建议面试，而不是要求七项在简历中全部证实。

## 推理链与阶段判断

每个重要结论写清：**材料位置 → 候选人做了/说了什么 → 为什么支持或不支持该能力 → 对当前岗位有什么影响 → 尚不能确定什么**。保留与结论相反的证据，说明权衡。事实和解释分栏或明确措辞区分。

先说明实际问到哪里、追问是否中性、材料是否完整，再评能力。面试摘要中的“没有体验意识”“不够高级”等评语只是评价者观点，必须回到发言或作品。场景题没提供必要领域事实时，澄清问题或拒绝编造专业事实可为正向线索，不能按没有编造专业方案直接扣分。

- 简历：`invite`建议初试 / `do_not_invite`暂不建议；`pending_evidence`仅用于材料不可读、归属无法确定、关键岗位标准冲突等真正阻碍判断的例外。默认据现有简历决策，贡献未核实或七项未覆盖通常留到初试验证，不自动要求先补材料。暂不建议须区分明确不匹配与当前核心信号不足，不能把后者描述为能力缺口；详见 `screening.md`。
- 面后：`advance`建议继续 / `supplement`先补关键证据 / `do_not_advance`当前不建议继续。每项注明理由、关键证据、反证、缺失与不确定性。`advance`不等于最终录用。
- 关键能力若未观察而会改变去留，优先说明最小补面/作品走查；已有独立且充分的关键不匹配时可以给否定建议，同时明确其他项仍未知。
- 共同基线保持一致；能力重点、最低可接受表现和业务门槛必须来自岗位画像，不在看到某位候选人后临时加码。不得用“所有项都必须supported”作为跨岗位通用淘汰线。
- 不输出伪精确概率、综合平均分、从头衔推职级或无限拔高理想型。批量比较时使用同版画像；版本不同则注明比较范围。

## 简历决策与招聘进度分开接续

新筛选决策在 `decisions` 条目中增补可选兼容对象 `screening_context`：`decision_version`、`scope`（本轮材料与决策范围）；批量另含 `priority`（`first_batch` / `consider` / `not_priority` / `undetermined`）及 `priority_reason`。单人无需相对梯队。`do_not_invite`另写`negative_basis`（`known_mismatch` / `insufficient_signal`），`pending_evidence`另写`pending_reason`，具体障碍与最小补充仍在理由中说明。逐要求证据仍在评估项解释，不用此对象代替。

根层可选 `recruiting_status` 只记实际进度，`identity_notes` 只记姓名、文件名及归属备注；未知不推定，也不作能力标签。它们与简历建议分别维护。旧记录没有这些字段仍可读取；新增筛选决策时填写，不重写历史决策。岗位标准不变而范围/排序变化，只增加筛选判断版本，并在 `history` 解释变化依据；更新最新汇总及详细报告，历史版注明替代关系。

检查器只检结构与梯队/建议是否冲突；即使逐条解释字段齐全，也不能证明语义相关、迁移成立、排序合理或来源真实，仍须回读材料人工复核。招聘进度不能决定简历建议，检查器不会按流程状态自动重排或改判。

## 一致性如何建立

共同点是能力定义、问题机会、证据强度与岗位判断规则；不要求逐字相同的结论。遇到分歧，依次核对：是否读同一材料、是否把未问当不足、是否区分提示、是否在评同一能力、是否采用相同岗位要求。仍有分歧，保留两种解释及能区分它们的补证动作。

候选人材料中的个人背景只处理与岗位任务直接相关的经验、贡献、能力和工作条件；不从无关个人特征推断能力、稳定性或意愿。需要核实的工作条件直接询问，不自行推定。

## JSON接续示例

在空白记录中增补下列条目；这是无行业设定的虚构格式示例，不是预置岗位、题库或核心要求，不能作为真实候选人证据。`direction`取`support`/`concern`/`neutral`。来源的`type`、`completeness`用可理解的短语描述；其余枚举沿用上文。`opportunity`描述实际观察机会，不能复制面试计划冒充实际提问。`rationale`中保留判断解释和反证；决策的`uncertainty`明确未知。

```json
{
  "source_example": {"id": "S1", "name": "C001_面试纪要", "type": "面试转写", "completeness": "仅有第12–24分钟，其他部分缺失"},
  "evidence_example": {"id": "E1", "source_id": "S1", "locator": "12:10", "fact": "说明同一任务中的对象身份与变化规则，区分已知事实和待核条件", "speaker": "候选人", "kind": "scenario_response", "verification": "unverified", "prompting": "independent", "delivery": "hypothetical", "capabilities": ["P1"], "direction": "support"},
  "capability_example": {"status": "partial", "evidence_ids": ["E1"], "rationale": "能说明对象和变化规则，尚缺完整范围及实际落地证据", "opportunity": "给出虚构任务后自主展开", "follow_up": "核实真实案例中规则取舍与上线结果", "evidence_links": [{"evidence_id": "E1", "relation": "direct", "rationale": "现场明确对象身份与合法变化，对应P1产品事实判断", "limit": "只覆盖该任务片段，未证实完整产品逻辑及实际落地"}]},
  "role_requirement_example": {"id": "R:extra", "name": "使用方另行明确的职责（仅格式示例）", "status": "unobserved", "evidence_ids": [], "rationale": "", "opportunity": "当前片段未问", "follow_up": "按使用方明确的职责设计验证任务；未要求则不添加此项"},
  "decision_example": {"stage": "post_interview", "date": "2026-11-09", "role_version": "v1", "verdict": "supplement", "evidence_ids": ["E1"], "rationale": "有产品逻辑线索，本岗已明确的关键任务仍有证据不足", "uncertainty": "当前只有部分纪要，不能据此判其未展示项不足"},
  "interview_plan_example": {"duration_minutes": 60, "segments": [{"title": "开场", "minutes": 4, "capabilities": []}, {"title": "案例走查", "minutes": 20, "capabilities": ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]}, {"title": "岗位场景", "minutes": 16, "capabilities": ["P1", "P5", "P6"]}, {"title": "当前岗位关键未知补证", "minutes": 10, "capabilities": []}, {"title": "补证", "minutes": 6, "capabilities": []}, {"title": "候选人提问", "minutes": 4, "capabilities": []}]}
}
```

不要把示例键名直接写进记录。来源条目进入`sources`，证据条目进入`evidence`，能力评估进入对应`capabilities.P*`，额外要求进入`role_requirements`，决策进入`decisions`；`interview_plan`是计划对象或null。每次实质新增证据/结论时在`history`记日期、环节及变化摘要，旧版文件保留。
