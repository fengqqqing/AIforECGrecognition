import torch
import numpy as np
from torch import nn, optim
from  tqdm import tqdm
from dataset import train_loadData
from dataset_ import train_loadData_
from draw import plot_loss_acc
from model import CNNModel
from paths import MODEL_ARTIFACTS_DIR
import os
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'


if __name__ == '__main__':
    MODEL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')   # GPU or CPU
    X_train, Y_train, X_val, Y_val = train_loadData_()                       # 加载数据集

    min_val = np.array([1582])
    max_val = np.array([2444])
    X_train = (X_train - min_val) / (max_val - min_val)
    X_val = (X_val - min_val) / (max_val - min_val)

    X_train_tensor = torch.tensor(X_train, dtype=torch.float32).permute(0, 2, 1)
    Y_train_tensor = torch.tensor(Y_train, dtype=torch.long)
    X_val_tensor = torch.tensor(X_val, dtype=torch.float32).permute(0, 2, 1)
    Y_val_tensor = torch.tensor(Y_val, dtype=torch.long)
    train_dataset = torch.utils.data.TensorDataset(X_train_tensor, Y_train_tensor)
    val_dataset = torch.utils.data.TensorDataset(X_val_tensor, Y_val_tensor)
    train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=128, shuffle=True)
    val_loader = torch.utils.data.DataLoader(dataset=val_dataset, batch_size=128, shuffle=False)

    model = CNNModel()                                                      # 加载模型
    model.to(device)
    criterion = nn.CrossEntropyLoss()                                       # 损失函数
    criterion.to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)  # 优化点：加入 1e-4 的 L2 正则化               # 优化器
    num_epochs = 100                                                        # 迭代次数

    train_losses = []
    val_losses = []
    val_acc = []
    best_acc = 0
    with tqdm(total=num_epochs) as pbar:
        for epoch in range(num_epochs):
            model.train()                                                   # 训练
            train_loss = 0.0
            for i, (x, y) in enumerate(train_loader):
                x, y = x.to(device), y.to(device)
                outputs = model(x)
                loss = criterion(outputs, y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            model.eval()                                                    # 验证
            val_loss = 0.0
            correct = 0
            total = 0
            with torch.no_grad():
                for inputs, labels in val_loader:
                    inputs, labels = inputs.to(device), labels.to(device)
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs, 1)
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()

            if correct / total > best_acc:                                  # 保存最好的模型
                best_acc = correct / total
                torch.save(model.state_dict(), MODEL_ARTIFACTS_DIR / 'best_acc.pth')
            torch.save(model.state_dict(), MODEL_ARTIFACTS_DIR / 'last.pth')         # 保存最后的模型
            if epoch % 10 == 0:                                             # 每10个epoch保存一次模型
                torch.save(model.state_dict(), MODEL_ARTIFACTS_DIR / f'epoch_{epoch}.pth')

            train_losses.append(train_loss / len(train_loader))             # 记录loss和acc
            val_losses.append(val_loss / len(val_loader))
            val_acc.append(correct / total)
            print(f"Epoch {epoch + 1}/{num_epochs}, "
                  f"Train Loss: {train_loss / len(train_loader):.4f}, "
                  f"Val Loss: {val_loss / len(val_loader):.4f}, "
                  f"Val Accuracy: {correct / total:.4f}")

            plot_loss_acc(train_losses, val_losses, val_acc)                # 绘制loss和acc曲线
            pbar.update(1)
