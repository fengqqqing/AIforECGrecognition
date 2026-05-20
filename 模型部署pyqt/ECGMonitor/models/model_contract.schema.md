# 模型契约 V1 格式说明

本文档定义部署侧模型契约 V1 的 JSON 格式。当前部署侧已读取契约并执行 V1 最小校验；本文档是契约文件和校验规则的依据。

契约文件应与模型文件放在同一个 `models/` 目录下。模型路径字段使用相对 `models/` 的文件名或子路径，不写入开发机绝对路径。

## 1. 文件命名

默认模型的契约文件建议命名为：

```text
best_acc.contract.json
```

默认模型文件与契约文件的对应关系：

```text
models/best_acc.pt
models/best_acc.contract.json
```

## 2. V1 JSON 示例

```json
{
  "contract_version": 1,
  "model_name": "best_acc",
  "model_file": "best_acc.pt",
  "framework": "torchscript",
  "device": "cpu",
  "input": {
    "window_size": 2000,
    "shape": ["B", 1, 2000],
    "dtype": "float32"
  },
  "preprocessing": {
    "normalization": "min_max",
    "min_val": 1582.0,
    "max_val": 2444.0
  },
  "output": {
    "num_classes": 12,
    "labels": [
      "正常",
      "RT室早",
      "ST上移",
      "ST下移",
      "窦性房颤",
      "窦性室颤",
      "单发室早",
      "窦性静止",
      "二联律",
      "房扑",
      "房早",
      "双重起搏"
    ]
  },
  "provenance": {
    "source_checkpoint": "",
    "training_data": "",
    "export_note": ""
  }
}
```

## 3. 字段定义

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `contract_version` | integer | 是 | 契约格式版本。V1 固定为 `1`。 |
| `model_name` | string | 是 | 模型逻辑名称，例如 `best_acc`。 |
| `model_file` | string | 是 | 模型文件路径，相对当前 `models/` 目录，例如 `best_acc.pt`。不得使用绝对路径，不得包含 `..`。 |
| `framework` | string | 是 | 模型框架。V1 使用 `torchscript`。 |
| `device` | string | 是 | 默认运行设备。V1 使用 `cpu`。 |
| `input` | object | 是 | 输入约束。 |
| `input.window_size` | integer | 是 | 单次推理窗口长度，必须为正整数。 |
| `input.shape` | array | 是 | 模型输入 shape。批大小使用字符串 `"B"` 表示，例如 `["B", 1, 2000]`。 |
| `input.dtype` | string | 是 | 输入张量 dtype。V1 使用 `float32`。 |
| `preprocessing` | object | 是 | 推理前预处理约束。 |
| `preprocessing.normalization` | string | 是 | 归一化方式。V1 使用 `min_max`。 |
| `preprocessing.min_val` | number | 是 | min-max 归一化最小值。 |
| `preprocessing.max_val` | number | 是 | min-max 归一化最大值，必须大于 `min_val`。 |
| `output` | object | 是 | 输出解释约束。 |
| `output.num_classes` | integer | 是 | 输出类别数，必须等于 `labels` 数组长度。 |
| `output.labels` | array[string] | 是 | 按模型输出编号排列的标签数组。顺序是模型语义的一部分。 |
| `provenance` | object | 否 | 来源说明字段。建议保留该对象，但不作为运行链路必需信息。 |
| `provenance.source_checkpoint` | string | 否 | 导出该 `.pt` 文件的 checkpoint 来源；未知时留空。 |
| `provenance.training_data` | string | 否 | 训练数据或数据版本说明；未知时留空。 |
| `provenance.export_note` | string | 否 | 导出说明、人工备注或评估摘要；未知时留空。 |

## 4. V1 必填字段

后续部署侧加载模块至少应要求以下字段存在并合法：

- `contract_version`
- `model_name`
- `model_file`
- `framework`
- `device`
- `input.window_size`
- `input.shape`
- `input.dtype`
- `preprocessing.normalization`
- `preprocessing.min_val`
- `preprocessing.max_val`
- `output.num_classes`
- `output.labels`

`provenance` 是说明性字段，允许为空或缺省。不能为了补齐契约而伪造 checkpoint、训练数据或指标信息。

当前 V1 最小校验包括：

- `contract_version == 1`。
- `framework == "torchscript"`。
- `device == "cpu"`。
- `input.window_size` 是正整数。
- `input.shape == ["B", 1, input.window_size]`。
- `input.dtype == "float32"`。
- `preprocessing.normalization == "min_max"`。
- `preprocessing.min_val < preprocessing.max_val`。
- `output.num_classes == len(output.labels)`。
- `model_file` 是位于 `models/` 内的相对路径，且模型文件存在。

## 5. 路径约定

- `model_file` 相对 `模型部署pyqt/ECGMonitor/models/` 解析。
- 默认模型应写作 `best_acc.pt`，不写作绝对路径。
- `model_file` 不允许包含 `..`，避免绕出 `models/`。
- 如未来模型放在 `models/` 的子目录中，可以使用类似 `archive/epoch_40.pt` 的相对路径。
- 契约文件自身不负责声明 `models/` 目录位置；目录位置仍由部署侧配置决定。

## 6. V1 不包含的内容

V1 契约只描述部署模型运行所需的最小语义，不包含以下内容：

- 患者信息。
- 医生复核流程。
- 数据库表结构。
- 医院系统集成信息。
- 完整临床产品化审计字段。
- 自动模型下载、升级或回滚策略。

这些内容属于未来临床产品化或模型版本治理范围，不能写入当前 V1 契约。
