"""Implementation of UNET Training"""
import os
import datetime
import torch.cuda
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
from techniques.unet.model import UNET
from preprocessing.Dataset import train_transform, val_transform
from techniques.unet.net_utils import (
    get_loaders,
    val_fn,
    save_preds_as_imgs,
    CheckpointSaver
)

from utils.definitions import (
    DTS_TRAIN_PATH,
    DTS_VALIDATION_PATH,
    DTS_ANALYZE_PATH,
    DEPTH,
    LEARNING_RATE,
    DEVICE,
    BATCH_SIZE,
    NUM_EPOCHS,
    NUM_WORKERS,
    UNET_PATH,
    UNET_RESULTS_PATH,
    UNET_RESULTS_CHECKPOINTS,
    IMG_HEIGHT,
    IMG_WIDTH,
    PIN_MEMORY,
    LOAD_MODEL
)


def train_fn(loader, model, optimizer, loss_fn, scaler):
    """Function for training

    :param loader:
    :param model:
    :param optimizer:
    :param loss_fn:
    :param scaler:
    :return:
    """
    pbar = tqdm(enumerate(loader), total=len(loader))
    for batch_idx, item in pbar:
        data = item['img'].to(device=DEVICE)
        targets = item['target'].float().to(device=DEVICE)

        optimizer.zero_grad()

        # forward
        with torch.cuda.amp.autocast():
            predictions = model(data)
            loss = loss_fn(predictions, targets)

        # backward
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        # update tqdm loop
        pbar.set_description(f"Processing {batch_idx + 1}/{len(loader)}, train_loss = {loss.item()}")


def main():
    # define all elements for training
    model = UNET(in_channels=DEPTH, out_channels=DEPTH).to(DEVICE)
    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scaler = torch.cuda.amp.GradScaler()

    # import loader for train and validation
    train_loader, val_loader = get_loaders(
        train_path=DTS_TRAIN_PATH,
        val_path=DTS_VALIDATION_PATH,
        batch_size=BATCH_SIZE,
        train_transforms=train_transform,
        val_transforms=val_transform,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY  # to improve speedup to transfer data from cpu to gpu
    )

    # define train dir
    train_name = datetime.datetime.today().strftime('day_%d_%m_%Y_time_%H_%M_%S')
    os.makedirs(UNET_RESULTS_CHECKPOINTS, exist_ok=True)
    checkpoint_saver = CheckpointSaver(os.path.join(UNET_RESULTS_CHECKPOINTS, f'{train_name}.pth.tar'))

    if LOAD_MODEL:
        print("=> Loading checkpoint")
        checkpoint_name = sorted(os.listdir(UNET_RESULTS_CHECKPOINTS))[-1]
        checkpoint = torch.load(os.path.join(UNET_RESULTS_CHECKPOINTS, checkpoint_name))
        model.load_state_dict(checkpoint["state_dict"])
        val_fn(val_loader, model, loss_fn, device=DEVICE)

    # start training
    for epoch in range(NUM_EPOCHS):
        # train
        print(f'epoch = {epoch}/{NUM_EPOCHS}')
        train_fn(train_loader, model, optimizer, loss_fn, scaler)

        # # save model
        # checkpoint = {"state_dict": model.state_dict(), "optimizer": optimizer.state_dict()}
        # print("=> Saving checkpoint")
        # torch.save(checkpoint, os.path.join(UNET_RESULTS_CHECKPOINTS, f'{train_name}.pth.tar'))

        # validation
        val_loss = val_fn(val_loader, model, loss_fn, device=DEVICE)
        checkpoint_saver.save_checkpoint(val_loss, model.state_dict(), optimizer.state_dict())

        # save images # FIXME
        # save_preds_as_imgs(val_loader, model, DTS_ANALYZE_PATH)


if __name__ == '__main__':
    main()
