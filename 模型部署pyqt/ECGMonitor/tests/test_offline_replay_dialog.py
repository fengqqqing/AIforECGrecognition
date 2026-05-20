import unittest
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets
from offline_replay_dialog import OfflineReplayDialog
from replay_utils import SOURCE_TYPE_LATEST_REPLAY, SOURCE_TYPE_TEST_CSV


class OfflineReplayDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_dialog_policy_roundtrip(self):
        dialog = OfflineReplayDialog(
            {
                "source_type": SOURCE_TYPE_LATEST_REPLAY,
                "input_csv": "test.csv",
                "use_real_model": True,
                "row": 2,
                "samples": 3000,
                "event_interval": 600,
                "lead_events": [0, 1],
                "hr_events": [72, 88],
                "mock_label": 4,
                "frame_sleep_ms": 2,
            }
        )

        policy = dialog.get_policy()
        self.assertEqual(policy["source_type"], SOURCE_TYPE_LATEST_REPLAY)
        self.assertTrue(policy["use_real_model"])
        self.assertEqual(policy["row"], 2)
        self.assertEqual(policy["samples"], 3000)
        self.assertEqual(policy["lead_events"], [0, 1])
        self.assertEqual(policy["hr_events"], [72, 88])

    def test_source_mode_enables_input_for_test_csv(self):
        dialog = OfflineReplayDialog({"source_type": SOURCE_TYPE_TEST_CSV})
        dialog.sourceTypeCombo.setCurrentIndex(0)
        dialog._sync_source_mode()
        self.assertTrue(dialog.inputEdit.isEnabled())

        dialog.sourceTypeCombo.setCurrentIndex(1)
        dialog._sync_source_mode()
        self.assertFalse(dialog.inputEdit.isEnabled())


if __name__ == "__main__":
    unittest.main()
