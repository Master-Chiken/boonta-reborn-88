"""Offline regression tests for the declarative agent role registry."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("check_agent_roles.py")
SPEC = importlib.util.spec_from_file_location("check_agent_roles", MODULE_PATH)
roles = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(roles)
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "docs/automation/agent-roles.json"


class AgentRoleRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_repository_registry_is_valid(self):
        self.assertEqual(roles.validate_registry(self.valid), [])

    def test_rejects_missing_manager(self):
        data = copy.deepcopy(self.valid)
        data["roles"][1]["manager_id"] = "missing"
        self.assertTrue(any("existing manager_id" in error for error in roles.validate_registry(data)))

    def test_rejects_manager_cycle(self):
        data = copy.deepcopy(self.valid)
        data["roles"][1]["manager_id"] = "ceo"
        self.assertTrue(any("cycle" in error for error in roles.validate_registry(data)))

    def test_requires_single_human_root(self):
        data = copy.deepcopy(self.valid)
        data["roles"][1]["manager_id"] = None
        self.assertTrue(any("only root" in error for error in roles.validate_registry(data)))

    def test_requires_independent_qa(self):
        data = copy.deepcopy(self.valid)
        next(role for role in data["roles"] if role["id"] == "qa")["manager_id"] = "cto"
        self.assertTrue(any("QA must not report" in error for error in roles.validate_registry(data)))

    def test_deterministic_operations_controller(self):
        data = copy.deepcopy(self.valid)
        next(role for role in data["roles"] if role["id"] == "chief-of-staff")["kind"] = "model_role"
        self.assertTrue(any("chief-of-staff must be deterministic" in error for error in roles.validate_registry(data)))

    def test_rejects_provider_order_or_paid_fallback_drift(self):
        data = copy.deepcopy(self.valid)
        data["provider_order"] = ["groq_free", "gemini", "openrouter_free"]
        self.assertTrue(any("provider order" in error for error in roles.validate_registry(data)))
        data = copy.deepcopy(self.valid)
        data["policy"]["paid_fallback"] = True
        self.assertTrue(any("paid_fallback" in error for error in roles.validate_registry(data)))

    def test_model_roles_cannot_gain_governance_or_merge_power(self):
        data = copy.deepcopy(self.valid)
        next(role for role in data["roles"] if role["id"] == "gameplay")["forbidden_actions"].remove("merge")
        self.assertTrue(any("missing forbidden actions" in error for error in roles.validate_registry(data)))

    def test_requires_unique_parent_objectives(self):
        data = copy.deepcopy(self.valid)
        data["objectives"].append(copy.deepcopy(data["objectives"][0]))
        self.assertTrue(any("objective IDs must be unique" in error for error in roles.validate_registry(data)))

    def test_requires_objective_descriptions(self):
        data = copy.deepcopy(self.valid)
        data["objectives"][0]["description"] = ""
        self.assertTrue(any("description is required" in error for error in roles.validate_registry(data)))


if __name__ == "__main__":
    unittest.main()
