import numpy as np
import matplotlib.pyplot as plt
import torchvision
import torch

class DeepDecoder(torch.nn.Module):
	def __init__(self):
		super().__init__()		
		
		
		self.decoder = torch.nn.Sequential(
			torch.nn.Linear(9, 9),
			torch.nn.ReLU(),
			torch.nn.Linear(64, 128),
			torch.nn.ReLU(),
			torch.nn.Linear(128, 256),
			torch.nn.ReLU(),
			torch.nn.Linear(256, 28 * 28),
			torch.nn.Sigmoid()
		)

	

	def decode(self, x):
		return self.decoder(x)
	def forward(self, x):		
		decoded = self.decode(x)
		return decoded