#!/usr/bin/env python3
"""Regression checks for ledger compatibility and requirement/evidence boundaries."""
import copy
import json
from pathlib import Path
import unittest

from case_tools import check

ROOT = Path(__file__).resolve().parents[1]


def record():
    result = json.loads((ROOT / "assets/candidate-record.json").read_text(encoding="utf-8"))
    result.update(candidate_id="C-fictional", role_id="ROLE-fictional", role_version="v1")
    result["hiring_priorities"]["role_version"] = "v1"
    for item in result["capabilities"].values():
        item["follow_up"] = "本轮未覆盖，按岗位重要性另排"
    result["sources"] = [{"id": "S1", "name": "虚构问答", "type": "测试", "completeness": "仅供结构检查"}]
    return result


def requirement(result, level="core"):
    result["hiring_priorities"]["requirements"] = [{
        "id": "H:task", "name": "结果确认", "level": level,
        "capabilities": ["P5"], "reason": "主要用户问题",
        "minimum": "区分已生效与失败范围，支持纠错", "verification": "具体操作走查",
        "basis": "虚构岗位说明v1",
    }]


def evidence(result, tag="P5", direction="support", prompting="independent"):
    result["evidence"] = [{
        "id": "E1", "source_id": "S1", "locator": "第1段", "fact": "虚构的具体任务回答",
        "speaker": "候选人", "kind": "scenario_response", "verification": "unverified",
        "prompting": prompting, "delivery": "hypothetical", "capabilities": [tag], "direction": direction,
    }]


def assessment(result, status="partial"):
    result["hiring_priorities"]["assessments"] = [{
        "requirement_id": "H:task", "status": status, "evidence_ids": ["E1"],
        "rationale": "具体证据及岗位影响，范围尚有限", "opportunity": "明确任务后中性追问",
        "follow_up": "补真实案例验证结果",
    }]


def decision(result, verdict="invite"):
    result["decisions"] = [{
        "stage": "screening", "verdict": verdict, "date": "2026-11-09", "role_version": "v1",
        "rationale": "仅作当前阶段建议", "uncertainty": "尚需核实本人判断与效果",
        "evidence_ids": ["E1"], "requirement_ids": ["H:task"],
    }]


class LedgerChecks(unittest.TestCase):
    def test_legacy_records_preserve_content(self):
        result = record()
        del result["hiring_priorities"]
        del result["role_fit"]
        before = copy.deepcopy(result)
        errors, warnings = check(result)
        self.assertEqual(errors, [])
        self.assertTrue(any("旧记录" in w for w in warnings))
        self.assertEqual(result, before)

    def test_partial_core_can_support_invitation(self):
        result = record()
        requirement(result)
        evidence(result)
        assessment(result)
        decision(result)
        self.assertEqual(check(result)[0], [])
        self.assertTrue(all(i["status"] == "unobserved" for i in result["capabilities"].values()))

    def test_current_role_version_cannot_silently_change(self):
        result = record()
        result["hiring_priorities"]["role_version"] = "v2"
        self.assertTrue(any("版本" in e for e in check(result)[0]))

    def test_undefined_requirement_assessment_fails(self):
        result = record()
        evidence(result)
        assessment(result)
        self.assertTrue(any("不存在的H:" in e for e in check(result)[0]))

    def test_duplicate_requirement_assessment_fails(self):
        result = record()
        requirement(result)
        evidence(result)
        assessment(result)
        result["hiring_priorities"]["assessments"] *= 2
        self.assertTrue(any("重复" in e for e in check(result)[0]))

    def test_evidence_must_match_requirement_scope(self):
        result = record()
        requirement(result)
        evidence(result, tag="P1")
        assessment(result)
        self.assertTrue(any("未标注" in e for e in check(result)[0]))

    def test_gap_needs_nonleading_concern_and_actual_opportunity(self):
        result = record()
        requirement(result)
        evidence(result, direction="concern", prompting="leading")
        assessment(result, status="gap")
        result["hiring_priorities"]["assessments"][0]["opportunity"] = ""
        errors, _ = check(result)
        self.assertTrue(any("中性澄清机会" in e for e in errors))
        self.assertTrue(any("非诱导" in e for e in errors))

    def test_bonus_only_rejection_requires_human_review(self):
        result = record()
        requirement(result, level="bonus")
        evidence(result, direction="concern")
        assessment(result, status="gap")
        decision(result, verdict="do_not_invite")
        errors, warnings = check(result)
        self.assertEqual(errors, [])
        self.assertTrue(any("误作淘汰条件" in w for w in warnings))
        self.assertEqual(result["decisions"][0]["verdict"], "do_not_invite")

    def test_unknown_core_is_not_automatically_gap(self):
        result = record()
        requirement(result)
        evidence(result)
        assessment(result, status="unobserved")
        decision(result, verdict="do_not_invite")
        errors, warnings = check(result)
        self.assertEqual(errors, [])
        self.assertTrue(any("区分材料不足" in w for w in warnings))
        self.assertEqual(result["hiring_priorities"]["assessments"][0]["status"], "unobserved")

    def test_developable_needs_real_support_plan(self):
        result = record()
        requirement(result, level="developable")
        errors, warnings = check(result)
        self.assertEqual(errors, [])
        self.assertTrue(any("支持、节点与验收" in w for w in warnings))

    def test_current_decision_cannot_reference_unknown_requirement(self):
        result = record()
        evidence(result)
        decision(result)
        self.assertTrue(any("requirement_ids" in e for e in check(result)[0]))

    def test_historical_decision_keeps_old_requirement_ids(self):
        result = record()
        evidence(result)
        decision(result)
        result["decisions"][0]["role_version"] = "old-v0"
        self.assertEqual(check(result)[0], [])

    def test_core_without_planned_task_warns_but_does_not_judge(self):
        result = record()
        requirement(result)
        result["interview_plan"] = {"duration_minutes": 60, "segments": [
            {"title": "现有计划", "minutes": 60, "capabilities": ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]}
        ]}
        errors, warnings = check(result)
        self.assertEqual(errors, [])
        self.assertTrue(any("未关联核心要求" in w for w in warnings))

    def test_shared_task_time_is_not_counted_per_requirement(self):
        result = record()
        requirement(result)
        extra = copy.deepcopy(result["hiring_priorities"]["requirements"][0])
        extra["id"] = "H:other"
        result["hiring_priorities"]["requirements"].append(extra)
        result["interview_plan"] = {"duration_minutes": 60, "segments": [
            {"minutes": 56, "capabilities": ["P1", "P2", "P3", "P4", "P5", "P6", "P7"], "requirement_ids": ["H:task", "H:other"]},
            {"minutes": 4, "capabilities": [], "requirement_ids": []},
        ]}
        self.assertEqual(check(result)[0], [])
        result["interview_plan"]["segments"][0]["minutes"] = 60
        self.assertTrue(any("时间合计" in e for e in check(result)[0]))

    def test_business_only_core_does_not_verify_product_fit(self):
        result = record()
        result["role_requirements"] = [{"id": "R:extra", "status": "unobserved", "evidence_ids": [], "follow_up": "另验"}]
        requirement(result)
        result["hiring_priorities"]["requirements"][0]["capabilities"] = ["R:extra"]
        evidence(result, tag="R:extra")
        assessment(result)
        result["role_fit"]["product_fit"] = {"status": "supported", "evidence_ids": ["E1"], "rationale": "误用增长证据"}
        self.assertTrue(any("不能只引用独立业务" in e for e in check(result)[0]))


if __name__ == "__main__":
    unittest.main()
