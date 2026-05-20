import numpy as np
import seaborn
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from paths import FIGURES_DIR

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# 绘制ECG信号
def plot_signal(signal):
    plt.plot(signal)
    plt.title("ECG Signal")
    plt.show()


# 绘制混淆矩阵热力图
def plot_HeatMap(Y_test, Y_pred):
    con_mat = confusion_matrix(Y_test, Y_pred)
    plt.figure(figsize=(5, 5))
    seaborn.heatmap(con_mat, annot=True, fmt='.20g', cmap='Blues')
    plt.ylim(0, 12)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.xlabel('预测值', fontsize=12)
    plt.ylabel('真实值', fontsize=12)
    plt.show()


# 绘制损失和准确率曲线
def plot_loss_acc(train_losses, val_losses, val_acc):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.cla()
    plt.plot(np.arange(len(train_losses)), train_losses, label='Train_Loss', color='b')
    plt.plot(np.arange(len(val_losses)), val_losses, label='Val_Loss', color='r')
    plt.legend()
    plt.xlabel('epochs')
    plt.ylabel('Loss')
    plt.savefig(FIGURES_DIR / 'loss.png')
    plt.cla()
    plt.plot(np.arange(len(val_acc)), val_acc, label='Val_Acc', color='r')
    plt.legend()
    plt.xlabel('epochs')
    plt.ylabel('Acc')
    plt.savefig(FIGURES_DIR / 'acc.png')
