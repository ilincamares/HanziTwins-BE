import torch

from backend.core.siamese_network import SiameseNetwork


def load_model():
    print("Loading Siamese Neural Network weights...")
    model = SiameseNetwork()
    model.load_state_dict(torch.load('assets/siamese_hanzi_model.pth'))
    print("Model loaded successfully!")