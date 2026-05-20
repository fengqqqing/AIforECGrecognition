# 离线验证说明

## 1）运行单元测试

### 方式 A：先进入 ECGMonitor 目录（推荐）

```powershell
cd 模型部署pyqt\ECGMonitor
python -m unittest discover -s tests -p "test_*.py" -v
```

### 方式 B：在项目根目录直接运行

```powershell
python -m unittest discover -s "模型部署pyqt\ECGMonitor\tests" -p "test_*.py" -t "模型部署pyqt\ECGMonitor" -v
```

当前测试覆盖：
- 协议打包/解包正确性与校验失败拦截
- 推理接口 `predict` 输出范围（使用 mock 模型，避免环境依赖）
- Worker 在 mock 串口输入下的流处理能力
- Worker 触发诊断流程的关键路径

## 2）无设备回放 ECG 数据

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 4000 --mock-label 2
```

说明：
- 默认样例数据位于 `模型部署pyqt\ECGMonitor\sample_data\test.csv`。
- `--mock-label`：使用模拟分类结果，不依赖真实模型加载。
- `--real-model`：切换为真实模型推理模式。
- 当 `--samples` 超过当前行可用 ECG 点数时，会自动截断并打印 `[WARN]`。

### 回放导联与心率事件（离线验证 UI 状态链路）

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --samples 2000 --mock-label 0 --lead-events 0,1,0 --hr-events 72,88,65 --event-interval 500
```

### 直接回放最近导出的 ECG 文件

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --input "模型部署pyqt\ECGMonitor\runs\<timestamp>_serial\ecg_replay.csv" --real-model
```

说明：
- `ecg_replay.csv` 由在线串口运行结束后自动导出。
- 脚本会打印来源文件、来源行号、可用样本数、使用样本数和源标签，便于确认当前回放数据是否来自预期采样。

如果只想直接使用 `runs/` 目录下最新的一份回放文件，可以省略手工路径：

```powershell
python 模型部署pyqt\ECGMonitor\offline_replay.py --latest --real-model
```

## 3）一键离线检查脚本

用途说明：
- 给“当前代码是否可离线运行”做快速体检，适合每次改动后执行一次。
- 不依赖外部设备，默认使用 mock 推理，确保环境稳定可复现。

```powershell
powershell -ExecutionPolicy Bypass -File 模型部署pyqt\ECGMonitor\run_offline_checks.ps1
```

该脚本会按顺序执行：
- 单元测试
- 离线回放（mock 推理）

成功标准：
- 命令退出码为 `0`
- 控制台出现 `Ran 5 tests ... OK`
- 控制台出现 `离线检查完成。`

常见问题排查：
- 提示找不到脚本：确认当前路径是项目根目录，或改用脚本绝对路径。
- PowerShell 执行策略报错：保留命令中的 `-ExecutionPolicy Bypass`。
- 单测导入失败：优先使用 README 中“方式 A”先进入 `ECGMonitor` 目录运行。
