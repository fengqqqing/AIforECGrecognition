# Demo 预检模块
# 职责：在启动 Demo 模式前验证所有必要资源是否就绪：
#   - 模型契约文件是否存在且有效
#   - 模型文件是否存在
#   - 样例数据文件是否存在且可读
#   - 回放参数（samples、event_interval 等）是否合法
# 预检失败时抛出 DemoReadinessError，包含所有问题列表。

import os

from config import DEMO_REPLAY_POLICY, MODEL_CONTRACT_PATH
from model_contract import load_model_contract
from replay_utils import load_replay_source, resolve_replay_path_from_policy


class DemoReadinessError(RuntimeError):
    """Demo 预检失败异常，problems 列表包含所有检查失败的原因。"""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("Demo 预检失败:\n- " + "\n- ".join(self.problems))


def check_demo_readiness(policy=None):
    demo_policy = dict(DEMO_REPLAY_POLICY if policy is None else policy)
    problems = []

    contract_path = demo_policy.get("model_contract_path") or MODEL_CONTRACT_PATH
    contract = None
    if not os.path.exists(contract_path):
        problems.append(f"模型契约不存在: {contract_path}")
    else:
        try:
            contract = load_model_contract(contract_path)
        except FileNotFoundError as exc:
            problems.append(f"模型文件不存在: {exc}")
        except Exception as exc:
            problems.append(f"模型契约无效: {exc}")

    source_path = None
    source = None
    try:
        source_path = resolve_replay_path_from_policy(demo_policy)
    except Exception as exc:
        problems.append(f"样例数据路径无效: {exc}")

    if source_path is not None:
        if not os.path.exists(source_path):
            problems.append(f"样例数据不存在: {source_path}")
        else:
            try:
                source = load_replay_source(source_path, demo_policy["row"], demo_policy["samples"])
            except ValueError as exc:
                problems.append(f"demo row 无效: {exc}")
            except Exception as exc:
                problems.append(f"样例数据读取失败: {exc}")

    if contract is not None:
        window_size = contract["input"]["window_size"]
        samples = demo_policy.get("samples")
        if not isinstance(samples, int) or samples <= 0:
            problems.append("demo samples 必须是正整数")
        elif samples < window_size:
            problems.append(f"样例数据不足以满足模型窗口: samples={samples}, window_size={window_size}")

    if source is not None and source["used_samples"] < demo_policy.get("samples", 0):
        problems.append(
            "样例数据不足: "
            f"requested={demo_policy.get('samples')}, available={source['available_samples']}"
        )

    event_interval = demo_policy.get("event_interval")
    if not isinstance(event_interval, int) or event_interval <= 0:
        problems.append("demo event_interval 必须是正整数")

    lead_events = demo_policy.get("lead_events")
    hr_events = demo_policy.get("hr_events")
    if not isinstance(lead_events, list):
        problems.append("demo lead_events 必须是数组")
    if not isinstance(hr_events, list):
        problems.append("demo hr_events 必须是数组")

    if problems:
        raise DemoReadinessError(problems)

    return {
        "contract_path": contract_path,
        "contract": contract,
        "source_path": source_path,
        "source": source,
        "window_size": contract["input"]["window_size"],
    }
