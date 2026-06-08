# CNN 分类模型定义模块
# 模型结构：4 层 1D 卷积（Conv1d + BatchNorm + ReLU + Pooling）+ 2 层全连接
# 输入 shape: (B, 1, 2000)，输出: (B, 12) 对应 12 个心电分类。
# 注意：输入窗口长度 2000 与部署侧模型契约一致，修改结构需同步更新部署侧。

import torch
from torch import nn


class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()
        # 优化点：卷积层后紧跟 BatchNorm1d
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=4, kernel_size=21, stride=1, padding=10)
        self.bn1 = nn.BatchNorm1d(4)
        self.pool1 = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)

        self.conv2 = nn.Conv1d(in_channels=4, out_channels=16, kernel_size=23, stride=1, padding=11)
        self.bn2 = nn.BatchNorm1d(16)
        self.pool2 = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)

        self.conv3 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=25, stride=1, padding=12)
        self.bn3 = nn.BatchNorm1d(32)
        self.pool3 = nn.AvgPool1d(kernel_size=3, stride=2, padding=1)

        self.conv4 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=27, stride=1, padding=13)
        self.bn4 = nn.BatchNorm1d(64)

        # 全连接层保持不变，但可以微调 Dropout
        self.fc1 = nn.Linear(64 * 250, 128)
        self.dropout = nn.Dropout(p=0.3)  # 优化点：从0.2微调至0.3，增强正则化
        self.fc2 = nn.Linear(128, 12)

    def forward(self, x):
        # x shape: (B, 1, 2000) -> 4 层卷积 -> 展平 -> 2 层全连接 -> (B, 12)
        x = torch.relu(self.bn1(self.conv1(x)))  # 优化点：Tanh换成ReLU能缓解梯度消失
        x = self.pool1(x)

        x = torch.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)

        x = torch.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)

        x = torch.relu(self.bn4(self.conv4(x)))

        x = x.view(x.size(0), -1)  # 展平
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x