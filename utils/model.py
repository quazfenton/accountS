import torch
import torch.nn as nn
import torch.nn.functional as F

class Generator(nn.Module):
    """
    Improved GAN Generator model for face generation.
    Uses a more sophisticated architecture with convolutional layers.
    """
    def __init__(self, image_size, latent_dim, num_layers):
        super().__init__()
        self.image_size = image_size
        self.latent_dim = latent_dim
        self.num_layers = num_layers
        
        # Calculate initial feature map size
        self.init_size = image_size // (2 ** 4)  # 4 upsampling layers
        
        # Linear layer to expand latent vector
        self.l1 = nn.Sequential(
            nn.Linear(latent_dim, 128 * self.init_size ** 2)
        )
        
        # Convolutional layers for upsampling
        self.conv_blocks = nn.Sequential(
            nn.BatchNorm2d(128),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(128, 128, 3, stride=1, padding=1),
            nn.BatchNorm2d(128, 0.8),
            nn.LeakyReLU(0.2, inplace=True),
            
            nn.Upsample(scale_factor=2),
            nn.Conv2d(128, 64, 3, stride=1, padding=1),
            nn.BatchNorm2d(64, 0.8),
            nn.LeakyReLU(0.2, inplace=True),
            
            nn.Upsample(scale_factor=2),
            nn.Conv2d(64, 32, 3, stride=1, padding=1),
            nn.BatchNorm2d(32, 0.8),
            nn.LeakyReLU(0.2, inplace=True),
            
            nn.Upsample(scale_factor=2),
            nn.Conv2d(32, 3, 3, stride=1, padding=1),
            nn.Tanh()
        )

    def forward(self, z):
        """
        Forward pass for the generator.
        Args:
            z (torch.Tensor): Latent vector.
        Returns:
            torch.Tensor: Generated image.
        """
        out = self.l1(z)
        out = out.view(out.shape[0], 128, self.init_size, self.init_size)
        img = self.conv_blocks(out)
        return img

if __name__ == '__main__':
    # Example usage:
    generator = Generator(image_size=256, latent_dim=512, num_layers=8)
    print(generator)

    # Test with a random latent vector
    z = torch.randn(1, 512)
    output_image = generator(z)
    print(f"Output image shape: {output_image.shape}")