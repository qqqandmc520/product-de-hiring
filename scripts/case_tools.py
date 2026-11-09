#!/usr/bin/env python3
"""Initialize a candidate ledger or check structural consistency, never judge hiring."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CAPS = {f"P{i}" for i in range(1, 8)}
MODEL = "general-v0.2_p1-v1.1_p2-p7-v1.0_2026-08-31"
STATUSES = {"supported", "partial", "gap", "unobserved"}
KINDS = {"resume_claim", "interview_claim", "scenario_response", "work_sample", "business_data"}


def check(record):
    errors, warnings = [], []

    def error(message):
        errors.append(message)

    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())

    if not isinstance(record, dict):
        return ["记录必须是JSON对象"], []
    for field in ("candidate_id", "role_id", "role_version"):
        if not nonempty(record.get(field)):
            error(f"缺少{field}")
    if record.get("schema_version") != "1.0":
        error("不支持的schema_version")
    if record.get("model_version") != MODEL:
        error("模型版本与技能快照不符，请先核对版本，不要自动改写旧记录")

    def index(items, collection):
        result = {}
        if not isinstance(items, list):
            error(f"{collection}必须是列表")
            return result
        for item in items:
            if not isinstance(item, dict) or not nonempty(item.get("id")):
                error(f"{collection}存在缺少id的条目")
                continue
            if item["id"] in result:
                error(f"{collection}重复ID：{item['id']}")
            result[item["id"]] = item
        return result

    sources = index(record.get("sources"), "sources")
    evidence = index(record.get("evidence"), "evidence")
    requirements = index(record.get("role_requirements"), "role_requirements")
    for sid, source in sources.items():
        for field in ("name", "type", "completeness"):
            if not nonempty(source.get(field)):
                error(f"来源{sid}缺少{field}")
    for rid in requirements:
        if not rid.startswith("R:"):
            error(f"岗位额外要求ID应以R:开头：{rid}")
    valid_tags = CAPS | set(requirements)
    for eid, item in evidence.items():
        if item.get("source_id") not in sources:
            error(f"证据{eid}引用了不存在的来源")
        for field in ("locator", "fact", "speaker"):
            if not nonempty(item.get(field)):
                error(f"证据{eid}缺少{field}")
        choices = {
            "kind": KINDS,
            "verification": {"unverified", "corroborated", "verified"},
            "prompting": {"independent", "neutral_probe", "leading", "not_applicable"},
            "delivery": {"shipped", "pilot", "planned", "hypothetical", "unknown"},
            "direction": {"support", "concern", "neutral"},
        }
        for field, allowed in choices.items():
            if item.get(field) not in allowed:
                error(f"证据{eid}的{field}无效")
        tags = item.get("capabilities")
        if not isinstance(tags, list) or not tags or any(t not in valid_tags for t in tags):
            error(f"证据{eid}的能力/岗位标签无效或为空")
        if item.get("verification") != "unverified" and not nonempty(item.get("verification_note")):
            error(f"证据{eid}须说明核验范围verification_note")

    capabilities = record.get("capabilities")
    if not isinstance(capabilities, dict):
        error("capabilities必须是对象")
        capabilities = {}
    if set(capabilities) != CAPS:
        error("必须保留P1–P7且不能增加第八项；额外要求放role_requirements")

    def review(tag, item, matching_tags=None):
        if not isinstance(item, dict):
            error(f"{tag}评估必须是对象")
            return
        status = item.get("status")
        if status not in STATUSES:
            error(f"{tag}状态无效")
        refs = item.get("evidence_ids")
        if not isinstance(refs, list):
            error(f"{tag}的evidence_ids须为列表")
            refs = []
        for eid in refs:
            if eid not in evidence:
                error(f"{tag}引用不存在的证据：{eid}")
            elif not set(matching_tags or [tag]).intersection(evidence[eid].get("capabilities", [])):
                error(f"{tag}引用证据{eid}但证据未标注该能力/要求")
        linked = [evidence[e] for e in refs if e in evidence]
        if status != "unobserved":
            if not linked or not nonempty(item.get("rationale")):
                error(f"{tag}已有判断须提供证据及rationale")
        if status == "gap":
            if not nonempty(item.get("opportunity")):
                error(f"{tag}判gap须说明实际任务和中性澄清机会opportunity")
            if not any(e.get("direction") == "concern" and e.get("prompting") != "leading" for e in linked):
                error(f"{tag}判gap缺少非诱导的具体问题证据")
        if status == "supported":
            if not any(e.get("direction") == "support" and e.get("prompting") != "leading" for e in linked):
                error(f"{tag}判supported缺少非诱导的支持证据")
            if linked and all(e.get("kind") == "resume_claim" for e in linked):
                warnings.append(f"{tag}仅有简历自述，请人工核对是否应为partial")
        if status in {"unobserved", "partial"} and not nonempty(item.get("follow_up")):
            warnings.append(f"{tag}尚未写明是否需要/如何补证")

    for tag, item in capabilities.items():
        review(tag, item)
    for tag, item in requirements.items():
        review(tag, item)

    # Role standards and candidate evidence remain separate. H: indexes tasks,
    # never adds a capability or supplies an automatic hiring threshold.
    priorities = record.get("hiring_priorities")
    hiring, assessments = {}, {}
    if priorities is None:
        warnings.append("旧记录未含hiring_priorities；按原岗位依据接续分层，不追溯改写历史标准或结论")
    elif not isinstance(priorities, dict):
        error("hiring_priorities须为对象")
    else:
        if priorities.get("role_version") != record.get("role_version"):
            error("hiring_priorities岗位版本须与当前记录一致，不自动套用新标准")
        hiring = index(priorities.get("requirements"), "hiring_priorities.requirements")
        if not hiring:
            warnings.append("尚未记录要求分层；应按岗位依据提炼，不能从候选人强弱倒定标准")
        for hid, item in hiring.items():
            if not hid.startswith("H:") or len(hid) <= 2:
                error(f"招聘要求ID应以H:开头且有名称：{hid}")
            for field in ("name", "reason", "minimum", "verification", "basis"):
                if not nonempty(item.get(field)):
                    error(f"招聘要求{hid}缺少{field}")
            if item.get("level") not in {"core", "required", "developable", "bonus"}:
                error(f"招聘要求{hid}层级无效")
            tags = item.get("capabilities")
            if not isinstance(tags, list) or not tags or any(t not in valid_tags for t in tags):
                error(f"招聘要求{hid}关联能力/独立要求无效")
            if item.get("level") == "developable" and not nonempty(item.get("development_plan")):
                warnings.append(f"可培养要求{hid}未说明支持、节点与验收；不能假定自然补齐")
        priority_fit = record.get("role_fit")
        if isinstance(priority_fit, dict) and priority_fit.get("role_orientation") == "product_led" and hiring:
            if not any(i.get("level") == "core" and isinstance(i.get("capabilities"), list) and CAPS.intersection(i["capabilities"]) for i in hiring.values()):
                warnings.append("产品主导岗位未记录关联产品能力的核心要求，请核对招聘定位")
        raw_assessments = priorities.get("assessments")
        if not isinstance(raw_assessments, list):
            error("hiring_priorities.assessments须为列表")
        else:
            for item in raw_assessments:
                if not isinstance(item, dict):
                    error("招聘要求评估须为对象")
                    continue
                hid = item.get("requirement_id")
                if not isinstance(hid, str) or hid not in hiring:
                    error("招聘要求评估引用不存在的H:要求")
                    continue
                if hid in assessments:
                    error(f"招聘要求评估重复：{hid}")
                assessments[hid] = item
                mapped_tags = hiring[hid].get("capabilities")
                review(hid, item, mapped_tags if isinstance(mapped_tags, list) else [])
        for hid, item in hiring.items():
            if item.get("level") in {"core", "required"} and hid not in assessments:
                warnings.append(f"关键/必需要求{hid}尚无本轮评估；不代表能力缺口")

    # Optional extension: preserve compatibility with v0.1/v0.2 ledgers.
    fit = record.get("role_fit")
    if fit is None:
        warnings.append("旧记录未含role_fit；接续评估时补岗位属性与产品/业务适配，不自动改写历史结论")
    elif not isinstance(fit, dict):
        error("role_fit须为对象")
    else:
        orientation = fit.get("role_orientation")
        if orientation not in {"product_led", "business_led", "hybrid", "undetermined"}:
            error("role_fit岗位属性无效")
        elif orientation != "undetermined" and not nonempty(fit.get("role_basis")):
            error("role_fit已判断岗位属性须有role_basis")
        if fit.get("candidate_evidence_focus") not in {"product", "business", "both", "insufficient"}:
            error("role_fit候选人证据侧重无效")
        for axis in ("product_fit", "domain_fit"):
            item = fit.get(axis)
            if not isinstance(item, dict):
                error(f"role_fit.{axis}须为对象")
                continue
            status = item.get("status")
            allowed = STATUSES | ({"not_required"} if axis == "domain_fit" else set())
            if status not in allowed:
                error(f"role_fit.{axis}状态无效")
            refs = item.get("evidence_ids")
            if not isinstance(refs, list) or any(e not in evidence for e in refs):
                error(f"role_fit.{axis}证据引用无效")
                continue
            if status != "unobserved" and not nonempty(item.get("rationale")):
                error(f"role_fit.{axis}已有判断须有rationale")
            if status in {"supported", "partial", "gap"} and not refs:
                error(f"role_fit.{axis}已有能力判断须引用证据")
            if axis == "product_fit" and status in {"supported", "partial", "gap"} and refs:
                linked = [evidence[e] for e in refs]
                if not any(CAPS.intersection(e.get("capabilities", [])) for e in linked):
                    error("产品适配不能只引用独立业务要求证据")
            relevant = [evidence[e] for e in refs if axis != "product_fit" or CAPS.intersection(evidence[e].get("capabilities", []))]
            if status == "supported" and refs and not any(
                e.get("direction") == "support" and e.get("prompting") != "leading"
                for e in relevant
            ):
                error(f"role_fit.{axis}缺少非诱导支持证据")
            if status == "gap" and refs and not any(
                e.get("direction") == "concern" and e.get("prompting") != "leading"
                for e in relevant
            ):
                error(f"role_fit.{axis}缺少非诱导问题证据")

    decisions = record.get("decisions")
    if not isinstance(decisions, list):
        error("decisions须为列表")
        decisions = []
    if decisions and isinstance(fit, dict):
        if fit.get("role_orientation") == "undetermined":
            warnings.append("岗位属性尚不明确；请核对去留结论是否超出当前依据")
        if not nonempty(fit.get("scope_note")):
            warnings.append("role_fit尚未说明产品/业务判断范围与局限scope_note")
    verdicts = {"screening": {"invite", "pending_evidence", "do_not_invite"}, "post_interview": {"advance", "supplement", "do_not_advance"}}
    for decision in decisions:
        if not isinstance(decision, dict):
            error("decision须为对象")
            continue
        if decision.get("verdict") not in verdicts.get(decision.get("stage"), set()):
            error("决策stage/verdict不匹配")
        for field in ("date", "role_version", "rationale", "uncertainty"):
            if not nonempty(decision.get(field)):
                error(f"决策缺少{field}")
        refs = decision.get("evidence_ids")
        if not isinstance(refs, list) or any(e not in evidence for e in refs):
            error("决策证据引用无效")
        elif not refs and decision.get("verdict") not in {"pending_evidence", "supplement"}:
            error("实质去留建议须引用证据")
        hids = decision.get("requirement_ids")
        if decision.get("role_version") == record.get("role_version"):
            if hids is None:
                if hiring:
                    warnings.append("当前决策未关联H:要求，请人工核对最低表现与阶段影响")
            elif not isinstance(hids, list) or any(not isinstance(h, str) or h not in hiring for h in hids):
                error("当前决策的requirement_ids引用无效")
            elif decision.get("verdict") in {"do_not_invite", "do_not_advance"} and hids:
                decisive = [h for h in hids if hiring[h].get("level") in {"core", "required"}]
                if not decisive:
                    warnings.append("否定建议仅关联可培养/加分要求；请核对是否误作淘汰条件")
                elif not any(assessments.get(h, {}).get("status") == "gap" for h in decisive):
                    warnings.append("否定建议关联的核心/必需要求尚无gap；请区分材料不足与已知不匹配，人工核对阶段理由")
        # Historical decisions retain their own role version and requirement IDs.

    plan = record.get("interview_plan")
    if plan is not None:
        if not isinstance(plan, dict) or not isinstance(plan.get("segments"), list):
            error("interview_plan须含segments列表")
        else:
            total, covered, planned_requirements = 0, set(), set()
            for segment in plan["segments"]:
                if not isinstance(segment, dict):
                    error("面试时间段须为对象")
                    continue
                minutes = segment.get("minutes")
                if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or minutes <= 0:
                    error("面试段minutes须大于0")
                else:
                    total += minutes
                tags = segment.get("capabilities", [])
                if not isinstance(tags, list) or any(t not in valid_tags for t in tags):
                    error("面试段能力标签无效")
                else:
                    covered.update(tags)
                hids = segment.get("requirement_ids", [])
                if not isinstance(hids, list) or any(not isinstance(h, str) or h not in hiring for h in hids):
                    error("面试段requirement_ids引用无效")
                else:
                    planned_requirements.update(hids)
            target = plan.get("duration_minutes")
            if isinstance(target, bool) or not isinstance(target, (int, float)) or target <= 0 or total != target:
                error(f"面试时间合计{total}与约定时长{target}不一致")
            if CAPS - covered:
                warnings.append("面试计划未覆盖：" + ",".join(sorted(CAPS - covered)) + "；应说明后续观察安排")
            missing_core = {h for h, i in hiring.items() if i.get("level") == "core"} - planned_requirements
            if missing_core:
                warnings.append("本轮计划未关联核心要求：" + ",".join(sorted(missing_core)) + "；说明前轮依据或后续安排，标签不代表已充分观察")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="建立空白记录，不覆盖已有文件")
    init.add_argument("path", type=Path)
    for field in ("candidate-id", "role-id", "role-version"):
        init.add_argument("--" + field, required=True)
    validate = commands.add_parser("check", help="检查结构及引用，不判定招聘结论")
    validate.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "init":
            record = json.loads((ROOT / "assets" / "candidate-record.json").read_text(encoding="utf-8"))
            for field in ("candidate_id", "role_id", "role_version"):
                value = getattr(args, field)
                if not value.strip():
                    raise ValueError(f"{field}不能为空")
                record[field] = value
            record["hiring_priorities"]["role_version"] = record["role_version"]
            args.path.parent.mkdir(parents=True, exist_ok=True)
            with args.path.open("x", encoding="utf-8") as stream:
                json.dump(record, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            print(f"已建立记录：{args.path}")
            return
        errors, warnings = check(json.loads(args.path.read_text(encoding="utf-8")))
        print(json.dumps({"structural_check": "failed" if errors else "passed", "errors": errors, "warnings": warnings, "limit": "只检查记录一致性，不验证原文内容、事实真伪或招聘判断。"}, ensure_ascii=False, indent=2))
        if errors:
            sys.exit(1)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
