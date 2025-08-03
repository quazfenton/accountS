import os
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from utils.model import Generator # Import the Generator from utils.model

# Placeholder for model download/loading instructions
# In a real scenario, you would download a pre-trained model (e.g., PULSE)
# and place it in the 'models/' directory.
# Example:
# 1. Download pulse.pt from a trusted source.
# 2. Place it in the 'models/' directory: /home/kwasifenton/accountS/models/pulse.pt

class FaceGenerator:
    def __init__(self, model_path='models/pulse.pt'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.load_model(model_path)
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        
    def load_model(self, model_path):
        """Load pre-trained PULSE generator"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        model = Generator(256, 512, 8)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.eval()
        return model.to(self.device)
    
    def generate_face(self, seed=None):
        """Generate a realistic face image"""
        if seed is not None:
            torch.manual_seed(seed)
        
        # Generate latent vector
        z = torch.randn(1, 512, device=self.device)
        
        # Generate image
        with torch.no_grad():
            generated = self.model(z)
        
        # Convert to PIL image
        img = (generated * 0.5 + 0.5).clamp(0, 1)
        img = transforms.ToPILImage()(img.squeeze())
        return img
    
    def save_face(self, output_path, seed=None):
        """Generate and save face to file"""
        img = self.generate_face(seed)
        img.save(output_path)
        return output_path