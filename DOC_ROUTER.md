# DOC ROUTER

本文档是项目文档路由入口，用来帮助人和 AI 在不同任务中选择最少、最相关的文档，避免上下文污染和阶段信息混乱。

原则：

- 先读当前阶段，再读长期设计。
- 先读目标相关文档，不默认通读全部文档。
- 代码事实与文档冲突时，先核对代码，再更新文档。
- 涉及医学能力表述时，永远采用保守口径：AI 输出是辅助提示，不是临床诊断。

## 1. 文档优先级

| 优先级 | 文档 | 用途 | 什么时候读 |
| --- | --- | --- | --- |
| P0 | `DOC_ROUTER.md` | 文档入口和路由规则 | 每次开始较复杂任务前先看。 |
| P0 | `docs/CURRENT_PHASE.md` | 当前阶段快照、已完成事项、风险和下一步 | 接续对话、阶段判断、规划新任务时必读。 |
| P1 | `docs/AGENT.md` | AI 协作开发规范、测试范围、禁止事项 | 准备改代码、改测试、改 Demo 或改 UI 前读。 |
| P1 | `README.md` | 对外展示入口、一键运行、项目亮点 | 做产品案例、README、展示说明、公开材料时读。 |
| P1 | `docs/TECH_DESIGN.md` | 长期技术架构、模块边界、数据流和关键技术点 | 做架构判断、模块拆分、依赖方向、技术取舍时读。 |
| P1 | `docs/PROJECT_STRUCTURE.md` | 目录结构、模块位置、资产位置 | 找文件、判断改动范围、整理目录时读。 |
| P2 | `docs/PRD.md` | 产品目标、V1 范围、非目标、验收标准 | 判断需求是否越界、讨论功能优先级时读。 |
| P2 | `docs/MODEL_CONTRACT.md` | 模型文件、输入窗口、归一化、输出标签契约 | 涉及模型加载、预测结果、标签、契约校验时读。 |
| P2 | `docs/DEMO_RUNBOOK.md` | Demo 运行路径、成功标准、失败回退、展示顺序 | 涉及一键运行、Demo 展示、演示失败排查时读。 |
| P2 | `docs/UI_REDESIGN.md` | 展示型 UI 的视觉契约、控件契约、布局约束 | 涉及 UI、截图、展示样式、右侧信息区、波形视觉时读。 |
| P2 | `docs/PRODUCT_EXPERIENCE.md` | 产品体验闭环、用户场景、状态反馈和展示口径 | 涉及产品化优化、用户旅程、UI 状态文案、README 体验叙事时读。 |
| P2 | `docs/PRODUCT_CASE.md` | 产品案例主线、问题定义、用户痛点和功能取舍 | 涉及产品案例、评审讲述主线、展示证据组织时读。 |
| P2 | `docs/DEMO_SCRIPT.md` | 1 分钟 / 3 分钟 Demo 讲解脚本和追问提示 | 准备项目展示讲述、评审介绍、Demo 口播时读。 |
| P2 | `docs/SCREENSHOT_WALKTHROUGH.md` | 截图标注方案和界面区域走查 | 做截图标注、README 截图说明、界面体验解释时读。 |
| P2 | `docs/PRODUCT_DECISIONS.md` | 关键产品决策记录 | 解释为什么这样做、为什么不做某些功能、准备产品追问时读。 |
| P2 | `docs/ARCHITECTURE_OVERVIEW.md` | 公开架构图、模块关系、依赖方向摘要 | 做公开架构展示、README 链接、项目讲述时读。 |
| P2 | `docs/DATA_AND_MODEL_NOTICE.md` | 公开数据范围、模型范围、评估边界 | 涉及数据、模型能力、公开说明和评估边界时读。 |
| P2 | `docs/MODEL_EVALUATION_STATUS.md` | 当前模型评估事实、未知项和 smoke test 解释 | 涉及模型指标、评估边界、训练结果表述时读。 |
| P2 | `docs/PUBLIC_SHOWCASE_PLAN.md` | 公开展示主线、README 叙事和训练到部署表达 | 修改公开展示叙事、亮点排序、架构讲述口径时读。 |
| P2 | `docs/PUBLICATION_BOUNDARY.md` | GitHub 公开仓库边界和发布规则 | 涉及公开分支、远端仓库、发布同步和公开资产检查时读。 |
| P2 | `docs/PUBLIC_RELEASE_CHECKLIST.md` | 公开分支同步前的人工门禁清单 | 发布前检查、选择性同步、公开资产审查时读。 |
| P2 | `模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md` | 测试选择规则和回归范围 | 准备验证改动、设计测试、收尾验收时读。 |

## 2. 核心长期文档

这些文档描述长期世界观，变动频率应低。

| 文档 | 负责回答 | 不负责 |
| --- | --- | --- |
| `docs/PRD.md` | 这个系统做什么、不做什么、当前 V1 的产品边界 | 不记录具体代码实现细节。 |
| `docs/TECH_DESIGN.md` | 架构分层、训练侧/部署侧边界、数据流、关键技术决策 | 不记录临时阶段进度。 |
| `docs/PROJECT_STRUCTURE.md` | 文件和目录在哪里、模块大致职责是什么 | 不解释为什么这样设计。 |
| `docs/AGENT.md` | AI 开发协作规则、常用命令、测试要求和开发禁忌 | 不替代具体技术设计。 |
| `README.md` | 给外部读者的项目入口和展示说明 | 不承载完整架构细节。 |

使用规则：

- 做长期架构判断时，优先读 `TECH_DESIGN.md`。
- 判断需求是否属于当前 V1 时，优先读 `PRD.md`。
- 找文件或约束改动范围时，优先读 `PROJECT_STRUCTURE.md`。
- 准备实际改代码时，必须结合 `AGENT.md` 和相关专项文档。

## 3. 阶段文档

阶段文档描述“当前走到哪一步”，用于防止 AI 把历史计划当成当前事实。

| 文档 | 用途 | 什么时候读 |
| --- | --- | --- |
| `docs/CURRENT_PHASE.md` | 当前阶段快照：架构状态、模块状态、已解决/未解决问题、技术债、风险、禁止事项、下一阶段建议 | 每次接续开发、规划下一阶段、生成新任务拆解前读。 |

阶段文档规则：

- `CURRENT_PHASE.md` 只记录当前阶段事实，不写长期理论。
- 每完成一个较大优化方向后，人类将通过适当的prompt更新 `CURRENT_PHASE.md`。
- 历史阶段判断如果和 `CURRENT_PHASE.md` 冲突，以 `CURRENT_PHASE.md` 为当前上下文入口。
- 如果 `CURRENT_PHASE.md` 与代码事实冲突，以代码事实为准，并提醒人类更新文档。

## 4. 专项文档

专项文档只在相关任务中读取，避免无关上下文进入任务。

| 文档 | 专项领域 | 适用场景 |
| --- | --- | --- |
| `docs/MODEL_CONTRACT.md` | 模型契约 | 模型文件、窗口长度、归一化、标签顺序、真实模型 smoke。 |
| `docs/DEMO_RUNBOOK.md` | Demo 闭环 | 一键 Demo、固定场景、演示路径、失败回退、成功标准。 |
| `docs/UI_REDESIGN.md` | 展示型 UI | UI 布局、视觉风格、控件契约、截图、右侧三卡结构、波形视觉。 |
| `docs/PRODUCT_EXPERIENCE.md` | 产品体验闭环 | 产品化优化、核心用户旅程、状态反馈、操作引导和 README 体验叙事。 |
| `docs/PRODUCT_CASE.md` | 产品案例 | 项目展示主线、问题定义、核心用户、痛点机会和功能取舍。 |
| `docs/DEMO_SCRIPT.md` | Demo 讲解 | 1 分钟 / 3 分钟讲述脚本、展示问答、演示步骤与支撑关系。 |
| `docs/SCREENSHOT_WALKTHROUGH.md` | 截图走查 | 截图标注区域、用户问题、设计意图、功能支撑和边界说明。 |
| `docs/PRODUCT_DECISIONS.md` | 产品决策 | 固定 Demo、辅助提示、导出复盘、范围收缩等关键决策解释。 |
| `docs/ARCHITECTURE_OVERVIEW.md` | 公开架构说明 | 对外展示架构图、模块关系、依赖方向和验证闭环。 |
| `docs/DATA_AND_MODEL_NOTICE.md` | 数据与模型边界 | 公开数据范围、模型范围、评估边界和后续模型更新要求。 |
| `docs/MODEL_EVALUATION_STATUS.md` | 模型评估状态 | 当前已知评估事实、未记录信息、smoke test 的真实含义和后续指标。 |
| `docs/PUBLIC_SHOWCASE_PLAN.md` | 公开展示主线 | README、架构说明、数据与模型说明中的对外表达一致性。 |
| `docs/PUBLICATION_BOUNDARY.md` | 公开发布边界 | `main` / `github-public` 分支策略、公开资产白名单和禁止公开内容。 |
| `docs/PUBLIC_RELEASE_CHECKLIST.md` | 公开发布门禁 | 从 `main` 选择性同步到 `github-public` 前的人工检查清单。 |
| `模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md` | 测试策略 | 改动收尾、回归范围选择、UI smoke、真实模型 smoke。 |
| `模型部署pyqt/ECGMonitor/models/model_contract.schema.md` | 模型契约格式 | 修改或审查契约 JSON 字段时读。 |
| `模型部署pyqt/ECGMonitor/models/README.md` | 部署模型目录说明 | 替换或整理部署模型文件时读。 |
| `模型部署pyqt/ECGMonitor/sample_data/README.md` | 样例数据说明 | 修改样例数据、Demo row、回放输入时读。 |

使用规则：

- 不相关就不读。
- 只读相关章节，先用标题定位。
- 专项文档不能推翻长期架构，只能细化对应领域。

## 5. 任务到文档的路由规则

| 任务类型 | 必读 | 选读 |
| --- | --- | --- |
| 接续当前工作、生成阶段快照 | `DOC_ROUTER.md`、`docs/CURRENT_PHASE.md` | `README.md`、相关专项文档 |
| 拆解下一阶段优化任务 | `docs/CURRENT_PHASE.md`、`docs/PRD.md`、`docs/TECH_DESIGN.md` | 相关专项文档 |
| 架构设计、模块边界、依赖方向 | `docs/TECH_DESIGN.md`、`docs/PROJECT_STRUCTURE.md` | `docs/CURRENT_PHASE.md` |
| 修改部署侧代码 | `docs/CURRENT_PHASE.md`、`docs/AGENT.md`、`docs/PROJECT_STRUCTURE.md` | `模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md`、相关专项文档 |
| 修改 ECG 管线、串口、回放 | `docs/TECH_DESIGN.md`、`docs/AGENT.md`、`模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md` | `docs/DEMO_RUNBOOK.md` |
| 修改模型加载、预测、标签 | `docs/MODEL_CONTRACT.md`、`docs/TECH_DESIGN.md`、`模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md` | `模型部署pyqt/ECGMonitor/models/model_contract.schema.md` |
| 修改 Demo、一键运行、打包 | `docs/DEMO_RUNBOOK.md`、`docs/CURRENT_PHASE.md`、`docs/AGENT.md` | `README.md` |
| 修改 UI、截图、展示样式 | `docs/UI_REDESIGN.md`、`docs/CURRENT_PHASE.md`、`模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md` | `README.md` |
| 修改产品体验、用户旅程、状态文案 | `docs/PRODUCT_EXPERIENCE.md`、`docs/PRD.md`、`docs/UI_REDESIGN.md` | `docs/DEMO_RUNBOOK.md`、`README.md` |
| 修改产品案例、讲解脚本、截图走查 | `docs/PRODUCT_CASE.md`、`docs/PRODUCT_EXPERIENCE.md`、`docs/DEMO_RUNBOOK.md` | `docs/DEMO_SCRIPT.md`、`docs/SCREENSHOT_WALKTHROUGH.md`、`docs/PRODUCT_DECISIONS.md` |
| 修改 README、产品案例材料 | `README.md`、`docs/PRODUCT_CASE.md`、`docs/PUBLIC_SHOWCASE_PLAN.md`、`docs/CURRENT_PHASE.md` | `docs/TECH_DESIGN.md`、`docs/DEMO_RUNBOOK.md`、`docs/UI_REDESIGN.md` |
| 修改公开架构说明 | `docs/ARCHITECTURE_OVERVIEW.md`、`docs/TECH_DESIGN.md`、`docs/CURRENT_PHASE.md` | `docs/PROJECT_STRUCTURE.md` |
| 修改训练侧公开说明 | `README.md`、`docs/PUBLIC_SHOWCASE_PLAN.md`、`docs/MODEL_EVALUATION_STATUS.md` | `artifacts/training/ecg/README.md`、`docs/ARCHITECTURE_OVERVIEW.md` |
| 修改数据或模型公开说明 | `docs/DATA_AND_MODEL_NOTICE.md`、`docs/MODEL_EVALUATION_STATUS.md`、`docs/MODEL_CONTRACT.md`、`docs/CURRENT_PHASE.md` | `docs/PUBLICATION_BOUNDARY.md` |
| 发布或同步 GitHub 公开分支 | `docs/PUBLICATION_BOUNDARY.md`、`docs/PUBLIC_RELEASE_CHECKLIST.md`、`docs/AGENT.md`、`docs/CURRENT_PHASE.md` | `README.md`、`check_public_release.ps1` |
| 判断功能是否该做 | `docs/PRD.md`、`docs/CURRENT_PHASE.md` | `docs/TECH_DESIGN.md` |
| 整理文件、移动资产 | `docs/PROJECT_STRUCTURE.md`、`docs/AGENT.md` | 相关目录 README |
| 选择测试范围 | `docs/AGENT.md`、`模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md` | 相关专项文档 |

## 6. AI 读取策略

为降低上下文污染，AI 执行任务时按下面顺序选择文档：

1. 先读 `DOC_ROUTER.md` 判断任务类型。
2. 再读 `docs/CURRENT_PHASE.md` 获取当前阶段事实。
3. 只读 1-3 个与任务直接相关的专项文档。
4. 需要代码事实时，用 `rg` 定位文件和符号，不通读整个项目。
5. 涉及测试时，再读 `docs/AGENT.md` 和 `模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md`。

建议读文档数量：

| 任务规模 | 建议读取 |
| --- | --- |
| 简单问答 | 1-2 个文档 |
| 文档整理 | 2-4 个文档 |
| 普通代码改动 | 3-5 个文档 |
| 架构判断 | 3-6 个文档 |
| 阶段规划 | `CURRENT_PHASE.md` + 长期文档 + 相关专项文档 |

不要默认读取：

- `docs/assets/` 下的图片文件。
- 训练数据、模型 checkpoint、运行产物。
- PyQt 自动生成文件，除非任务涉及 UI 布局。
- 历史截图，除非任务涉及展示资产对比。

## 7. 冲突处理原则

文档或代码出现冲突时按以下顺序裁决：

1. **运行代码事实优先**：当前代码、配置、模型契约文件是最终事实来源。
2. **当前阶段优先**：当前状态以 `docs/CURRENT_PHASE.md` 为入口。
3. **长期边界优先**：产品边界看 `docs/PRD.md`，架构边界看 `docs/TECH_DESIGN.md`。
4. **专项事实优先**：模型看 `MODEL_CONTRACT.md` 和契约 JSON；Demo 看 `DEMO_RUNBOOK.md`；UI 看 `UI_REDESIGN.md`。
5. **医学表述从严**：任何冲突中，只要涉及诊断能力，采用更保守说法。

常见冲突处理：

| 冲突 | 处理 |
| --- | --- |
| README 和代码入口不一致 | 先核对代码和脚本，再更新 README。 |
| 阶段快照和技术设计不一致 | 快照用于当前状态，技术设计用于长期原则；必要时同步二者。 |
| 文档说已完成但测试不存在 | 不视为已验证，补测试或降低表述。 |
| UI 文档和实际控件名不一致 | 以代码控件名为准，更新 `UI_REDESIGN.md`。 |
| 模型标签文档和 contract JSON 不一致 | 以 contract JSON 为准，更新文档。 |
| Demo 文档和 `DEMO_REPLAY_POLICY` 不一致 | 以 `DEMO_REPLAY_POLICY` 为准，更新 Demo 文档。 |

## 8. 文档维护规则

低维护成本优先：

- 新增文档前，先判断能否补到现有文档。
- 一个文档只负责一个层级：长期原则、当前阶段、专项说明不要混写。
- 完成一个阶段后，只更新 `docs/CURRENT_PHASE.md`，不回写所有历史说明。
- 修改模型契约、Demo、UI、测试策略时，同步更新对应专项文档。
- 新增长期核心文档时，必须更新本路由表。

推荐命名：

| 类型 | 命名 |
| --- | --- |
| 当前阶段 | `docs/CURRENT_PHASE.md` |
| 长期设计 | `docs/TECH_DESIGN.md`、`docs/PRD.md` |
| 专项说明 | `docs/<TOPIC>.md` |
| 展示材料 | `docs/<SHOWCASE_TOPIC>.md` 或 `docs/assets/` |
| 测试说明 | 放在相关测试目录，例如 `模型部署pyqt/ECGMonitor/tests/TEST_STRATEGY.md` |

## 9. 当前推荐入口

如果不知道从哪里开始，按这个顺序：

```text
DOC_ROUTER.md
-> docs/CURRENT_PHASE.md
-> docs/AGENT.md
-> docs/TECH_DESIGN.md 或相关专项文档
```

如果是给外部读者或项目评审者：

```text
README.md
-> docs/PRODUCT_CASE.md
-> docs/DEMO_SCRIPT.md
-> docs/SCREENSHOT_WALKTHROUGH.md
-> docs/ARCHITECTURE_OVERVIEW.md
```

如果是 AI 继续开发：

```text
DOC_ROUTER.md
-> docs/CURRENT_PHASE.md
-> docs/AGENT.md
-> 任务相关专项文档
-> 代码检索
```
