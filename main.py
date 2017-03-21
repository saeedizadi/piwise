import argparse
import numpy as np
import visdom

from piwise import network, dataset

from torch import nn, optim, autograd
from torch.utils import data
from torchvision import utils, transforms

def vis_image(vis, image, epoch, step, name):
    if image.is_cuda:
        image = tensor.cpu()
    if isinstance(image, autograd.Variable):
        image = image.data
    image = image.numpy()

    if len(image.shape) == 3:
        if image.shape[0] == 3:
            image = image.transpose((1, 2, 0))
        if image.shape[0] == 1:
            image = image[0].transpose((0, 1))
    if image.dtype == np.int64:
        image = image.astype(np.uint8)

    vis.image(image,
        opts=dict(title=f'{name} (epoch: {epoch}, step: {step})'))

def main(args):
    model = network.Basic()

    if args.cuda:
        model.cuda()

    loader = data.DataLoader(dataset.VOC2012(args.dataroot,
        input_transform=transforms.Compose([
            transforms.CenterCrop(256),
            transforms.ToTensor(),
        ]),
        target_transform=transforms.Compose([
            transforms.CenterCrop(256),
            transforms.ToTensor(),
            transforms.Lambda(lambda t: t.mul(255).long()[0]),
        ])), num_workers=args.num_workers, batch_size=args.batch_size)

    optimizer = optim.Adam(model.parameters())
    criterion = network.CrossEntropySoftmax2d()

    if args.visdom:
        vis = visdom.Visdom()

    for epoch in range(args.num_epochs+1):
        epoch_loss = []

        for step, (images, labels) in enumerate(loader):
            if args.cuda:
                images = images.cuda()
                labels = labels.cuda()
            inputs = autograd.Variable(images)
            targets = autograd.Variable(labels)
            outputs = model(inputs)

            optimizer.zero_grad()
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            epoch_loss.append(loss.data[0])

            if args.visdom and step % args.visdom_steps == 0:
                vis_image(vis, inputs[0], epoch, step, 'input')
                vis_image(vis, outputs[0], epoch, step, 'output')
                vis_image(vis, targets[0], epoch, step, 'target')

        print(f'epoch: {epoch}, epoch_loss: {sum(epoch_loss)}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cuda', action='store_true')
    parser.add_argument('--visdom', action='store_true')
    parser.add_argument('--visdom-steps', type=int, default=10)
    parser.add_argument('--num-epochs', type=int, default=5)
    parser.add_argument('--num-workers', type=int, default=2)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--dataroot', nargs='?', default='data')
    parser.add_argument('--trainroot', nargs='?', default='train')
    main(parser.parse_args())
