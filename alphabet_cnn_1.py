# -*- coding: utf-8 -*-
"""alphabet-cnn-1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18b1z5ltde8IpJTHa6iR3gkS_QOUOfvEh
"""

#import all the libraries
import os
import string

import numpy as np
import torch
import torch.nn as nn
from torch.nn import functional as F
from torch.optim import Adam
from torch.utils.data import Dataset, DataLoader
from torch.utils.data.sampler import SubsetRandomSampler

import torchvision
#from torchvision import models
from torchvision import transforms
from torchvision.transforms import ToTensor, Normalize

#ord('C') - ord('A')

#Train dataset config
class ASLDatasetTrain(Dataset):
    char_to_int = {c: ord(c) - ord('A') for c in string.ascii_uppercase}
    char_to_int['del'] = 26
    char_to_int['nothing'] = 27
    char_to_int['space'] = 28
    int_to_char = {value: key for key, value in char_to_int.items()}
        
    def __init__(self, directory: str, transform=None, label_transform=None):
        super().__init__()
        
        self.directory = directory
        self.transform = transform
        self.label_transform = label_transform
        
        self.x = None
        self.y = None
        
        self._load_images()
    
    def __getitem__(self, idx):
        x, y = torchvision.io.read_image(self.x[idx]).type(torch.float32), self.y[idx]
        
        if self.transform:
            x = self.transform(x)
        if self.label_transform:
            y = self.label_transform(y)
        
        return x, y
    
    def __len__(self):
        return len(self.y)
    
    def _load_images(self):
        self.x = []
        self.y = []
        
        for c in os.listdir(self.directory):
            class_name = c
            class_dir = os.path.join(self.directory, class_name)
            for img in os.listdir(class_dir):
                self.x.append(os.path.join(class_dir, img))
                self.y.append(self.char_to_int[class_name])
                
        self.y = torch.tensor(self.y, dtype=torch.int64)
    
    @staticmethod
    def get_classname(idx: int) -> str:
        return ASLDatasetTrain.int_to_char[idx]

#Test dataset config
class ASLDatasetTest(Dataset):
    char_to_int = {c: ord(c) - ord('A') for c in string.ascii_uppercase}
    char_to_int['del'] = 26
    char_to_int['nothing'] = 27
    char_to_int['space'] = 28
    int_to_char = {value: key for key, value in char_to_int.items()}
        
    def __init__(self, directory: str, transform=None, label_transform=None):
        super().__init__()
        
        self.directory = directory
        self.transform = transform
        self.label_transform = label_transform
        
        self.x = None
        self.y = None
        
        self._load_images()
    
    def __getitem__(self, idx):
        x, y = torchvision.io.read_image(self.x[idx]).type(torch.float32), self.y[idx]
        
        if self.transform:
            x = self.transform(x)
        if self.label_transform:
            y = self.label_transform(y)
        
        return x, y
    
    def __len__(self):
        return len(self.y)
    
    def _load_images(self):
        self.x = []
        self.y = []
        
        for img in os.listdir(self.directory):
            class_name = img [:1]
            if 'space' in img:
                class_name = 'space'
            elif 'nothing' in img:
                class_name = 'nothing'
            elif 'del' in img:
                class_name = 'del'    
            self.x.append(os.path.join(self.directory, img))
            self.y.append(self.char_to_int[class_name])
                
        self.y = torch.tensor(self.y, dtype=torch.int64)
    
    @staticmethod
    def get_classname(idx: int) -> str:
        return ASLDatasetTest.int_to_char[idx]

#Transformation
ts = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomCrop(224),
    transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
])

#All the data store in train and test
train = ASLDatasetTrain('../input/fingerdataset/dataset/train', transform=ts)
test = ASLDatasetTest('../input/fingerdataset/dataset/test', transform=ts)

#Train and test data print
print(len(train))
print(len(test))

#test path
test.x

#train path
train.x

#sampler
train_sampler = SubsetRandomSampler(np.arange(len(train)))
test_sampler = SubsetRandomSampler(np.arange(len(test)))

#train and test loader using sampler
train_loader = DataLoader(train, 32, sampler=train_sampler)
test_loader = DataLoader(test, 32, sampler=test_sampler)

for x, y in train_loader:
    print(x.shape)
    print(y.shape)

"""# **Alexnet**"""

class AlexNet(nn.Module):
    def __init__(self, num_classes: int = 1000) -> None:
        super(AlexNet, self).__init__()
        
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=11, stride=4, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
            nn.Conv2d(64, 192, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
            nn.Conv2d(192, 384, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(384, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
        )
        self.avgpool = nn.AdaptiveAvgPool2d((6, 6))
        
        self.classifier = nn.Sequential(
            nn.Dropout(),
            nn.Linear(256 * 6 * 6, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.ReLU(inplace=True),
            nn.Linear(4096, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

model = AlexNet(29)

#using adam optimizer
criterion = nn.CrossEntropyLoss()
optimizer = Adam(model.parameters(), lr=0.0001)

#print minibatch of the train data
print(len(train_loader.dataset))
print(len(train_loader))

epochs = 20

for e in range(epochs):
    running_loss = 0.0
    
    for i, (imgs, labels) in enumerate(train_loader):
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        if i % 13 == 12:
            print('[Epoch %d, Step %5d] loss: %.3f' %
                  (e + 1, i + 1, running_loss / 13))
            running_loss = 0.0

def test(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.eval()
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \nAccuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")

test(test_loader, model, nn.CrossEntropyLoss())

#each class accuracy
class_correct = list(0. for i in range(29))
class_total = list(0. for i in range(29))

with torch.no_grad():
    for data in test_loader:
        images, labels = data
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)
        c = (predicted == labels).squeeze()
        for i in range(len(labels)):
            label = labels[i]
            class_correct[label] += c[i].item()
            class_total[label] += 1


for i in range(29):
    print('Accuracy of %5s : %2d %%' % (
        ASLDatasetTest.int_to_char[i], 100 * class_correct[i] / class_total[i]))

"""# **Pre-trained AlexNet**"""

from torchvision import models

"""**Issue on kaggle anyone trying to download the model will fail if the internet option is off at the bottom right.**"""

model = models.alexnet(pretrained=True)

for param in model.parameters():
    param.requires_grad = False

print(model)

new_clf = nn.Sequential(
    nn.Dropout(p=0.5, inplace=False),
    nn.Linear(in_features=9216, out_features=4096, bias=True),
    nn.ReLU(inplace=True),
    nn.Dropout(p=0.5, inplace=False),
    nn.Linear(in_features=4096, out_features=4096, bias=True),
    nn.ReLU(inplace=True),
    nn.Linear(in_features=4096, out_features=1000, bias=True),
    nn.ReLU(inplace=True),
    nn.Linear(in_features=1000, out_features=29, bias=True),
)

model.classifier = new_clf

criterion = nn.CrossEntropyLoss()
optimizer = Adam(model.parameters(), lr=0.0001)

epochs = 20

for e in range(epochs):
    running_loss = 0.0
    for i, (imgs, labels) in enumerate(train_loader):
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        if i % 13 == 12:
            print('[Epoch %d, Step %5d] loss: %.3f' %
                  (e + 1, i + 1, running_loss / 13))
            running_loss = 0.0

test(test_loader, model, nn.CrossEntropyLoss())

"""# ResNet101"""

#Used resnet 101 instead of resnet 152
model = models.resnet101(pretrained=True)

print(model)

new_fc = torch.nn.Sequential(
    nn.Linear(in_features=2048, out_features=1000, bias=True),
    nn.ReLU(inplace=True),
    nn.Linear(in_features=1000, out_features=29, bias=True),
)

model.fc = new_fc

criterion = nn.CrossEntropyLoss()
optimizer = Adam(model.parameters(), lr=0.0001)

epochs = 5

for e in range(epochs):
    running_loss = 0.0
    for i, (imgs, labels) in enumerate(train_loader):
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        if i % 13 == 12:
            print('[Epoch %d, Step %5d] loss: %.3f' %
                  (e + 1, i + 1, running_loss / 12))
            running_loss = 0.0

test(test_loader, model, nn.CrossEntropyLoss())