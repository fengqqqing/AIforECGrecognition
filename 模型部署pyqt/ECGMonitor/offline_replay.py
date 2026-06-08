# 离线回放 CLI 入口模块
# 职责：从命令行运行离线回放，读取 CSV 中的 ECG 数据，
#       通过 EcgProcessingPipeline 执行 mock 或真实模型推理，输出回放结果。
# 用法：python offline_replay.py [--input CSV] [--latest] [--row N] [--samples N]
#       [--real-model] [--mock-label N] [--lead-events 0,1,0] [--hr-events 72,88,65]
# 注意：与 GUI 回放共用 replay_utils 中的回放源解析逻辑。

import argparse
import time

from config import MODEL_CONTRACT_PATH
from ecg_pipeline import EcgProcessingPipeline
from example import predict
from model_contract import load_model_contract
from replay_utils import load_replay_source, parse_int_list, resolve_replay_input


def make_ecg_packet(value):
    """构造 ECG 数据包：包头 0x10，子类型 0x02，高 8 位 + 低 8 位合成采样值。"""
    value = int(value)
    return [0x10, 0x02, (value >> 8) & 0xFF, value & 0xFF]


def make_lead_packet(status):
    """构造导联状态包：包头 0x10，子类型 0x03。"""
    return [0x10, 0x03, int(status) & 0xFF]


def make_hr_packet(hr):
    """构造心率数据包：包头 0x10，子类型 0x04，高 8 位 + 低 8 位合成心率值。"""
    hr = int(hr)
    return [0x10, 0x04, (hr >> 8) & 0xFF, hr & 0xFF]


def main():
    parser = argparse.ArgumentParser(description="Offline ECG replay for worker/inference validation")
    parser.add_argument("--input", default="", help="CSV path containing ECG rows")
    parser.add_argument("--latest", action="store_true", help="Replay the latest exported ecg_replay.csv from runs/")
    parser.add_argument("--row", type=int, default=0, help="Which row to replay")
    parser.add_argument("--samples", type=int, default=4000, help="Number of ECG points to replay")
    parser.add_argument("--lead-events", default="", help="Comma-separated lead status events, e.g. 0,1,0")
    parser.add_argument("--hr-events", default="", help="Comma-separated HR events, e.g. 72,88,65")
    parser.add_argument("--event-interval", type=int, default=500, help="Inject lead/hr events every N ECG samples")
    parser.add_argument("--real-model", action="store_true", help="Use real model inference instead of mock")
    parser.add_argument("--mock-label", type=int, default=0, help="Mock diagnosis label when not using real model")
    args = parser.parse_args()

    csv_path = resolve_replay_input(args.input, use_latest=args.latest)

    source = load_replay_source(csv_path, args.row, args.samples)
    values = source["values"]
    if args.samples > source["available_samples"]:
        print(
            f"[WARN] requested --samples={args.samples}, "
            f"but only {source['available_samples']} ECG points are available in row {args.row}."
        )

    lead_events = parse_int_list(args.lead_events)
    hr_events = parse_int_list(args.hr_events)

    diagnosis = []
    heart_rates = []
    lead_status = []
    ecg_count = 0

    if args.real_model:
        predict_func = lambda values: predict(values)
    else:
        predict_func = lambda values: args.mock_label

    pipeline = EcgProcessingPipeline(
        window_size=load_model_contract(MODEL_CONTRACT_PATH)["input"]["window_size"],
        predict_func=predict_func,
        on_diagnosis=diagnosis.append,
        on_heart_rate=heart_rates.append,
        on_lead_status=lead_status.append,
    )

    start = time.perf_counter()
    lead_idx = 0
    hr_idx = 0
    for value in values:
        pipeline.process_packet(make_ecg_packet(value))
        ecg_count += 1

        if args.event_interval > 0 and ecg_count % args.event_interval == 0:
            if lead_idx < len(lead_events):
                pipeline.process_packet(make_lead_packet(lead_events[lead_idx]))
                lead_idx += 1
            if hr_idx < len(hr_events):
                pipeline.process_packet(make_hr_packet(hr_events[hr_idx]))
                hr_idx += 1

    elapsed = time.perf_counter() - start

    print("Replay finished")
    print(f"  Source file: {source['source_path']}")
    print(f"  Source row: {source['row_index'] + 1}/{source['row_count']}")
    print(f"  Available samples: {source['available_samples']}")
    print(f"  Used samples: {source['used_samples']}")
    print(f"  Source label: {source['source_label'] if source['source_label'] is not None else 'none'}")
    print(f"  Inference mode: {'real-model' if args.real_model else f'mock({args.mock_label})'}")
    print(f"  Diagnosis count: {len(diagnosis)}")
    if diagnosis:
        print(f"  Latest diagnosis: {diagnosis[-1]}")
    print(f"  Injected lead events: {lead_events if lead_events else 'none'}")
    print(f"  Injected HR events: {hr_events if hr_events else 'none'}")
    print(f"  Lead events: {len(lead_status)}")
    print(f"  HR events: {len(heart_rates)}")
    print(f"  Elapsed: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
