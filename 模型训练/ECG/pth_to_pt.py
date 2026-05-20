import torch
from model import CNNModel
from paths import MODEL_ARTIFACTS_DIR

device = torch.device('cpu')
model = CNNModel()
MODEL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
model.load_state_dict(torch.load(MODEL_ARTIFACTS_DIR / 'best_acc.pth', map_location=device))
# model.load_state_dict(torch.load(MODEL_ARTIFACTS_DIR / 'epoch_40.pth', map_location=device))

model.eval()
model.to(device)
example = torch.rand(1, 1, 2000)
example = example.to(device)
traced_script_module = torch.jit.trace(model, example)
# traced_script_module.save(str(MODEL_ARTIFACTS_DIR / "epoch_40.pt"))
traced_script_module.save(str(MODEL_ARTIFACTS_DIR / "best_acc.pt"))
print(f"最佳模型已成功导出为 {MODEL_ARTIFACTS_DIR / 'best_acc.pt'}")
