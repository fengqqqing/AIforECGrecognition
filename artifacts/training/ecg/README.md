# ECG 训练侧实验资产

这里暂时存放训练侧的大体积实验资产。后续如果引入 DVC，可以优先从这个目录切入。

- `raw_data/`：MIT-BIH 等原始 ECG 记录文件，例如 `.dat`、`.hea`、`.atr`。
- `processed_data/`：整理后的 CSV 样本、训练集、验证集和测试集。
- `models/`：训练生成的 PyTorch checkpoint 和 TorchScript 导出文件。
- `figures/`：训练曲线、评估图等可视化产物。

训练侧源码位于 `模型训练/ECG/`，通过 `paths.py` 统一引用本目录下的资产。

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
