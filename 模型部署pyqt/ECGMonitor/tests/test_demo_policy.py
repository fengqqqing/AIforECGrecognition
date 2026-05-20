import os
import unittest

from config import DEMO_REPLAY_POLICY, OFFLINE_REPLAY_POLICY, SAMPLE_DATA_DIR
from model_contract import load_model_contract
from replay_utils import SOURCE_TYPE_TEST_CSV, load_replay_source, resolve_replay_path_from_policy


class DemoReplayPolicyTest(unittest.TestCase):
    def test_demo_policy_points_to_valid_sample_row(self):
        self.assertIsNot(DEMO_REPLAY_POLICY, OFFLINE_REPLAY_POLICY)
        self.assertEqual(DEMO_REPLAY_POLICY["source_type"], SOURCE_TYPE_TEST_CSV)
        self.assertEqual(DEMO_REPLAY_POLICY["input_csv"], os.path.join(SAMPLE_DATA_DIR, "test.csv"))

        resolved_path = resolve_replay_path_from_policy(DEMO_REPLAY_POLICY)
        self.assertTrue(os.path.exists(resolved_path))

        source = load_replay_source(
            resolved_path,
            DEMO_REPLAY_POLICY["row"],
            DEMO_REPLAY_POLICY["samples"],
        )

        self.assertEqual(source["row_index"], DEMO_REPLAY_POLICY["row"])
        self.assertEqual(source["used_samples"], DEMO_REPLAY_POLICY["samples"])
        self.assertGreaterEqual(source["available_samples"], DEMO_REPLAY_POLICY["samples"])
        self.assertEqual(source["source_label"], DEMO_REPLAY_POLICY["expected_source_label"])

    def test_demo_policy_uses_one_full_contract_window(self):
        contract = load_model_contract(DEMO_REPLAY_POLICY["model_contract_path"])
        window_size = contract["input"]["window_size"]

        self.assertEqual(DEMO_REPLAY_POLICY["samples"], window_size)
        self.assertEqual(DEMO_REPLAY_POLICY["event_interval"], 500)
        self.assertEqual(
            len(DEMO_REPLAY_POLICY["lead_events"]),
            DEMO_REPLAY_POLICY["samples"] // DEMO_REPLAY_POLICY["event_interval"],
        )
        self.assertEqual(len(DEMO_REPLAY_POLICY["hr_events"]), len(DEMO_REPLAY_POLICY["lead_events"]))

    def test_demo_policy_keeps_lead_connected_until_first_diagnosis(self):
        self.assertTrue(DEMO_REPLAY_POLICY["lead_events"])
        self.assertTrue(all(status == 0 for status in DEMO_REPLAY_POLICY["lead_events"]))

    def test_demo_policy_prefers_real_model_and_documents_manual_mock_replay(self):
        self.assertTrue(DEMO_REPLAY_POLICY["use_real_model"])
        self.assertEqual(DEMO_REPLAY_POLICY["expected_real_diagnosis"], 0)
        self.assertNotIn("mock_fallback", DEMO_REPLAY_POLICY)

        manual_mock = DEMO_REPLAY_POLICY["manual_mock_replay"]
        self.assertEqual(manual_mock["mock_label"], DEMO_REPLAY_POLICY["expected_real_diagnosis"])
        self.assertEqual(manual_mock["row"], DEMO_REPLAY_POLICY["row"])
        self.assertEqual(manual_mock["samples"], DEMO_REPLAY_POLICY["samples"])

        display_strategy = DEMO_REPLAY_POLICY["display_strategy"]
        self.assertEqual(display_strategy["primary_mode"], "real-model")
        self.assertNotIn("fallback_mode", display_strategy)
        self.assertIn("辅助识别", display_strategy["result_wording"])


if __name__ == "__main__":
    unittest.main()
