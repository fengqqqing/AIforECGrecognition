# ECG AI 辅助识别上位机 Demo

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/UI-PyQt5-41CD52.svg)](https://riverbankcomputing.com/software/pyqt/)
[![TorchScript](https://img.shields.io/badge/Model-TorchScript-EE4C2C.svg)](https://pytorch.org/)
[![Demo](https://img.shields.io/badge/Demo-one--click-0F766E.svg)](docs/DEMO_RUNBOOK.md)
[![Boundary](https://img.shields.io/badge/Boundary-AI%20assist%20only-64748B.svg)](docs/DATA_AND_MODEL_NOTICE.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个覆盖训练侧与部署侧的 ECG AI 辅助识别桌面 Demo：训练侧负责 ECG 数据处理、CNN 模型训练/评估和 TorchScript 导出，部署侧负责固定样例回放、波形展示、模型辅助识别、运行指标和可追溯导出。

> 说明：本项目输出只作为辅助提示和实验验证，不是临床独立诊断产品。

![Demo GUI](docs/assets/screenshots/demo-gui.png)

固定样例回放场景下的 PyQt 工作台：中央显示 ECG 波形，右侧展示 AI 辅助识别、心率和导联状态，底部展示运行指标。

## 项目主线

```text
ECG 数据处理与模型训练
-> TorchScript 模型导出
-> best_acc.contract.json 模型契约
-> EcgProcessingPipeline 统一处理
-> PyQt 桌面 Demo 展示
-> 指标、诊断事件和可回放数据导出
```

访问者可以先运行一键 Demo 看到桌面端效果，再通过架构和模型说明了解训练侧如何交付给部署侧。

## 快速开始

推荐环境：

- Windows 10/11
- Python 3.10+
- PowerShell

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

一键启动固定 Demo：

```powershell
.\run_demo.ps1
```

或双击：

```text
run_demo.bat
```

脚本会从仓库根目录自动定位 `*pyqt\ECGMonitor\main.py`，并启动：

```powershell
python 模型部署pyqt\ECGMonitor\main.py --demo
```

启动后会自动进入固定离线回放场景，无需手动选择样例数据。

## Demo 展示内容

- 中央 ECG 波形主视图区。
- 右侧 AI 辅助识别、心率、三导联单通道导联状态。
- 底部运行指标：包计数、诊断次数、单次推理耗时、吞吐量和事件计数。
- 顶部操作入口：离线回放、回放设置、最近摘要、导出目录、重置显示。

## 训练到部署闭环

训练侧位于 `模型训练/ECG/`，当前公开说明覆盖以下能力：

- 数据处理：通过数据处理、滤波和划分脚本生成训练、验证和测试输入。
- 模型定义：`model.py` 定义当前 CNN 分类模型结构。
- 训练与评估入口：`train.py`、`test.py` 和 `draw.py` 支撑训练、测试和曲线产物生成。
- 模型导出：`pth_to_pt.py` 将训练侧权重导出为部署可加载的 TorchScript `.pt`。
- 契约交付：部署侧通过 `best_acc.contract.json` 读取输入窗口、归一化参数和 12 分类标签顺序。

当前公开 Demo 的真实模型 smoke test 只验证部署链路可用；模型准确率、类别级 recall/F1、混淆矩阵等评估结论需要后续以独立评估文档记录，不能由 smoke test 推断。

## 验证 Demo

维护者可从仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo_checks.ps1
```

该命令会依次检查：

- 部署侧单元测试
- 固定 demo policy
- 固定场景 mock 回放
- 固定场景真实模型回放

真实模型 smoke 的最低成功标准是输出 `Diagnosis count: 1`。这只证明部署推理链路可用，不代表医学准确率达标。

## 打包 Demo

如需重新构建 exe，先安装 PyInstaller：

```powershell
python -m pip install pyinstaller
```

然后执行：

```powershell
cd 模型部署pyqt\ECGMonitor
python -m PyInstaller main.spec
```

## 核心亮点

| 亮点 | 说明 | 对应位置 |
| --- | --- | --- |
| 训练到部署闭环 | 训练侧覆盖数据处理、CNN 训练/评估入口和 TorchScript 导出，部署侧通过模型契约接收模型语义。 | [架构总览](docs/ARCHITECTURE_OVERVIEW.md) |
| 模型契约化 | `best_acc.contract.json` 管理输入窗口、归一化参数和 12 分类标签顺序，避免 UI 和推理侧各自解释模型。 | [模型契约](docs/MODEL_CONTRACT.md) |
| 管线复用 | CLI 回放、GUI 回放和串口 worker 共用 `EcgProcessingPipeline`，减少输入路径行为分叉。 | `模型部署pyqt/ECGMonitor/ecg_pipeline.py` |
| 一键 Demo | `run_demo.ps1` / `run_demo.bat` 固定工作目录并启动 `python main.py --demo`。 | [Demo 运行手册](docs/DEMO_RUNBOOK.md) |
| 可追溯导出 | 每次运行导出 `metrics.jsonl`、`diagnosis.csv`、`ecg_replay.csv`，便于复盘 Demo 过程。 | `模型部署pyqt/ECGMonitor/run_exporter.py` |
| 真实模型 smoke | `run_demo_checks.ps1` 同时覆盖 mock 回放和真实 TorchScript 回放，保护部署链路。 | `run_demo_checks.ps1` |
| 中文路径兼容 | 模型加载走二进制内存流，一键脚本避免硬编码中文目录字面量。 | `模型部署pyqt/ECGMonitor/example.py` |
| 公开发布边界 | 公开分支保留可运行 Demo 必需资产，排除原始数据、完整训练 CSV、checkpoint 和运行输出。 | [公开仓库发布边界](docs/PUBLICATION_BOUNDARY.md) |

## 常用入口

启动普通 GUI：

```powershell
cd 模型部署pyqt\ECGMonitor
python main.py
```

固定场景真实模型回放：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --row 3 --samples 2000 --event-interval 500 --lead-events 0,0,0,0 --hr-events 72,84,78,90 --real-model
```

固定场景 mock 回放：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --row 3 --samples 2000 --event-interval 500 --lead-events 0,0,0,0 --hr-events 72,84,78,90 --mock-label 0
```

## 项目结构

```text
模型训练/ECG/
  训练数据处理、模型定义、训练、评估和模型导出

模型部署pyqt/ECGMonitor/
  PyQt 上位机、串口采集、推理、离线回放、导出和测试

docs/
  PRD、技术设计、Demo runbook、模型契约、架构说明和截图资产
```

## 阅读路径

| 想了解 | 推荐入口 |
| --- | --- |
| 运行 Demo | [Demo 运行手册](docs/DEMO_RUNBOOK.md) |
| 训练侧到部署侧架构 | [架构总览](docs/ARCHITECTURE_OVERVIEW.md)、[技术设计](docs/TECH_DESIGN.md) |
| 模型输入输出契约 | [模型契约](docs/MODEL_CONTRACT.md) |
| 数据、模型和评估边界 | [数据与模型说明](docs/DATA_AND_MODEL_NOTICE.md)、[模型评估状态](docs/MODEL_EVALUATION_STATUS.md) |
| 产品范围和非目标 | [产品需求](docs/PRD.md) |
| 公开分支同步规则 | [公开仓库发布边界](docs/PUBLICATION_BOUNDARY.md) |
| 协作开发约束 | [Agent 开发指南](docs/AGENT.md) |

## 公开仓库边界

公开仓库保留一键 Demo 所需代码、文档、小体积样例数据和默认部署模型。完整原始数据、完整训练 CSV、训练 checkpoint、历史模型归档和运行输出不纳入公开发布分支。

发布边界详见 [公开仓库发布边界](docs/PUBLICATION_BOUNDARY.md)，数据与模型边界详见 [数据与模型说明](docs/DATA_AND_MODEL_NOTICE.md)。

## 设计边界

1. 本项目定位为 ECG 辅助识别实验系统，重点验证部署闭环，不作为临床独立诊断产品。
2. 一键 Demo 使用固定样例回放，展示波形、心率、导联、辅助识别和运行指标同步更新。
3. 部署侧通过模型契约读取窗口长度、归一化参数和标签顺序，避免模型语义漂移。
4. CLI 回放、GUI 回放和串口输入最终进入同一条 ECG 处理管线，减少行为分叉。
5. 运行后导出 metrics、diagnosis 和 replay 文件，方便复盘本次演示结果。
6. 模型效果、真实临床数据、医生复核、权限审计和医院系统接入仍属于后续方向。
