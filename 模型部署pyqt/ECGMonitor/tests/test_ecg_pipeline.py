import unittest

from ecg_pipeline import EcgProcessingPipeline


class EcgProcessingPipelineTest(unittest.TestCase):
    def _pipeline(self, window_size=3, predict_func=None):
        events = {"ecg": [], "diagnosis": [], "lead": [], "heart": [], "metrics": [], "error": []}
        pipeline = EcgProcessingPipeline(
            window_size=window_size,
            predict_func=predict_func or (lambda values: 0),
            on_ecg_sample=events["ecg"].append,
            on_diagnosis=events["diagnosis"].append,
            on_lead_status=events["lead"].append,
            on_heart_rate=events["heart"].append,
            on_metrics=events["metrics"].append,
            on_error=events["error"].append,
        )
        return pipeline, events

    def test_pipeline_can_be_created_with_minimal_dependencies(self):
        events = {"ecg": [], "diagnosis": [], "lead": [], "heart": [], "metrics": [], "error": []}

        pipeline = EcgProcessingPipeline(
            window_size=3,
            predict_func=lambda values: 0,
            on_ecg_sample=events["ecg"].append,
            on_diagnosis=events["diagnosis"].append,
            on_lead_status=events["lead"].append,
            on_heart_rate=events["heart"].append,
            on_metrics=events["metrics"].append,
            on_error=events["error"].append,
        )

        self.assertEqual(pipeline.window_size, 3)
        self.assertEqual(pipeline.metrics.snapshot()["diagnosis_count"], 0)
        self.assertEqual(events, {"ecg": [], "diagnosis": [], "lead": [], "heart": [], "metrics": [], "error": []})

    def test_ecg_packet_emits_sample_without_diagnosis_before_window_full(self):
        pipeline, events = self._pipeline(window_size=3)

        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])

        self.assertEqual(events["ecg"], [2000])
        self.assertEqual(events["diagnosis"], [])
        self.assertEqual(pipeline.metrics.snapshot()["ecg_packets"], 1)

    def test_ecg_window_triggers_diagnosis_metrics_and_clears_window(self):
        predict_inputs = []

        def predict_func(values):
            predict_inputs.append(list(values))
            return 5

        pipeline, events = self._pipeline(window_size=3, predict_func=predict_func)

        for value in [2000, 2001, 2002, 2003, 2004]:
            pipeline.process_packet([0x10, 0x02, (value >> 8) & 0xFF, value & 0xFF])

        self.assertEqual(events["ecg"], [2000, 2001, 2002, 2003, 2004])
        self.assertEqual(events["diagnosis"], [5])
        self.assertEqual(predict_inputs, [[2000, 2001, 2002]])
        self.assertTrue(events["metrics"])
        self.assertEqual(events["metrics"][-1]["ecg_packets"], 3)
        self.assertEqual(events["metrics"][-1]["diagnosis_count"], 1)

    def test_ecg_success_logs_inference_summary(self):
        pipeline, events = self._pipeline(window_size=3, predict_func=lambda values: 2)

        with self.assertLogs("ecg_pipeline", level="INFO") as logs:
            for _ in range(3):
                pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])

        log_text = "\n".join(logs.output)
        self.assertIn("Inference completed", log_text)
        self.assertIn("result=2", log_text)
        self.assertEqual(events["diagnosis"], [2])

    def test_ecg_predict_error_is_reported_and_window_clears(self):
        calls = []

        def predict_func(values):
            calls.append(list(values))
            raise RuntimeError("boom")

        pipeline, events = self._pipeline(window_size=3, predict_func=predict_func)

        with self.assertLogs("ecg_pipeline", level="ERROR"):
            for _ in range(3):
                pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])
        pipeline.predict_func = lambda values: 9
        for _ in range(2):
            pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])

        self.assertEqual(calls, [[2000, 2000, 2000]])
        self.assertEqual(events["diagnosis"], [])
        self.assertEqual(len(events["error"]), 1)
        self.assertIn("AI推理失败", events["error"][0])

    def test_ecg_predict_error_is_logged(self):
        def predict_func(values):
            raise RuntimeError("boom")

        pipeline, events = self._pipeline(window_size=3, predict_func=predict_func)

        with self.assertLogs("ecg_pipeline", level="ERROR") as logs:
            for _ in range(3):
                pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])

        self.assertEqual(len(events["error"]), 1)
        self.assertIn("Inference failed in ECG pipeline", "\n".join(logs.output))

    def test_malformed_packets_report_error_without_raising(self):
        pipeline, events = self._pipeline(window_size=3)

        with self.assertLogs("ecg_pipeline", level="WARNING") as logs:
            for packet in [[], [0x10], [0x10, 0x02, 0x00], [0x10, 0x03], [0x10, 0x04, 0x00]]:
                pipeline.process_packet(packet)

        self.assertEqual(events["ecg"], [])
        self.assertEqual(events["diagnosis"], [])
        self.assertEqual(events["lead"], [])
        self.assertEqual(events["heart"], [])
        self.assertEqual(len(events["error"]), 5)
        self.assertEqual(len(logs.output), 5)

    def test_unknown_subtype_is_ignored(self):
        pipeline, events = self._pipeline(window_size=3)

        pipeline.process_packet([0x10, 0x99, 0x00, 0x00])

        self.assertEqual(events, {"ecg": [], "diagnosis": [], "lead": [], "heart": [], "metrics": [], "error": []})
        self.assertEqual(pipeline.metrics.snapshot()["total_packets"], 1)

    def test_lead_status_emits_metrics_and_clears_window_when_off(self):
        pipeline, events = self._pipeline(window_size=3, predict_func=lambda values: 8)

        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])
        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])
        pipeline.process_packet([0x10, 0x03, 0x01])
        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])

        self.assertEqual(events["lead"], [1])
        self.assertEqual(events["diagnosis"], [])
        self.assertTrue(events["metrics"])
        self.assertEqual(events["metrics"][-1]["lead_events"], 1)

    def test_lead_connected_emits_status_without_clearing_future_diagnosis(self):
        pipeline, events = self._pipeline(window_size=3, predict_func=lambda values: 4)

        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])
        pipeline.process_packet([0x10, 0x03, 0x00])
        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])
        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])

        self.assertEqual(events["lead"], [0])
        self.assertEqual(events["diagnosis"], [4])
        self.assertEqual(events["metrics"][0]["lead_events"], 1)

    def test_heart_rate_emits_only_positive_values_and_updates_metrics(self):
        pipeline, events = self._pipeline(window_size=3)

        pipeline.process_packet([0x10, 0x04, 0x00, 0x00])
        pipeline.process_packet([0x10, 0x04, 0x00, 0x48])

        self.assertEqual(events["heart"], [72])
        self.assertTrue(events["metrics"])
        self.assertEqual(events["metrics"][-1]["heart_rate_events"], 2)

    def test_heart_rate_does_not_clear_ecg_window(self):
        pipeline, events = self._pipeline(window_size=3, predict_func=lambda values: 3)

        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])
        pipeline.process_packet([0x10, 0x04, 0x00, 0x48])
        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])
        pipeline.process_packet([0x10, 0x02, 0x07, 0xD0])

        self.assertEqual(events["heart"], [72])
        self.assertEqual(events["diagnosis"], [3])


if __name__ == "__main__":
    unittest.main()
