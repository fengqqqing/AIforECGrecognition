# Demo 运行手册

本文档定义当前 ECG 上位机 demo 的运行契约：展示时跑什么、应该看到什么、怎样判断成功，以及失败时如何回退。它服务于“医生辅助识别工具”的实验演示，不把模型输出描述为最终临床诊断。

## 1. Demo 定位

当前 demo 目标是证明部署侧闭环可运行：

```text
样例 ECG 数据
-> 离线回放
-> ECG 处理管线
-> TorchScript 或 mock 推理
-> PyQt GUI 展示
-> 运行指标与回放产物导出
```

演示重点是工程闭环、路径兼容、模型契约接入和无设备验证能力。不要承诺医学准确率、自动临床诊断、患者管理、医院系统接入或真实临床可用性。

## 2. 当前可运行入口

### 2.1 一键 GUI Demo

从仓库根目录执行：

```powershell
.\run_demo.ps1
```

也可以双击根目录的 `run_demo.bat`。

脚本会自动定位 `*pyqt\ECGMonitor\main.py`，并以 `--demo` 启动固定 demo 场景。启动后应看到 PyQt 上位机主界面自动进入离线回放演示态。

当前主界面操作入口分为两层：

菜单栏只保留传统入口：

- `串口设置`
- `退出`

顶部操作区是 demo 展示主入口：

- `离线回放`
- `回放设置`
- `最近摘要`
- `导出目录`
- `重置显示`

如果模型契约、模型文件、样例数据或 demo policy 存在问题，`--demo` 启动阶段会弹出清晰的阻断提示。普通 `python main.py` 启动不做 demo 预检弹窗。

普通 GUI 启动入口仍然保留：

```powershell
cd 模型部署pyqt\ECGMonitor
python main.py
```

### 2.2 CLI 离线回放 smoke

从仓库根目录执行 mock 回放：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --row 3 --samples 2000 --event-interval 500 --lead-events 0,0,0,0 --hr-events 72,84,78,90 --mock-label 0
```

从仓库根目录执行真实模型回放：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --row 3 --samples 2000 --event-interval 500 --lead-events 0,0,0,0 --hr-events 72,84,78,90 --real-model
```

真实模型回放成功时，控制台至少应包含：

- `Replay finished`
- `Inference mode: real-model`
- `Diagnosis count: 1`
- `Latest diagnosis: <编号>`

### 2.3 Demo 验证脚本

从仓库根目录执行：

```powershell
.\run_demo_checks.ps1
```

该脚本会运行部署侧单元测试、固定 demo policy 校验、固定场景 mock 回放和固定场景真实模型回放。

## 3. GUI 演示路径

推荐演示路径：

1. 在仓库根目录执行 `.\run_demo.ps1`，或双击 `run_demo.bat`。
2. 主界面打开后，确认顶部模式徽标进入 Demo 启动或运行状态。
3. 观察中央 ECG 波形区刷新，波形区是主视觉。
4. 观察右侧 `心率` 卡更新为固定 demo 心率序列中的值。
5. 观察右侧 `导联状态` 卡保持三导联单通道连接语义。
6. 等待 2000 点固定窗口完成后，观察 `AI 辅助识别` 卡出现辅助识别结果。
7. 观察底部运行指标区更新包计数、诊断次数、推理耗时、吞吐量和事件计数。
8. 等待回放完成后，顶部模式提示应显示已完成，可通过 `最近摘要` 查看导出结果。
9. 点击 `最近摘要`，确认本次导出路径、指标、诊断记录和回放文件路径存在。
10. 点击 `导出目录`，确认本次运行产物位于 `模型部署pyqt\ECGMonitor\runs\`。

固定 demo policy 位于 `config.py` 的 `DEMO_REPLAY_POLICY`，当前使用 `sample_data/test.csv` 第 4 行（`row=3`）、`samples=2000`、`event_interval=500`、导联事件 `[0, 0, 0, 0]`、心率事件 `[72, 84, 78, 90]`。

## 4. 成功标准

一次 demo 可判定成功，需要同时满足：

- GUI 能启动，并且没有阻断真实模型使用的契约错误。
- 离线回放可以从 `模型部署pyqt\ECGMonitor\sample_data\test.csv` 读取样本。
- ECG 波形在主界面持续刷新。
- 心率和导联事件可以在界面上更新。
- AI 辅助识别、心率、导联状态和运行指标在新版展示区中可读。
- ECG 累计到模型契约窗口 `input.window_size=2000` 后产生至少一次辅助识别结果。
- 运行指标展示中诊断次数、ECG 采样点数、导联事件和心率事件能更新。
- 本次运行可以生成或更新导出产物：
  - `metrics.jsonl`
  - `diagnosis.csv`
  - `ecg_replay.csv`
- `最近运行摘要` 能展示本次运行路径和关键结果。

真实模型 smoke 的最低成功标准是：

```text
Diagnosis count: 1
```

该标准只说明部署推理链路可用，不说明医学准确率达标。

## 5. 失败回退

### 5.1 GUI 启动失败

优先检查当前目录是否正确：

```powershell
cd 模型部署pyqt\ECGMonitor
python main.py
```

如果提示缺少 PyQt5、torch、numpy、pandas 或 pyserial，说明运行环境未安装完整依赖。不要把依赖缺失描述为模型能力问题。

### 5.2 模型契约或模型文件失败

检查以下路径是否存在：

- `模型部署pyqt\ECGMonitor\models\best_acc.contract.json`
- `模型部署pyqt\ECGMonitor\models\best_acc.pt`

可先回退到 mock CLI 回放，证明回放管线仍可工作：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --mock-label 2
```

对外讲述时应说明：mock 只验证流程，不验证真实模型加载或真实模型输出。

### 5.3 样例数据缺失或行号非法

检查样例数据路径：

- `模型部署pyqt\ECGMonitor\sample_data\test.csv`

固定 demo policy 使用 `row=3`，即 CSV 第 4 行。非法 row 或样例数据不足会在 `--demo` 启动预检中提前提示。

### 5.4 GUI 回放异常

优先用 CLI 分层定位：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --mock-label 2
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --real-model
```

如果 CLI 正常而 GUI 异常，重点检查 `ParamMonitor.py`、`offline_replay_worker.py` 和线程退出路径。

## 6. 面试讲述顺序

建议按下面顺序讲，避免把能力讲过头：

1. 项目定位：这是 ECG 辅助识别实验系统，不是临床独立诊断产品。
2. 架构边界：训练侧负责模型训练和导出，部署侧 PyQt 上位机负责采集、展示、回放、导出和推理接入。
3. 模型契约：部署侧不硬编码模型语义，而是读取 `best_acc.contract.json` 中的窗口、归一化和标签顺序。
4. 无设备验证：通过 `sample_data/test.csv` 离线回放，保护 ECG 处理管线和 GUI 展示。
5. 展示型 UI：波形是主视觉，右侧三卡展示 AI 辅助识别、心率和三导联单通道导联状态，底部展示运行指标。
6. 真实模型验证：使用 `--real-model` smoke 证明 TorchScript 模型和中文路径加载链路可用。
7. 可追溯导出：运行后导出 `metrics.jsonl`、`diagnosis.csv` 和 `ecg_replay.csv`，后续可继续回放。
8. 当前限制：模型精度、临床数据、医生复核、权限审计和医院系统集成都不是 V1 已实现能力。

## 7. 自动化契约

自动 demo 当前应保持以下约束：

- `python main.py --demo` 打开 GUI 后自动进入固定离线回放演示态。
- 根目录 `run_demo.ps1` 和 `run_demo.bat` 固定工作目录，再调用部署侧入口。
- 自动 demo 使用 `DEMO_REPLAY_POLICY`，不依赖用户手动选择行号或样本数。
- 自动 demo 失败时给出明确阻断提示，说明是缺模型、缺契约、缺样例数据还是配置非法。
- 非 demo 模式保持手动启动行为，不弹 demo readiness 阻断提示。

## 8. 展示资产

README 首页截图固定引用：

```text
docs/assets/screenshots/demo-gui.png
```

更新截图时建议使用一次完整 demo 运行后的主界面，画面中应能看到 ECG 波形、AI 辅助识别卡、心率卡、导联状态卡和底部运行指标。截图只展示当前工程闭环，不应加入模型准确率或临床诊断结论类标注。
