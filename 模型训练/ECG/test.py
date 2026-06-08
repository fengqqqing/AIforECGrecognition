# 模型评估脚本
# 职责：加载测试数据和模型，计算混淆矩阵、各类别 accuracy/precision/recall/F1，
#       绘制 ROC 曲线和混淆矩阵热力图。
# 注意：此脚本使用 best_acc.pth（PyTorch 权重），而非部署侧的 best_acc.pt（TorchScript）。

import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from dataset import test_loadData
from dataset_ import test_loadData_
from draw import plot_HeatMap
from model import CNNModel
from paths import MODEL_ARTIFACTS_DIR


if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')           # GPU or CPU
    X, Y = test_loadData_()                                                          # 加载数据集

    min_val = np.array([1582])
    max_val = np.array([2444])
    X = (X - min_val) / (max_val - min_val)

    X_tensor = torch.tensor(X, dtype=torch.float32).permute(0, 2, 1)
    Y_tensor = torch.tensor(Y, dtype=torch.long)
    train_dataset = torch.utils.data.TensorDataset(X_tensor, Y_tensor)
    train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=1, shuffle=False)

    model = CNNModel()                                                              # 加载模型
    # model.load_state_dict(torch.load(MODEL_ARTIFACTS_DIR / 'epoch_40.pth', map_location=device))
    model.load_state_dict(torch.load(MODEL_ARTIFACTS_DIR / 'best_acc.pth', map_location=device))
    # model = torch.jit.load(MODEL_ARTIFACTS_DIR / 'best_acc.pt')
    model.to(device)
    model.eval()                                                                    # 测试

    true_labels = []
    predicted_scores = []
    name = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
    conf_matrix = torch.zeros(12, 12)
    with torch.no_grad():
        for x, y in train_loader:
            x = x.to(device=device)
            y = y.to(device=device)
            outputs = model(x)
            _, pred = torch.max(outputs, 1)                                         # 预测分类
            for t, p in zip(y.view(-1), pred.view(-1)):                             # 计算混淆矩阵
                conf_matrix[t.long(), p.long()] += 1
                predicted_scores.append(outputs.softmax(1).cpu().numpy())           # 记录预测概率
                true_labels.append(y.cpu().numpy())                                 # 记录真实标签
    predicted_scores = np.concatenate(predicted_scores, axis=0)                     # 将预测概率转换为numpy数组
    true_labels = np.concatenate(true_labels, axis=0)                               # 将真实标签转换为numpy数组
    predicted_scores_ = np.argmax(predicted_scores, axis=1)                         # 将预测概率转换为预测标签
    plot_HeatMap(true_labels, predicted_scores_)                                    # 绘制混淆矩阵热力图

    plt.figure(figsize=(8, 6))
    for i in range(12):                                                             # 遍历每一个类别
        TP = conf_matrix[i, i]                                                      # 计算TP、FP、FN、TN
        FP = conf_matrix[:, i].sum() - TP
        FN = conf_matrix[i, :].sum() - TP
        TN = conf_matrix.sum() - (TP + FP + FN)
        accuracy = (TP + TN) / conf_matrix.sum()                                    # 计算准确率、精确度、召回率、F1分数
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        print(f"类别: {name[i]}")
        print(f"准确率: {accuracy:.4f}")
        print(f"精确度: {precision:.4f}")
        print(f"召回率: {recall:.4f}")
        print(f"F1分数: {f1:.4f}")
        print('---------------------------------')

        fpr, tpr, _ = roc_curve(true_labels == i, predicted_scores[:, i])           # 计算ROC曲线
        roc_auc = auc(fpr, tpr)                                                     # 计算AUC
        plt.plot(fpr, tpr, label=f"{name[i]} (AUC = {roc_auc:.2f})")                # 绘制ROC曲线

    plt.plot([0, 1], [0, 1], color='navy', linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve for Each Class')
    plt.legend(loc="lower right")
    plt.show()
