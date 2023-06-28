# Creating a DeepAutoencoder class

import torch
import torchvision


class UpscaleModel(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.decoder = torch.nn.Sequential(
            torch.nn.Linear(64, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, 512),
            torch.nn.ReLU(),
            torch.nn.Linear(512, 768),
            torch.nn.ReLU(),
            torch.nn.Linear(768, 32 * 32),
            torch.nn.Sigmoid()
        )

    def decode(self, x):
        return self.decoder(x)

    def forward(self, x):

        decoded = self.decode(x)
        return decoded


model = None


def transform_input(input):
	transform = torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),
	])
	return transform(input)

def get_model():
    global model
    if model is not None:
        return model
    model = UpscaleModel()
    model.load_state_dict(torch.load('./bom/encoders/RADAR_UPSCALER.pth'))
    model = model.to('cuda')
    return model
