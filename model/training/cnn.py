import torch
from torch import nn


class CNNModel(nn.Module):
    def __init__(
        self,
        vocab_size: int = 300,
        embedding_size: int = 64,
        context_window: int = 6,
        kernel_size: int = 5,
        conv_out_channels: int = 6,
        hidden_dim: int = 128,
    ):
        super(CNNModel, self).__init__()
        self.embedding = nn.Embedding(
            num_embeddings=vocab_size, embedding_dim=embedding_size
        )
        self.conv1d = nn.Conv1d(
            in_channels=embedding_size,
            out_channels=conv_out_channels,
            kernel_size=kernel_size,
        )
        self.fc1 = nn.Linear(
            ((context_window * 2 + 1) - kernel_size + 1) * conv_out_channels,
            hidden_dim,
        )
        self.fc2 = nn.Linear(hidden_dim, 1)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(p=0.2)

    def forward(self, x):
        x = self.embedding(x).permute(0, 2, 1)
        x = self.conv1d(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        output = torch.sigmoid(x)
        return output


if __name__ == "__main__":
    model = CNNModel(vocab_size=300)
    print(model)
