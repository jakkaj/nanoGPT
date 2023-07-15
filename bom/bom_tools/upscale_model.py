# Creating a DeepAutoencoder class

import torch
import torchvision


class UpscaleModel(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.decoder = torch.nn.Sequential(
			# input is 1 x 8 x 8
			torch.nn.ConvTranspose2d(1, 128, 4, stride=2, padding=1),
			torch.nn.BatchNorm2d(128),
			torch.nn.ReLU(True),
			# state size. 128 x 16 x 16
			torch.nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1),
			torch.nn.BatchNorm2d(64),
			torch.nn.ReLU(True),
			# state size. 64 x 32 x 32
			torch.nn.ConvTranspose2d(64, 32, 4, stride=2, padding=1),
			torch.nn.BatchNorm2d(32),
			torch.nn.ReLU(True),
			# state size. 32 x 64 x 64
			torch.nn.ConvTranspose2d(32, 1, 4, stride=2, padding=1),
			# state size. 1 x 128 x 128
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

def get_model(rescale_size):
    global model
    if model is not None:
        return model
    model = UpscaleModel()
    model.load_state_dict(torch.load(f'./bom/encoders/RADAR_UPSCALER_{rescale_size}.pth'))
    model = model.to('cuda')
    return model
