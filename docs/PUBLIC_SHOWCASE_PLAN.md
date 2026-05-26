# 公开展示主线说明

本文档用于统一 GitHub 首页、架构说明、数据与模型说明中的公开表达，避免不同文档各自讲述、重点分散或夸大系统能力。

## 1. 一句话定位

本项目是一个从 ECG 模型训练、TorchScript 导出到 PyQt 桌面端离线回放与实时推理展示的 AI 辅助识别 Demo。

更简洁的首页表达可以是：

```text
PyQt5 ECG AI assist monitor with TorchScript inference, offline replay, model contract, and one-click demo.
```

## 2. 面向 GitHub 访问者的核心亮点

| 亮点 | 应传达的信息 | 事实支撑 |
| --- | --- | --- |
| 训练到部署闭环 | 项目不只是 GUI 调模型，也包含训练侧、模型导出和部署侧衔接。 | `模型训练/ECG/`、`artifacts/training/ecg/`、`docs/TECH_DESIGN.md` |
| TorchScript 部署 | 默认模型以 TorchScript 形式被桌面端加载，适合本地 Demo 推理。 | `模型部署pyqt/ECGMonitor/models/best_acc.pt` |
| 模型契约化 | 模型输入窗口、归一化参数和标签顺序由契约文件管理，降低语义漂移风险。 | `best_acc.contract.json`、`docs/MODEL_CONTRACT.md` |
| 处理管线复用 | 串口输入、GUI 回放和 CLI 回放共用 `EcgProcessingPipeline`。 | `ecg_pipeline.py`、`offline_replay.py`、`serial_worker.py` |
| 一键公开 Demo | 无设备环境下可以用固定样例数据启动桌面 Demo，并运行 smoke checks。 | `run_demo.ps1`、`run_demo.bat`、`run_demo_checks.ps1` |
| 可追溯导出 | 运行指标、诊断事件和可回放 ECG 数据会导出为文件，便于复盘。 | `run_exporter.py`、`metrics.jsonl`、`diagnosis.csv`、`ecg_replay.csv` |

亮点数量应控制在 6-8 个以内。README 首屏优先展示“能运行、能解释、边界清楚”，不要堆砌未来规划。

## 3. 训练侧能力怎么讲

训练侧应被描述为模型来源与工程闭环的一部分，而不是当前重点包装的医学效果证明。

推荐表达：

- 训练侧包含 ECG 数据处理、CNN 模型定义、训练、评估与 TorchScript 导出入口。
- 训练侧最终通过 `.pt` 模型和模型契约交付给部署侧。
- 训练侧后续重点是补齐数据版本、训练配置、checkpoint 来源和评估指标记录。
- 当前公开说明可以展示训练链路存在，但不能补写未经验证的 accuracy、F1、recall 或临床结论。

不推荐表达：

- 不把训练侧写成已经具备完整临床验证。
- 不用单次 smoke test 代替独立测试集评估。
- 不把 `best_acc` 名称解释成当前公开可承诺的医学准确率。

## 4. 部署侧闭环怎么讲

部署侧是当前最成熟、最适合公开展示的工程主线。建议围绕下面链路讲：

```text
样例 ECG / 串口输入
-> EcgProcessingPipeline
-> TorchScript 推理
-> PyQt GUI 展示
-> 指标与诊断事件导出
-> 离线回放和 smoke checks
```

推荐表达：

- 公开 Demo 使用固定样例 ECG 数据，无需真实设备即可启动。
- CLI 回放、GUI 回放和串口 worker 共享处理管线，减少行为分叉。
- `run_demo_checks.ps1` 用于验证部署链路可运行，包括 mock 回放和真实模型回放。
- 真实模型 smoke 的含义是“模型文件可加载、推理链路可走通”，不是医学准确率证明。

## 5. 不能夸大的能力

公开文档必须避免以下表述：

- 不承诺临床独立诊断能力。
- 不声称已经完成真实临床验证。
- 不声称具备患者管理、医生复核、权限审计或医院系统接入。
- 不把 smoke test、固定样例回放或单次 GUI 演示写成模型效果评估。
- 不补写未记录的准确率、F1、召回率、混淆矩阵或测试集结论。
- 不把当前桌面 Demo 描述成已产品化医疗器械。

## 6. 文档表达的一致性规则

- README 负责第一眼定位、截图、一键运行和核心亮点。
- `docs/ARCHITECTURE_OVERVIEW.md` 负责训练侧到部署侧的结构关系。
- `docs/DATA_AND_MODEL_NOTICE.md` 负责数据范围、模型范围和评估边界。
- `docs/PUBLICATION_BOUNDARY.md` 负责公开分支、禁入资产和发布流程。
- 涉及医学能力时，统一使用“AI 辅助识别”“辅助提示”“实验验证”。
- 未记录的模型评估信息必须写成“当前未记录”，不能推断或补造。
