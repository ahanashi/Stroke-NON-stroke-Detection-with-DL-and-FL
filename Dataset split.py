# -*- coding: utf-8 -*-
"""eda.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18DgW6tv3aX3lFidkcsHy_uAgt0s9-DHo
"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# 
# !pip install gdown
# !gdown https://drive.google.com/uc?id=1U6pF0v7LsIIBzhAOQ9W3ALUh9iN-kNf-
# 
# !unzip gdrive.zip
# !mv gdrive/* .
# !rm -rf gdrive

!pip install -q -r requirements.txt

import os
import cv2
import yaml
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
ROOT = Path().resolve()

np.random.seed(42)

num_clients = 3
train_df = pd.read_csv('data/train.csv')

# 1. Split the data into 3 parts
# 2. Each client, we will split dataset into 2 parts: 80% training and 20% validation
num_samples = len(train_df)
index_list = np.arange(num_samples)
np.random.shuffle(index_list)

num_samples_per_client = num_samples // num_clients
train_df["client"] = None
train_df["is_train"] = None
for i in range(num_clients):
    if i == num_clients - 1:
        idx = index_list[i * num_samples_per_client:]
    else:
        idx = index_list[i * num_samples_per_client: (i + 1) * num_samples_per_client]
    training_idex = idx[:int(len(idx) * 0.8)]
    validation_index = idx[int(len(idx) * 0.8):]

    train_df.loc[idx, "client"] = i
    train_df.loc[training_idex, "is_train"] = True
    train_df.loc[validation_index, "is_train"] = False

train_df.to_csv('data/train.csv', index=False)
train_df.describe()

data_dir = "data/images/"
index2label = {0: "stroke", 1: "no stroke"}

def show_image(image_name):
    image = cv2.imread(data_dir + image_name)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape
    print("Image shape: ", image.shape)

    anno_path = image_name.split(".")[0] + ".txt"
    anno = np.loadtxt(data_dir + anno_path).reshape(-1, 5)
    for idx, cx, cy, w, h in anno:
        x1 = int((cx - w / 2) * width)
        y1 = int((cy - h / 2) * height)
        x2 = int((cx + w / 2) * width)
        y2 = int((cy + h / 2) * height)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 1)
        cv2.putText(image, index2label[int(idx)], (x1 + 5, y1 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

    plt.imshow(image)
    plt.axis("off")
    plt.show()

np.random.seed(None)
image_name = train_df.sample()["image"].values[0]
show_image(image_name)

np.random.seed(None)
test_df = pd.read_csv('data/test.csv')

image_name = test_df.sample()["image"].values[0]
show_image(image_name)

# Create client data folder and remove old data if exists
!mkdir -p data/clients && rm -rf data/clients/*

cfg = yaml.load(open("data/cfg.yaml", "r"), Loader=yaml.FullLoader)
for i in range(num_clients):
    print(f"Client {i}")
    !mkdir -p data/clients/{i}/train
    !mkdir -p data/clients/{i}/val

    # Distribute data to each client
    train_image_list = train_df[(train_df["client"] == i) & (train_df["is_train"] == True)]["image"].to_list()
    val_image_list = train_df[(train_df["client"] == i) & (train_df["is_train"] == False)]["image"].to_list()

    for image_name in train_image_list:
        path = f"{ROOT}/data/clients/{i}"
        cfg["path"] = path
        with open(f"{path}/cfg.yaml", "w") as f:
            yaml.dump(cfg, f)

        # Check if image and annotation file exists
        if not os.path.exists(data_dir + image_name) or not os.path.exists(data_dir + image_name.split(".")[0] + ".txt"):
            continue
        # !cp data/images/{image_name} data/clients/{i}/train
        # !cp data/images/{image_name.split(".")[0]}.txt data/clients/{i}/train
        shutil.copy(data_dir + image_name, f"data/clients/{i}/train")
        shutil.copy(data_dir + image_name.split(".")[0] + ".txt", f"data/clients/{i}/train")

    for image_name in val_image_list:
        # Check if image and annotation file exists
        if not os.path.exists(data_dir + image_name) or not os.path.exists(data_dir + image_name.split(".")[0] + ".txt"):
            continue
        # !cp data/images/{image_name} data/clients/{i}/val
        # !cp data/images/{image_name.split(".")[0]}.txt data/clients/{i}/val
        shutil.copy(data_dir + image_name, f"data/clients/{i}/val")
        shutil.copy(data_dir + image_name.split(".")[0] + ".txt", f"data/clients/{i}/val")

!mkdir -p data/clients/test && rm -rf data/clients/test/*
!mkdir -p data/clients/test/val

cfg = yaml.load(open("data/cfg.yaml", "r"), Loader=yaml.FullLoader)
for image_name in test_df["image"].to_list():
    path = f"{ROOT}/data/clients/test"
    cfg["path"] = path
    cfg["train"] = None
    cfg["val"] = "val"

    with open(f"{path}/cfg.yaml", "w") as f:
        yaml.dump(cfg, f)

    # Check if image and annotation file exists
    if not os.path.exists(data_dir + image_name) or not os.path.exists(data_dir + image_name.split(".")[0] + ".txt"):
        continue
    # !cp data/images/{image_name} data/clients/test/val
    # !cp data/images/{image_name.split(".")[0]}.txt data/clients/test/val
    shutil.copy(data_dir + image_name, f"data/clients/test/val")
    shutil.copy(data_dir + image_name.split(".")[0] + ".txt", f"data/clients/test/val")