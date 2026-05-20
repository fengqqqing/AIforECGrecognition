# Agent 开发指南

## 1. 项目概述

本项目是 ECG 自动识别系统，当前重点是算法训练、模型部署和 PyQt 上位机实时推理闭环。系统通过串口或离线回放接收 ECG 数据，累计固定窗口后调用 TorchScript 模型推理，并在桌面 GUI 中展示波形、心率、导联状态、诊断结果和运行指标。

当前产品定位是医生辅助识别工具，模型输出只作为辅助提示和实验验证依据，不能被描述为最终临床诊断。

项目分为两个主要域：

- `模型训练/ECG/`：训练数据处理、模型定义、训练、评估和模型导出。
- `模型部署pyqt/ECGMonitor/`：PyQt 上位机、串口采集、推理、离线回放、导出和测试。

配套文档：

- `docs/PRD.md`：产品需求、功能优先级和边界。
- `docs/TECH_DESIGN.md`：技术架构、数据模型和关键技术点。
- `docs/PROJECT_STRUCTURE.md`：目录结构和资产位置。

## 2. 开发环境

当前项目以 Windows + Python 环境为主，路径中包含中文目录，所有路径处理都必须兼容中文路径。

主要技术栈：

- Python
- PyQt5
- PyTorch / TorchScript
- NumPy / pandas
- pyserial
- wfdb
- unittest

常用入口：

```powershell
# 启动上位机
cd 模型部署pyqt\ECGMonitor
python main.py

# 运行部署侧单元测试
cd 模型部署pyqt\ECGMonitor
python -m unittest discover -s tests -p "test_*.py" -v

# 从项目根目录运行部署侧单元测试
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v

# 离线回放 mock 推理
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --mock-label 2

# 离线回放真实模型
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --real-model

# UI smoke check
cd 模型部署pyqt\ECGMonitor
python tests\check_param_monitor_ui.py
```

## 3. 开发规范

- 每次改动前先确认改动属于训练侧、部署侧、文档、测试还是资产整理，不要把多个方向混在一个任务里。
- 不要把训练侧逻辑写入部署侧 GUI，也不要让训练脚本依赖 PyQt 界面。
- GUI 负责展示和调度，不直接承担协议解析、模型加载、数据导出细节。
- CLI 回放和 GUI 回放必须共用 `replay_utils` 中的回放源解析逻辑，并统一把 ECG、导联和心率事件交给 `EcgProcessingPipeline`。
- 离线回放不得通过 `SerialInferenceWorker._process_packet()` 复用处理逻辑；该方法只允许作为 worker 内部薄包装存在。
- 新增模型文件、样例数据、运行产物时必须放到约定目录，不要散落在代码根目录。
- 运行时产物进入 `模型部署pyqt/ECGMonitor/runs/`，默认不纳入版本管理。
- 训练侧大文件和实验资产优先进入 `artifacts/training/ecg/`。
- 改动导出、回放、推理、线程生命周期时，必须考虑回归风险。

## 4. 代码风格

- 保持现有 Python 模块风格，优先小步修改，不做无关重构。
- 文件和函数职责要清晰，避免继续把业务逻辑堆进 `ParamMonitor`。
- PyQt 自动生成文件如 `*_ui.py`、`img_rc.py` 不写业务逻辑。
- 新增文本默认使用 UTF-8，避免再次引入中文乱码。
- 处理文件路径时使用 `os.path` 或等价路径 API，不手写脆弱字符串拼接。
- 日志和错误提示应说明具体失败原因，例如模型缺失、串口失败、回放文件不存在。
- 模型输入窗口、标签数量、归一化参数必须与部署模型契约保持一致。
- ECG 处理相关逻辑必须进入 `ecg_pipeline.py`；`SerialInferenceWorker` 只负责串口打开、读取、字节解包、线程退出和 Qt 信号转发。

## 5. 测试要求

根据改动类型选择测试范围。

### 5.1 文档或纯说明改动

- 检查 Markdown 结构和链接路径。
- 不需要运行完整单元测试，除非文档改动伴随代码改动。

### 5.2 UI 文案或展示规则改动

至少运行：

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
cd 模型部署pyqt\ECGMonitor
python tests\check_param_monitor_ui.py
```

### 5.3 串口、worker、线程生命周期改动

至少运行：

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
```

并重点关注：

- `test_ecg_pipeline.py`
- `test_worker_mock_serial.py`
- `test_offline_replay.py`
- `test_offline_replay_worker.py`
- 程序关闭时是否出现 `QThread: Destroyed while thread is still running`

### 5.4 模型加载或推理链路改动

至少运行：

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --real-model
```

重点确认：

- 模型文件能加载。
- `Diagnosis count` 正常。
- 不出现中文路径或 TorchScript 加载错误。

### 5.5 导出或回放改动

至少运行：

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --mock-label 2
```

如果改动涉及真实模型或最新回放文件，再补充：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --latest --real-model
```

## 6. 注意事项

- 当前系统不是 Web 项目，不要在 V1 中强行引入前后端分离、数据库或服务化架构。
- 当前 V1 不保存真实患者身份信息，不建立完整病例库。
- 诊断结果必须被描述为辅助提示，不要写成最终临床诊断。
- mock 推理只能证明流程通，不能证明真实模型可用。
- 真实模型回放是保护模型部署链路的关键检查。
- 训练侧优化必须保持训练输入窗口、归一化方式、标签映射和部署侧一致。
- 替换 `models/best_acc.pt` 前，必须确认模型输入 shape、输出类别数、标签含义、归一化参数和推理耗时。
- 不要删除或覆盖用户已有的实验资产、运行产物或未提交改动。
- 发现历史乱码时，单独拆清理任务，不要混入功能改动。
- 涉及临床产品化、真实患者数据、权限审计、医生复核时，需要先更新 PRD 和技术设计，再进入实现。

## 7. Demo 闭环开发口径

Demo 运行契约见 `docs/DEMO_RUNBOOK.md`。当前 demo 只证明部署侧闭环可运行：样例 ECG 数据进入离线回放，经 `EcgProcessingPipeline` 触发 mock 或真实 TorchScript 推理，在 PyQt GUI 中展示波形、心率、导联、辅助识别结果和运行指标，并导出可追溯产物。

开发 demo 相关任务时应保持以下口径：

- 不把 mock 推理描述为真实模型能力。
- 不把真实模型 smoke 描述为医学准确率验证。
- 不把辅助识别结果描述为最终临床诊断。
- 不为了 demo 引入 Web、数据库、病例管理或医院系统集成。
- 一键 demo、健康检查和打包改动必须保护现有手动 GUI 启动、CLI 回放和导出闭环。
