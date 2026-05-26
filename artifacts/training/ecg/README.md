# ECG 训练侧实验资产

这里暂时存放训练侧的大体积实验资产。后续如果引入 DVC，可以优先从这个目录切入。

- `raw_data/`：MIT-BIH 等原始 ECG 记录文件，例如 `.dat`、`.hea`、`.atr`。
- `processed_data/`：整理后的 CSV 样本、训练集、验证集和测试集。
- `models/`：训练生成的 PyTorch checkpoint 和 TorchScript 导出文件。
- `figures/`：训练曲线、评估图等可视化产物。

训练侧源码位于 `模型训练/ECG/`，通过 `paths.py` 统一引用本目录下的资产。

## 公开索引

当前公开仓库中，训练侧应只保留有助于理解工程闭环的轻量资产：

| 类型 | 路径 | 公开状态 | 说明 |
| --- | --- | --- | --- |
| 训练源码 | `模型训练/ECG/` | 可公开 | 包含数据处理、滤波、模型定义、训练、测试、绘图和 TorchScript 导出入口。 |
| 训练曲线 | `artifacts/training/ecg/figures/acc.png`、`loss.png` | 可公开 | 用于展示训练过程产物存在，不作为当前模型效果承诺。 |
| 契约模板 | `artifacts/training/ecg/models/contract_template.json` | 可公开 | 用于说明训练侧导出模型后应如何交付部署契约。 |
| 原始数据 | `artifacts/training/ecg/raw_data/` | 不公开 | 原始 ECG 数据需遵守数据集许可和授权边界。 |
| 完整训练 CSV | `artifacts/training/ecg/processed_data/` | 不公开 | 体积较大，且不作为公开 Demo 必需资产。 |
| checkpoint / 中间模型 | `artifacts/training/ecg/models/*.pth`、`*.pt` | 不公开 | 训练过程产物不进入公开分支；部署侧默认模型另放于 `模型部署pyqt/ECGMonitor/models/`。 |

公开分支同步时，不应把 `raw_data/`、`processed_data/`、训练 checkpoint 或训练侧中间 `.pt` 文件带入仓库。

## 当前评估记录状态

当前公开仓库可以说明训练链路和部署交付关系，但仍缺少完整模型评估记录：

- `best_acc.pt` 的来源 checkpoint 当前未记录。
- 默认模型对应的数据版本、训练配置和测试集指标当前未记录。
- 公开训练曲线不能替代独立测试集 accuracy、macro-F1、recall 或混淆矩阵。
- 部署侧真实模型 smoke test 只能证明模型可加载、链路可运行，不能代表医学准确率。

后续补评估记录时，应至少关联：

- 数据版本与划分方式。
- 训练配置和模型结构版本。
- checkpoint、TorchScript `.pt` 和契约 JSON。
- accuracy、macro-F1、各类别 recall/F1、混淆矩阵。
- 推理耗时和部署侧真实模型回放结果。

## 部署契约交付约定

训练侧导出可部署 `.pt` 模型时，必须同步提供一份模型契约信息。当前不修改 `pth_to_pt.py` 行为，也不自动生成契约；导出者需要人工依据模板补全并审查。

模板位置：

```text
artifacts/training/ecg/models/contract_template.json
```

契约字段名称必须与部署侧 `模型部署pyqt/ECGMonitor/models/model_contract.schema.md` 保持一致。至少记录：

- 输入窗口长度，例如当前部署默认 `2000`。
- 输入 shape，例如当前部署默认 `["B", 1, 2000]`。
- 归一化方式和参数来源，包括 `min_val`、`max_val`。
- 标签编号与含义，标签顺序必须与模型输出编号一致。
- 输出类别数。
- 导出 `.pt` 对应的 checkpoint 来源。
- 训练数据或数据版本说明。
- 测试集指标摘要。

未知信息必须留空或写明“当前未记录”，不能伪造成事实。smoke test 只能证明部署链路可用，不能替代测试集评估，也不能代表医学准确率。
