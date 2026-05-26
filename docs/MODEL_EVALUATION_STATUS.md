# 模型评估状态说明

本文档说明当前公开仓库中“模型评估到什么程度”，用于区分部署链路验证、训练侧产物和医学准确率验证。

## 1. 当前已知事实

| 项目 | 当前事实 | 来源 |
| --- | --- | --- |
| 默认部署模型 | `模型部署pyqt/ECGMonitor/models/best_acc.pt` | `best_acc.contract.json` |
| 模型格式 | TorchScript，CPU 推理 | `docs/MODEL_CONTRACT.md` |
| 输入窗口 | `2000` 点，shape 为 `["B", 1, 2000]` | `best_acc.contract.json` |
| 归一化 | min-max，`min_val=1582.0`，`max_val=2444.0` | `best_acc.contract.json` |
| 输出标签 | 12 分类标签，顺序由契约定义 | `best_acc.contract.json` |
| 部署 smoke | 固定样例真实模型回放可触发 `Diagnosis count: 1` | `run_demo_checks.ps1` |
| 公开训练图 | `artifacts/training/ecg/figures/acc.png`、`loss.png` | `artifacts/training/ecg/README.md` |

以上事实可以证明：当前项目具备模型契约、TorchScript 加载、固定样例回放和 PyQt 展示的部署链路。

## 2. 当前未记录信息

以下信息当前没有可靠公开记录，不能补写成事实：

- `best_acc.pt` 对应的来源 checkpoint。
- 默认模型使用的数据版本和数据划分。
- 训练时使用的完整超参数配置。
- 独立测试集 accuracy、macro-F1、各类别 precision/recall/F1。
- 混淆矩阵、ROC/AUC 或类别级误判分析。
- 推理耗时的正式 benchmark。
- 真实临床采集数据上的验证结果。

## 3. Smoke Test 的真实含义

`run_demo_checks.ps1` 中的真实模型回放用于验证部署链路：

```text
样例 ECG CSV
-> 离线回放
-> EcgProcessingPipeline
-> TorchScript 推理
-> 诊断事件输出
```

当输出 `Diagnosis count: 1` 时，只能说明：

- 样例数据可读。
- ECG 窗口能累计到模型输入长度。
- TorchScript 模型可加载并返回分类结果。
- 部署侧管线能把结果传给 CLI/GUI 链路。

它不能说明：

- 模型医学准确率达标。
- 某个类别的召回率可靠。
- 模型可以用于临床独立诊断。
- 固定样例结果可以代表整体测试集表现。

## 4. 后续应补的评估指标

后续模型评估建议最少补齐：

| 指标/产物 | 用途 |
| --- | --- |
| 数据版本说明 | 明确训练、验证、测试数据来源和划分方式。 |
| 训练配置 | 记录窗口长度、归一化方式、模型结构、epoch、batch size、学习率等。 |
| 总体 accuracy | 作为基础可比指标，但不能单独代表模型质量。 |
| macro-F1 | 避免类别不均衡时只看整体准确率。 |
| 各类别 recall | 关注高风险类别漏检情况。 |
| 混淆矩阵 | 分析误判方向和类别间混淆。 |
| 模型来源记录 | 关联 `.pth`、`.pt`、契约 JSON 和评估结果。 |
| 推理耗时 | 确认模型升级不会破坏桌面端实时展示。 |

## 5. 当前不能承诺的能力

当前公开文档和 README 不能承诺：

- 医学准确率达标。
- 已完成真实临床验证。
- 可替代医生诊断。
- 已具备医生复核、患者管理、权限审计或医院系统接入。
- 固定 Demo 结果等同于模型泛化能力。

## 6. 结论

当前模型评估状态应概括为：

```text
部署链路已可验证，模型医学效果仍需独立评估记录。
```

后续若更新模型，应同时更新模型契约和评估记录；未知信息必须写明“当前未记录”，不能以推测或文件名补全。
