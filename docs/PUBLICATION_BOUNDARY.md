# 公开仓库发布边界

本文档定义当前 GitHub 公开仓库应该包含什么、不包含什么，以及后续同步时必须遵守的边界。它服务于长期一致性：让公开版本稳定可运行，同时避免把大体积实验资产、运行输出或不适合公开的内部上下文带入仓库。

## 1. 分支策略

当前采用双分支策略：

| 分支 | 职责 | 发布方式 |
| --- | --- | --- |
| `main` | 本地完整开发主线，可保留训练侧历史和内部阶段文档。 | 不直接推送为 GitHub 公开主线。 |
| `github-public` | GitHub 公开发布分支，只包含公开安全文件和可运行 Demo 资产。 | 使用 `git push origin HEAD:main` 发布到远端 `main`。 |

后续不要把 `main` 直接 merge 到 `github-public`。公开更新应从 `main` 选择性同步文件，例如：

```powershell
git switch github-public
git checkout main -- README.md docs/PUBLICATION_BOUNDARY.md docs/DATA_AND_MODEL_NOTICE.md docs/ARCHITECTURE_OVERVIEW.md
git status
git push origin HEAD:main
```

## 2. 公开仓库应包含

- 部署侧 PyQt 上位机源码。
- ECG 处理管线、模型契约、离线回放和导出相关代码。
- 一键 Demo 脚本：`run_demo.ps1`、`run_demo.bat`、`run_demo_checks.ps1`。
- 小体积 Demo 所需模型和契约：`模型部署pyqt/ECGMonitor/models/best_acc.pt`、`best_acc.contract.json`。
- 小体积样例数据：`模型部署pyqt/ECGMonitor/sample_data/test.csv`。
- README、技术设计、Demo runbook、模型契约说明、UI 说明和架构说明。
- 训练侧源码、训练曲线图片和契约模板。

## 3. 公开仓库不应包含

- 原始 ECG 数据目录：`artifacts/training/ecg/raw_data/`。
- 整理后的完整训练数据目录：`artifacts/training/ecg/processed_data/`。
- 训练 checkpoint 和中间模型：`artifacts/training/ecg/models/*.pth`、`artifacts/training/ecg/models/*.pt`。
- 部署侧历史模型归档：`模型部署pyqt/ECGMonitor/models/archive/`。
- 运行输出目录：`模型部署pyqt/ECGMonitor/runs/`。
- 构建产物：`build/`、`dist/`。
- Python 缓存、IDE 本地配置和临时日志。
- 包含个人规划、沟通记录或内部阶段判断的上下文文件。

## 4. 公开表述边界

公开仓库应保持中性、工程化表述：

- 使用“公开演示”“项目说明”“设计边界”“AI 辅助识别”“实验验证”。
- 不使用私人准备、内部讲述、阶段计划等语境。
- 不把 smoke test 结果描述为医学准确率。
- 不承诺临床诊断、医生复核、患者管理、医院系统接入等 V1 未实现能力。
- 不写入真实患者身份信息、敏感医疗数据或不可公开的第三方资产。

## 5. 发布前检查

每次发布前至少执行：

```powershell
git status --short --branch
git ls-files | Select-String -Pattern "raw_data|processed_data|\.pth$|models/archive|ECGMonitor/runs|__pycache__|build/|dist/"
$publicWordingPattern = [string]::Join("|", @("面" + "试", "求" + "职", "作品" + "集"))
rg -n $publicWordingPattern README.md docs
```

如需验证 Demo：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo_checks.ps1
```

如果 `git ls-files` 命中大体积数据、运行输出或归档模型，不应继续推送公开分支。
