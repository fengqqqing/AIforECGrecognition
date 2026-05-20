import csv
import os

from config import BASE_DIR, RUNS_DIR, SAMPLE_DATA_DIR


SOURCE_TYPE_TEST_CSV = "test_csv"
SOURCE_TYPE_LATEST_REPLAY = "latest_replay"


def parse_int_list(raw: str):
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def resolve_replay_input(
    input_path: str = "",
    use_latest: bool = False,
    runs_dir: str = RUNS_DIR,
    base_dir: str = BASE_DIR,
):
    if input_path:
        if os.path.isabs(input_path):
            return input_path
        return os.path.join(base_dir, input_path)

    if not use_latest:
        return os.path.join(SAMPLE_DATA_DIR, "test.csv")

    candidates = []
    if os.path.isdir(runs_dir):
        for root, _dirs, files in os.walk(runs_dir):
            for filename in files:
                if filename == "ecg_replay.csv":
                    full_path = os.path.join(root, filename)
                    candidates.append((os.path.getmtime(full_path), full_path))

    if not candidates:
        raise FileNotFoundError(f"在 runs 目录下未找到 ecg_replay.csv: {runs_dir}")

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def resolve_replay_path_from_policy(policy: dict):
    source_type = policy.get("source_type", SOURCE_TYPE_TEST_CSV)
    input_csv = policy.get("input_csv", "")
    use_latest = source_type == SOURCE_TYPE_LATEST_REPLAY
    return resolve_replay_input(input_csv, use_latest=use_latest)


def load_replay_source(csv_path: str, row_index: int, requested_samples: int):
    with open(csv_path, "r", encoding="utf-8") as file_obj:
        rows = list(csv.reader(file_obj))

    if row_index < 0 or row_index >= len(rows):
        raise ValueError(f"--row out of range: {row_index}, total rows: {len(rows)}")

    row = rows[row_index]
    if not row:
        raise ValueError(f"row {row_index} is empty")

    source_label = None
    signal_cells = row
    try:
        source_label = int(float(row[-1]))
        signal_cells = row[:-1]
    except ValueError:
        if len(row) > 1:
            signal_cells = row[:-1]

    all_values = [int(float(x)) for x in signal_cells]
    available = len(all_values)
    values = all_values[:requested_samples]
    return {
        "values": values,
        "available_samples": available,
        "row_index": row_index,
        "row_count": len(rows),
        "source_label": source_label,
        "requested_samples": requested_samples,
        "used_samples": len(values),
        "source_path": csv_path,
    }
