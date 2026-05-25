# 项目结构说明

本项目分为训练侧和部署侧两个主要域：

```text
模型训练/ECG/
  训练数据处理、模型定义、训练、评估和模型导出。

模型部署pyqt/ECGMonitor/
  PyQt 上位机、串口采集、推理、离线回放、导出和测试。
```

## 根目录

- `README.md`：项目对外展示入口，包含一键运行、Demo 效果、核心亮点和设计边界。
- `docs/`：技术设计、项目结构说明和文档图片。
- `artifacts/`：实验资产目录，当前存放训练侧数据、模型 checkpoint 和训练图表；未来可迁移到 DVC。
- `.vscode/`：VS Code 工作区配置。
- `模型部署（优化后）.code-workspace`：VS Code 工作区入口。

## 训练侧目录

- `模型训练/ECG/model.py`：CNN 模型结构定义。
- `模型训练/ECG/train.py`：训练入口。
- `模型训练/ECG/test.py`：评估入口。
- `模型训练/ECG/dataset.py`：从原始 ECG 记录读取和构造样本。
- `模型训练/ECG/dataset_.py`：从整理后的 CSV 加载训练/测试样本。
- `模型训练/ECG/generate_data.py`：生成增强后的 CSV 样本。
- `模型训练/ECG/spilt.py`：历史数据集划分脚本，文件名保留现状。
- `模型训练/ECG/pth_to_pt.py`：将 checkpoint 导出为 TorchScript。
- `模型训练/ECG/paths.py`：训练侧统一路径配置。

## 训练侧资产目录

- `artifacts/training/ecg/raw_data/`：原始 ECG 记录文件。
- `artifacts/training/ecg/processed_data/`：整理后的 CSV 数据集。
- `artifacts/training/ecg/models/`：训练 checkpoint 和 TorchScript 导出文件。
- `artifacts/training/ecg/figures/`：训练曲线和评估图。

## 部署侧目录

- `models/`：部署运行需要的 TorchScript 模型。
- `models/archive/`：保留的历史模型或对照模型。
- `image/`：界面图片资源。
- `sample_data/`：离线回放和测试使用的样例 CSV。
- `examples/`：不参与主程序运行的演示脚本。
- `tests/`：单元测试和 UI smoke check。
- `runs/`：运行时导出的指标、诊断和回放文件，默认不纳入版本管理。

### 部署侧关键模块

- `main.py`：上位机启动入口。
- `ParamMonitor.py`：主窗口协调层，负责 UI 事件、串口 worker 生命周期和离线回放入口。
- `serial_worker.py`：串口 worker，负责串口打开、读取、字节解包和 Qt 信号转发。
- `ecg_pipeline.py`：正式 ECG 处理管线，负责 ECG 窗口累计、推理触发、导联/心率事件处理和 metrics 更新。
- `offline_replay_worker.py`：GUI 离线回放 worker，负责读取回放数据和节奏控制，处理逻辑走 `ecg_pipeline.py`。
- `offline_replay.py`：CLI 离线回放入口，处理逻辑走 `ecg_pipeline.py`。
- `replay_utils.py`：CLI 与 GUI 共享的回放源解析逻辑。

## 约定

- 主程序入口仍是 `模型部署pyqt/ECGMonitor/main.py`。
- 默认部署模型由 `config.py` 中的 `MODEL_CONTRACT_PATH` 指向契约文件，再由契约中的 `model_file` 定位模型文件。
- 默认离线回放样例由 `config.py` 中的 `OFFLINE_REPLAY_POLICY["input_csv"]` 指向。
- PyQt 生成文件 `*_ui.py` 和 `img_rc.py` 可以保留，但业务逻辑不要写入这些生成文件。
