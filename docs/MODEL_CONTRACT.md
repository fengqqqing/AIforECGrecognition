# 模型契约说明

本文档记录当前部署侧模型契约事实、接入状态和人工审查重点。默认模型已经具备显式契约文件，部署侧会读取并校验这份契约。

## 1. 当前事实

### 1.1 模型文件

| 字段 | 当前事实 | 来源 |
| --- | --- | --- |
| 默认模型目录 | `模型部署pyqt/ECGMonitor/models/` | `config.py` 的 `MODELS_DIR` |
| 默认模型文件 | `best_acc.pt` | `best_acc.contract.json` 的 `model_file` |
| 部署侧相对路径 | `models/best_acc.pt` | `config.py` 与 `models/README.md` |
| 模型格式 | TorchScript `.pt` | `example.py` 使用 `torch.jit.load()` |
| 加载方式 | 先读取模型二进制，再通过 `io.BytesIO` 传给 `torch.jit.load()` | `example.py` |
| 运行设备 | CPU | `example.py` 使用 `map_location="cpu"` |

当前与 `best_acc.pt` 配套的契约文件是 `models/best_acc.contract.json`。模型文件、窗口长度、归一化参数和标签顺序通过该契约关联。

### 1.2 输入约束

| 字段 | 当前事实 | 来源 |
| --- | --- | --- |
| 输入窗口长度 | `input.window_size = 2000` | `best_acc.contract.json` |
| 最小输入长度 | 输入样本少于 2000 点时报错 | `example.predict()` |
| 超长输入处理 | 输入样本多于 2000 点时取最后 2000 点 | `example.predict()` |
| 输入 dtype | `float32` | `np.asarray(data, dtype=np.float32)` |
| 模型输入 shape | `(B, 1, 2000)`，当前单次推理为 `(1, 1, 2000)` | `best_acc.contract.json` 与 `example.predict()` |

### 1.3 归一化约束

| 字段 | 当前事实 | 来源 |
| --- | --- | --- |
| 归一化方式 | min-max 归一化 | `example.predict()` |
| 最小值 | `min_val = 1582.0` | `best_acc.contract.json` |
| 最大值 | `max_val = 2444.0` | `best_acc.contract.json` |
| 计算公式 | `(signal - min_val) / (max_val - min_val)` | `example.predict()` |

当前部署侧没有记录这些归一化参数来自哪一次训练、哪一个数据集或哪一个导出流程。

### 1.4 输出与标签

当前部署侧将模型输出解释为 12 分类结果。类别数量来自 `best_acc.contract.json` 的 `output.num_classes`，UI 通过模型输出的整数编号索引契约中的 `output.labels`。

| 编号 | 标签 |
| --- | --- |
| 0 | 正常 |
| 1 | RT室早 |
| 2 | ST上移 |
| 3 | ST下移 |
| 4 | 窦性房颤 |
| 5 | 窦性室颤 |
| 6 | 单发室早 |
| 7 | 窦性静止 |
| 8 | 二联律 |
| 9 | 房扑 |
| 10 | 房早 |
| 11 | 双重起搏 |

相关事实：

- 输出类别数：12。
- 标签顺序当前定义在 `best_acc.contract.json` 的 `output.labels`。
- `ui_rules.get_diagnosis_label(result)` 使用诊断编号索引契约标签。
- 越界编号当前返回空字符串。
- 启动 warmup 阶段会用 dummy input 检查 TorchScript 模型真实输出维度是否等于 `output.num_classes`。

## 2. 当前风险

- 替换 `models/best_acc.pt` 时，如果没有同步更新 `best_acc.contract.json`，仍可能造成模型语义与部署解释不一致。
- 契约可以校验字段完整性、窗口、归一化范围、标签数量和模型输出维度，但不能证明医学准确率。
- 当前默认契约没有记录 `best_acc.pt` 的来源 checkpoint、训练数据版本或测试集指标摘要。
- 训练侧后续导出新模型时，必须补齐契约来源信息；未知信息不能伪造成事实。

## 3. 已实现接入

当前已完成：

- 使用 `模型部署pyqt/ECGMonitor/models/model_contract.schema.md` 定义 V1 JSON 字段格式。
- 为默认模型创建 `models/best_acc.contract.json`。
- 在契约中记录模型文件名、框架、运行设备、输入窗口、输入 shape、输入 dtype、归一化方式、归一化参数、输出类别数和完整标签顺序。
- 使用相对 `models/` 的路径记录模型文件，避免写入开发机绝对路径。
- 通过 `model_contract.py` 校验契约文件存在、JSON 格式正确、必填字段存在、窗口长度合法、`min_val < max_val`、`num_classes == len(labels)`、模型文件存在。
- `example.predict()` 从契约读取 `model_file`、`window_size`、`min_val`、`max_val`。
- `ui_rules.get_diagnosis_label()` 从契约读取标签。
- `warmup_model()` 在启动前检查契约和模型输出类别数。
- `config.py` 不再保留模型路径、窗口长度、归一化参数和标签列表这些重复语义来源。

## 4. 人工审查重点

替换或创建契约文件前，必须人工确认：

- `model_file` 是否仍指向 `best_acc.pt`。
- `window_size` 是否为 `2000`。
- 输入 shape 是否为 `(B, 1, 2000)`。
- `min_val` 是否为 `1582.0`。
- `max_val` 是否为 `2444.0`。
- `num_classes` 是否为 `12`。
- 标签数组顺序是否与本文档和 `best_acc.contract.json` 中的 `output.labels` 完全一致。
