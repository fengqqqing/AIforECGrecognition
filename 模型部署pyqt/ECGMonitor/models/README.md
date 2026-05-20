# 模型文件说明

- `best_acc.pt`：部署侧默认加载的 TorchScript 模型。
- `best_acc.contract.json`：`best_acc.pt` 对应的模型契约文件，记录输入窗口、归一化参数、输出类别数和标签顺序等部署语义。
- `model_contract.schema.md`：模型契约 V1 格式说明。
- `archive/`：历史模型或实验对照模型，不作为默认运行入口。

当前部署代码通过 `config.py` 中的 `MODEL_CONTRACT_PATH` 读取默认契约，再由契约中的 `model_file` 定位模型文件。契约中的输入窗口、归一化参数和标签顺序会分别用于推理和 UI 展示。

## 替换默认模型流程

替换 `best_acc.pt` 时，必须同步替换或更新 `best_acc.contract.json`，并重点确认：

- `model_file` 指向实际模型文件。
- `input.window_size` 与模型输入窗口一致，当前默认是 `2000`。
- `input.shape` 与模型输入一致，当前默认是 `["B", 1, 2000]`。
- `preprocessing.min_val` 和 `preprocessing.max_val` 与训练/导出时一致。
- `output.num_classes` 与模型输出类别数一致。
- `output.labels` 的顺序与模型输出编号完全一致。

替换后至少运行：

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --real-model
```

真实模型回放 smoke test 只表示模型文件、契约、推理链路和离线回放链路可用，不代表模型医学准确率达标。
