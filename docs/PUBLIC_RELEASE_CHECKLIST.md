# 公开发布门禁清单

本文档用于把本地开发主线同步到 GitHub 公开分支前的检查步骤固化下来。它是发布前人工检查清单，不是自动发布授权。

## 1. 目标

降低后续公开迭代风险，确保：

- 不直接发布本地 `main`。
- 不把 `main` merge 到 `github-public`。
- 不把原始数据、完整训练数据、训练 checkpoint、运行输出或内部上下文带入公开仓库。
- 不把 Demo smoke test 描述为医学准确率验证。

## 2. 发布前必须确认

| 检查项 | 通过标准 | 失败时处理 |
| --- | --- | --- |
| 当前任务范围 | 本轮只同步公开安全文件。 | 停止同步，重新列出文件清单。 |
| 工作区状态 | `main` 上改动已完成审查；`github-public` 不含未解释改动。 | 停止，先处理未提交或不明改动。 |
| 远端仓库 | `origin` 和可选 `ecg-ai-monitor` 指向 `https://github.com/fengqqqing/ecg-ai-monitor.git`。 | 停止，先修正 remote。 |
| 分支策略 | 只从 `main` 选择性同步文件到 `github-public`。 | 禁止 merge，禁止直接推送 `main`。 |
| 禁入资产 | `git ls-files` 不命中禁入目录或文件。 | 停止，先移出公开分支索引并审查原因。 |
| 公开表达 | README 和 docs 不含私人准备语境，不夸大医学能力。 | 停止，先改文档。 |

## 3. 允许同步的文件类型

通常允许从 `main` 同步到 `github-public`：

- `README.md`
- `LICENSE`
- `requirements.txt`
- `run_demo.ps1`
- `run_demo.bat`
- `run_demo_checks.ps1`
- `check_public_release.ps1`
- `docs/` 下公开说明文档和公开截图
- `模型部署pyqt/ECGMonitor/` 下部署侧源码、测试、样例数据、默认部署模型和契约
- `模型训练/ECG/` 下训练侧源码
- `artifacts/training/ecg/README.md`
- `artifacts/training/ecg/figures/` 下小体积公开图像
- `artifacts/training/ecg/models/contract_template.json`

是否允许同步，应以“公开仓库是否需要它运行 Demo 或理解工程设计”为判断标准。

## 4. 绝对禁止进入公开分支

以下内容不得进入 `github-public`：

```text
artifacts/training/ecg/raw_data/
artifacts/training/ecg/processed_data/
artifacts/training/ecg/models/*.pth
artifacts/training/ecg/models/*.pt
模型部署pyqt/ECGMonitor/models/archive/
模型部署pyqt/ECGMonitor/runs/
build/
dist/
__pycache__/
```

也不得公开：

- 个人规划、沟通记录或内部阶段判断。
- 真实患者身份信息、敏感医疗数据或无授权第三方资产。
- 未验证的模型指标、临床结论或医生复核能力。

## 5. 选择性同步步骤

先在 `main` 完成开发和审查，再切到公开分支：

```powershell
git switch github-public
git status --short --branch
```

确认公开分支状态干净后，只同步本轮公开安全文件。例如：

```powershell
git checkout main -- README.md docs/PUBLICATION_BOUNDARY.md docs/DATA_AND_MODEL_NOTICE.md docs/ARCHITECTURE_OVERVIEW.md
```

本轮如果新增公开门禁文件，可按需同步：

```powershell
git checkout main -- docs/PUBLIC_RELEASE_CHECKLIST.md docs/PUBLIC_SHOWCASE_PLAN.md check_public_release.ps1
```

同步后必须先检查，不要立即发布：

```powershell
git status --short --branch
powershell -ExecutionPolicy Bypass -File .\check_public_release.ps1
```

如本轮改动影响 Demo 入口、模型契约、回放或 README 中的运行说明，再运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo_checks.ps1
```

## 6. 发布失败或检查失败时如何停止

遇到以下任何情况，立即停止同步或发布：

- 当前分支不是 `github-public`。
- 发现禁入目录或禁入文件被追踪。
- 发现 README 或 docs 中存在不适合公开的私人语境。
- remote 指向不是 `fengqqqing/ecg-ai-monitor`。
- `run_demo_checks.ps1` 失败且本轮改动影响 Demo 入口。
- 不确定某个文件是否公开安全。

停止后只做诊断和记录，不做推送、不做合并、不改写历史。需要继续时，先回到文件清单和发布边界重新审查。

## 7. 最终发布规则

只有在人工确认以下条件全部满足后，才可以从 `github-public` 发布到远端 `main`：

- 本轮同步文件清单明确。
- 禁入资产检查通过。
- 公开表达检查通过。
- 必要的 Demo 检查通过。
- `git status` 中只包含本轮预期文件。

发布命令仍必须由人工确认后执行。本文档不授权 AI 在未得到明确指令时自动推送远端。
