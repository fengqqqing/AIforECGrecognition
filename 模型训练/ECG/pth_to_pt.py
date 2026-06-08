# PyTorch -> TorchScript 模型导出脚本
# 职责：加载 best_acc.pth 权重，通过 torch.jit.trace 导出为 TorchScript 格式
#       （best_acc.pt），供部署侧加载推理。
# 注意：导出时的 dummy input shape (1, 1, 2000) 必须与部署侧模型契约一致。

import torch
from model import CNNModel
from paths import MODEL_ARTIFACTS_DIR

device = torch.device('cpu')
model = CNNModel()
MODEL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
model.load_state_dict(torch.load(MODEL_ARTIFACTS_DIR / 'best_acc.pth', map_location=device))  # 加载训练权重
# model.load_state_dict(torch.load(MODEL_ARTIFACTS_DIR / 'epoch_40.pth', map_location=device))

model.eval()
model.to(device)
example = torch.rand(1, 1, 2000)  # dummy input：shape 与部署侧模型契约一致
example = example.to(device)
traced_script_module = torch.jit.trace(model, example)  # trace 导出 TorchScript
# traced_script_module.save(str(MODEL_ARTIFACTS_DIR / "epoch_40.pt"))
traced_script_module.save(str(MODEL_ARTIFACTS_DIR / "best_acc.pt"))
print(f"最佳模型已成功导出为 {MODEL_ARTIFACTS_DIR / 'best_acc.pt'}")
