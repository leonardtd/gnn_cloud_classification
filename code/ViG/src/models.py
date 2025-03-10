import torch
import torch.nn as nn
import torch.nn.functional as F

from .modules import *


class IsotropicVIG(nn.Module):
    def __init__(self, img_hw, in_channels, out_channels, num_blocks, kernel_size=16, patch_size=4):
        super().__init__()
        
        self.hw = img_hw
        self.num_blocks = num_blocks
        self.patch_size = patch_size

        self.patchifier = Patchifier(
            hw=img_hw, patch_size=patch_size, hidden_channels=in_channels
        )
        self.network = nn.ModuleList()
        self.norms = nn.ModuleList()

        for i in range(num_blocks):
            self.network.append(Block(in_channels, kernel_size))
            self.norms.append(nn.BatchNorm2d(in_channels))

        self.head = nn.Sequential(
            nn.Dropout(0.1),
            nn.Linear(in_channels*(img_hw//patch_size)**2, 512, bias=False),
            nn.GELU(),
            nn.Linear(512, out_channels, bias=True)
        )

        self.reset_parameters()

        
    def reset_parameters(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

            elif isinstance(m, nn.BatchNorm2d) or isinstance(m, nn.InstanceNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def forward(self, x):

        x = self.patchifier(x)

        for i, block in enumerate(self.network):
            x = block(x)
            x = F.gelu(x)
            x = self.norms[i](x)
            x = F.dropout(x, 0.7, training=self.training)

        x = x.flatten(1)
      
        x = self.head(x)

        return x

    


def test_iso_vig():
    # Tiny config
    model = IsotropicVIG(in_channels=192, out_channels=7, num_blocks=12, kernel_size=16)

    x = torch.randn(1, 3, 224, 224)
    print(model(x).shape)  # torch.Size([`batch_size`, `in_channels`, 56, 56])


if __name__ == "__main__":
    test_iso_vig()
