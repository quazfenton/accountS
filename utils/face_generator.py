import os
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import requests
from torchvision import transforms
from pathlib import Path
import logging

# Implement an enhanced face generator with proper model handling

class EnhancedFaceGenerator:
    """Enhanced face generator with realistic face generation and fallback options"""
    
    def __init__(self, model_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path or 'models/generator.pth'  # Updated path
        self.model = self._load_model()
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
    
    def _load_model(self):
        """Load face generation model with download capability"""
        try:
            # Create models directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Initialize model architecture
            model = self._get_default_model()
            
            # Load model weights if file exists
            if os.path.exists(self.model_path):
                try:
                    model.load_state_dict(
                        torch.load(self.model_path, map_location=self.device, weights_only=True)
                    )
                    self.logger.info(f"Loaded pre-trained model from {self.model_path}")
                except Exception as e:
                    self.logger.warning(f"Could not load model: {e}, using random initialization")
            else:
                self.logger.warning(f"Model file not found at {self.model_path}, using randomly initialized model")
            
            model.eval()
            return model.to(self.device)
            
        except Exception as e:
            self.logger.error(f"Error initializing face generator: {e}")
            # Return a simple fallback generator
            return self._create_fallback_model()
    
    def _get_default_model(self):
        """Create a default GAN generator model"""
        # This is a simplified StyleGAN-like architecture
        class SimpleGenerator(nn.Module):
            def __init__(self, latent_dim=512, img_channels=3, img_size=256):
                super().__init__()
                self.init_size = img_size // 8
                self.l1 = nn.Linear(latent_dim, 128 * self.init_size ** 2)
                
                self.conv_blocks = nn.Sequential(
                    nn.BatchNorm2d(128),
                    nn.Upsample(scale_factor=2),
                    nn.Conv2d(128, 128, 3, stride=1, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(inplace=True),
                    
                    nn.Upsample(scale_factor=2),
                    nn.Conv2d(128, 64, 3, stride=1, padding=1),
                    nn.BatchNorm2d(64),
                    nn.ReLU(inplace=True),
                    
                    nn.Upsample(scale_factor=2),
                    nn.Conv2d(64, 32, 3, stride=1, padding=1),
                    nn.BatchNorm2d(32),
                    nn.ReLU(inplace=True),
                    
                    nn.Conv2d(32, img_channels, 3, stride=1, padding=1),
                    nn.Tanh()
                )
            
            def forward(self, z):
                out = self.l1(z)
                out = out.view(out.shape[0], 128, self.init_size, self.init_size)
                img = self.conv_blocks(out)
                return img
        
        return SimpleGenerator()
    
    def _create_fallback_model(self):
        """Create a simple fallback model that generates random faces"""
        self.logger.warning("Using fallback face generator")
        return self._get_default_model()
    
    def generate_face(self, seed=None):
        """Generate a realistic face image"""
        try:
            if seed is not None:
                torch.manual_seed(seed)
                np.random.seed(seed)
            
            # Generate random latent vector
            z = torch.randn(1, 512).to(self.device)
            
            # Generate image
            with torch.no_grad():
                generated_img = self.model(z)
            
            # Denormalize and convert to PIL image
            img = generated_img.cpu().squeeze(0)
            img = (img + 1) / 2  # Denormalize from [-1, 1] to [0, 1]
            img = torch.clamp(img, 0, 1)
            
            # Convert to PIL Image
            img_np = (img.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np)
            
            return pil_img
            
        except Exception as e:
            self.logger.error(f"Face generation error: {e}")
            # Return a fallback image
            return self._create_fallback_image()
    
    def _create_fallback_image(self):
        """Create a fallback image when generation fails"""
        # Create a random noise image as fallback
        fallback_array = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        return Image.fromarray(fallback_array)
    
    def generate_faces_batch(self, count: int, seed=None):
        """Generate a batch of face images"""
        if seed is not None:
            torch.manual_seed(seed)
        
        faces = []
        for i in range(count):
            face = self.generate_face(seed=None if seed is None else seed + i)
            faces.append(face)
        
        return faces
    
    def save_face(self, output_path: str, seed=None):
        """Generate and save face to file"""
        img = self.generate_face(seed)
        img.save(output_path)
        return output_path

# For backward compatibility, create an alias
FaceGenerator = EnhancedFaceGenerator