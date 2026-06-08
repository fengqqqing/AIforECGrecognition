# ECG AI 辅助识别上位机 Demo

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/UI-PyQt5-41CD52.svg)](https://riverbankcomputing.com/software/pyqt/)
[![TorchScript](https://img.shields.io/badge/Model-TorchScript-EE4C2C.svg)](https://pytorch.org/)
[![Demo](https://img.shields.io/badge/Demo-one--click-0F766E.svg)](docs/DEMO_RUNBOOK.md)
[![Boundary](https://img.shields.io/badge/Boundary-AI%20assist%20only-64748B.svg)](docs/DATA_AND_MODEL_NOTICE.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个面向 ECG 采集与初筛场景的 AI 辅助桌面工作台 Demo：帮助一线用户先确认波形、导联和心率等基础状态，再查看正式判读前的 AI 辅助提示，并把本次运行留下可回放、可复盘的证据。

> 说明：本项目输出只作为辅助提示和实验验证，不是临床独立诊断产品。

![Demo GUI](docs/assets/screenshots/demo-gui.png)

固定样例回放场景下的 PyQt 工作台：中央显示 ECG 波形，右侧展示 AI 辅助识别、心率和导联状态，底部展示运行指标。

## 一键体验

```powershell
python -m pip install -r requirements.txt
.\run_demo.ps1
```

脚本会自动启动固定 Demo：`python 模型部署pyqt\ECGMonitor\main.py --demo`。启动后无需手动选择样例数据，可按“波形 -> 心率 / 导联 -> AI 辅助识别 -> 指标 -> 最近摘要 / 导出”的顺序走完整体验闭环。

## 产品体验闭环

这个 Demo 的产品假设不是“让 AI 替代医生诊断”，而是在 ECG 采集到医生正式判读之间，为采集与初筛人员提供一个轻量工作台：先确认信号质量，再查看 AI 辅助提示，最后把运行过程留下来供复核和复盘。

- **核心用户**：心电图室技师、基层 / 床旁采集人员、需要先看 ECG 但不是心电专科医生的一线人员。
- **核心痛点**：现场人员不承担最终诊断责任，但需要判断波形是否有效、导联是否正常、是否有值得优先转交医生复核的辅助提示。
- **解决方案**：把 ECG 波形、导联状态、心率、AI 辅助识别、运行指标和导出复盘放在同一个桌面工作台里。
- **体验路径**：启动固定 Demo -> 查看波形 -> 确认心率和导联 -> 等待 AI 辅助识别 -> 查看运行指标 -> 打开最近摘要 -> 复盘导出文件。
- **边界取舍**：当前验证产品流程和部署链路，不验证临床准确率，也不提供患者管理、医生复核流程或医院系统集成。
- **未来方向**：可在现有回放和导出基础上扩展信号质量提示、结构化交接卡、复盘时间线和 ECG 回放训练模式，但这些不是当前已实现能力。

进一步阅读：

- [产品案例主线](docs/PRODUCT_CASE.md)：问题定义、核心用户、痛点机会和功能取舍。
- [Demo 讲解脚本](docs/DEMO_SCRIPT.md)：1 分钟 / 3 分钟讲述版本和展示问答提示。
- [截图体验走查](docs/SCREENSHOT_WALKTHROUGH.md)：截图区域标注方案和界面设计解释。
- [产品体验闭环专项说明](docs/PRODUCT_EXPERIENCE.md)：用户旅程、状态模型和展示口径。

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

## 环境与手动启动

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

Demo 建议按一次 ECG 采集与初筛流程讲述，而不是只介绍控件：

1. 顶部状态进入固定 Demo / 离线回放流程。
2. 中央 ECG 波形刷新，用来确认当前信号是否可观察。
3. 右侧心率和三导联单通道导联状态更新，用来判断基础状态是否可信。
4. ECG 窗口达到 2000 点后，AI 结果卡显示辅助识别标签和保守提示文案。
5. 底部指标展示包计数、诊断次数、推理耗时、吞吐量和事件计数。
6. 回放完成后，通过最近摘要和导出目录复盘本次运行。

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
| 产品体验闭环 | 围绕 ECG 采集与初筛人员设计，从信号确认、状态观察、AI 辅助提示到摘要和导出复盘。 | [产品体验说明](docs/PRODUCT_EXPERIENCE.md) |
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
| 产品案例主线、问题定义和功能取舍 | [产品案例](docs/PRODUCT_CASE.md) |
| 项目展示或评审时如何讲 Demo | [Demo 讲解脚本](docs/DEMO_SCRIPT.md) |
| 截图区域和界面设计意图 | [截图体验走查](docs/SCREENSHOT_WALKTHROUGH.md) |
| 产品体验闭环和用户旅程 | [产品体验闭环专项说明](docs/PRODUCT_EXPERIENCE.md) |
| 训练侧到部署侧架构 | [架构总览](docs/ARCHITECTURE_OVERVIEW.md)、[技术设计](docs/TECH_DESIGN.md) |
| 模型输入输出契约 | [模型契约](docs/MODEL_CONTRACT.md) |
| 数据、模型和评估边界 | [数据与模型说明](docs/DATA_AND_MODEL_NOTICE.md)、[模型评估状态](docs/MODEL_EVALUATION_STATUS.md) |
| 关键产品决策 | [产品决策记录](docs/PRODUCT_DECISIONS.md) |
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
