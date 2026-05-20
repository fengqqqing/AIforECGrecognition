# 测试策略清单

适用范围：`ECGMonitor` 上位机、离线回放、串口接入、AI 推理与 UI 状态链路。

## 1. 测试目标

这套测试不是追求“全都测到”，而是优先覆盖高风险链路：

- ECG 数据能否正确进入系统
- 数据包能否正确解析
- ECG 累积到窗口长度后能否触发 AI 推理
- 诊断、导联、心率能否正确显示
- 线程、串口、退出路径是否稳定
- 修复一个问题后，旧功能是否被带坏

## 2. 分层测试策略

### A. 单元测试

目标：验证独立逻辑，不依赖真实设备。

当前建议持续保留的点：

- `PackUnpack`：协议打包、解包、校验失败拦截
- `ui_rules`：诊断标签、导联状态、心率显示规则、指标格式化
- `worker_metrics`：指标快照结构
- `ecg_pipeline`：ECG 窗口累计、推理触发、导联/心率事件处理和 metrics 更新
- `model_contract`：契约 JSON 加载、必填字段、窗口、归一化、标签数量和模型文件存在性校验
- `example._get_model()`：模型加载路径与缺文件报错
- `example.warmup_model()`：启动前契约与模型输出类别数一致性检查
- `predict()`：输入窗口处理与输出类别范围

运行命令：

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
```

### B. 集成测试

目标：验证多个模块连起来是否工作。

当前关键链路：

- `EcgProcessingPipeline`：接收 ECG、导联、心率包后累计窗口、触发诊断并更新 metrics
- `SerialInferenceWorker`：负责串口读取、字节解包，并把管线回调转成 Qt 信号
- `OfflineReplayWorker`：读取 CSV 后把回放事件交给 `EcgProcessingPipeline`
- `offline_replay.py`：CLI 回放读取 CSV 后把事件交给 `EcgProcessingPipeline`
- `RunExporter`：指标与诊断结果能否落盘

当前已经覆盖的重点：

- mock 串口输入下的 worker 流处理
- worker 诊断触发
- ECG 管线单元行为
- 离线回放触发 AI 诊断
- 离线回放导联/心率事件传播

### C. 在线/手工测试

目标：验证真实环境依赖与时序问题。

必须人工确认的点：

- 串口能否正常打开
- 模拟器数据是否持续稳定进入
- 实时波形是否刷新
- 心率与导联状态是否按设备行为变化
- 诊断结果是否在窗口凑满后出现
- 关闭窗口时是否还有线程退出异常

## 3. 回归测试清单

每次改动后，至少检查下面 8 项：

1. `PackUnpack` 协议解析正常
2. 离线回放可以跑通
3. 串口 worker 能处理 ECG/导联/心率包
4. ECG 波形刷新逻辑未破坏
5. 导联状态能更新
6. 心率能更新
7. ECG 累积到 2000 点后能产生诊断
8. 程序关闭时无 `QThread: Destroyed while thread is still running`

## 4. 按改动类型选择测试范围

### 改 UI 文案/样式

至少执行：

- 全部单元测试
- 离线回放 smoke test
- `python tests/check_param_monitor_ui.py`
- 手工确认主界面主要状态文案

### 改串口/线程逻辑

至少执行：

- 全部单元测试
- `test_worker_mock_serial.py`
- `test_offline_replay_worker.py`
- 手工验证启动、停止、退出

### 改 ECG 处理管线或 worker 处理逻辑

至少执行：

- `test_ecg_pipeline.py`
- `test_worker_mock_serial.py`
- `test_offline_replay.py`
- `test_offline_replay_worker.py`
- `test_predict.py`
- 离线回放 mock smoke test
- 如涉及真实模型路径，再补离线回放 `--real-model` smoke test

重点确认：

- ECG 包会发出 `ecg_sample`。
- 累计到契约窗口长度后只触发一次 `diagnosis`。
- 推理成功或失败后窗口都会清空。
- 导联脱落会清空窗口。
- 心率大于 0 才发出 `heart_rate`。
- metrics 中 `ecg_packets`、`diagnosis_count`、`lead_events`、`heart_rate_events` 行为不变。
- `OfflineReplayWorker` 和 CLI 回放不得调用 `SerialInferenceWorker._process_packet()`；它们必须直接使用 `EcgProcessingPipeline`。

### 改推理/模型加载逻辑

至少执行：

- `test_model_contract.py`
- `test_example_model_loading.py`
- `test_predict.py`
- `test_worker_mock_serial.py`
- `test_offline_replay_worker.py`
- 离线回放 `--real-model` 烟雾测试

### 改导出/运行摘要逻辑

至少执行：

- `test_run_exporter.py`
- 离线回放一轮后检查 `runs/` 目录内容

## 5. AI 诊断专项测试

AI 诊断建议分三层测，不要只测其中一层。

### 第一层：纯推理接口

目标：确认 `predict()` 本身输入输出稳定。

当前自动化：

- `test_predict.py`

说明：

- 这里使用 mock 模型，重点是验证输入裁剪、张量形状、输出类别范围。

### 第二层：诊断触发链路

目标：确认系统在积累到契约窗口长度后会真的触发诊断。当前默认契约窗口为 `input.window_size=2000`。

当前自动化：

- `test_ecg_pipeline.py`
- `test_worker_mock_serial.py`
- `test_offline_replay.py`
- `test_offline_replay_worker.py`

说明：

- 这里验证的是 `ECG 包 -> EcgProcessingPipeline 累积 -> 调用 predict_func -> diagnosis 回调/信号`。
- 这是“AI 诊断是否显示”的核心保护测试。
- `SerialInferenceWorker`、`OfflineReplayWorker` 和 CLI 回放都应通过管线获得一致处理语义；测试应保护可见信号、输出和 metrics 行为，而不是保护私有方法本身。

### 第三层：真实模型加载烟雾测试

目标：确认当前环境里契约文件和模型文件能被真实加载，并能跑通一次真实推理。

建议命令：

```powershell
cd 模型部署pyqt\ECGMonitor
python offline_replay.py --samples 2000 --real-model
```

成功标准：

- 命令可正常结束
- 输出 `Diagnosis count: 1`
- 不出现契约校验或模型加载失败报错

说明：

- 这一步很重要，因为 mock 推理无法发现模型文件、Torch 环境、路径编码等真实问题。
- smoke test 只代表部署链路可用，不代表模型医学准确率达标。

## 6. 模型替换检查

替换 `models/best_acc.pt` 时，必须同步替换或更新 `models/best_acc.contract.json`。重点检查：

- `model_file` 指向实际模型文件。
- `input.window_size` 和 `input.shape` 与模型输入一致。
- `preprocessing.min_val` 和 `preprocessing.max_val` 与训练/导出时一致。
- `output.num_classes` 等于 `output.labels` 数组长度。
- `output.labels` 顺序与模型输出编号完全一致。

替换后必须运行：

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --real-model
```

## 7. 推荐执行顺序

### 日常开发最小检查

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --mock-label 2
```

### Demo 闭环检查

完成 demo 相关改动后，优先从仓库根目录运行：

```powershell
.\run_demo_checks.ps1
```

该脚本只覆盖 demo 关键路径，按顺序执行：

- 部署侧单元测试
- 固定 demo policy 校验
- 固定场景 mock 回放
- 固定场景真实模型回放

成功标准：

- 脚本退出码为 0。
- 单元测试全部通过。
- mock 和真实模型回放都输出 `Diagnosis count: 1`。
- 真实模型回放不出现契约校验、模型加载或中文路径错误。

### 改动推理链路后的增强检查

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --real-model
```

如果已经完成一次在线采样，建议再补一条回放验证：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --input "模型部署pyqt\ECGMonitor\runs\<timestamp>_serial\ecg_replay.csv" --real-model
```

或者直接使用最新导出的回放文件：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --latest --real-model
```

### 有设备时的在线检查

- 打开串口
- 接入模拟器
- 观察波形、导联、心率、诊断
- 关闭程序确认线程正常退出

## 8. 当前测试边界

当前自动化仍然没有完全覆盖：

- `ParamMonitor` 真实 UI 渲染与控件状态切换
- 串口真实设备时序抖动
- 长时间运行下的资源稳定性
- 多次连接/断开后的恢复行为

这些部分仍然需要手工测试或后续补更高层的 UI/端到端测试。

## 9. UI Smoke Check

用途：

- 验证 `ParamMonitor` 收到诊断、导联、心率更新后，关键标签会正确变化。
- 这是介于“纯单元测试”和“手工点界面”之间的一层轻量自动化检查。

运行命令：

```powershell
cd 模型部署pyqt\ECGMonitor
python tests\check_param_monitor_ui.py
```

成功标准：

- 控制台输出 `ParamMonitor UI smoke check passed.`

说明：

- 当前环境下，Qt 窗口对象在 `unittest discover` 中不够稳定，容易让测试进程挂起。
- 因此这里采用独立 smoke check 脚本，而不是把它并入常规 `test_*.py` 发现流程。
