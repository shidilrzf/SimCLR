from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, transforms
from torch.utils.data.sampler import SubsetRandomSampler
import numpy as np

from PIL import ImageFilter
from PIL import Image


class GaussianSmoothing(object):
    def __init__(self, radius):
        self.radius = radius

    def __call__(self, image):
        return image.filter(ImageFilter.GaussianBlur(self.radius))


def color_distortion_transform(s=1.0):
    # s is the strength of color distortion.
    color_jitter = transforms.ColorJitter(0.8 * s, 0.8 * s, 0.8 * s, 0.2 * s)
    rnd_color_jitter = transforms.RandomApply([color_jitter], p=0.8)
    rnd_gray = transforms.RandomGrayscale(p=0.2)
    color_distort = transforms.Compose([
        rnd_color_jitter,
        rnd_gray])
    return color_distort


def get_transforms():
    jitter_transform = color_distortion_transform()

    all_transforms = transforms.Compose([
        # transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        # transforms.RandomResizedCrop((224, 224)),
        transforms.RandomHorizontalFlip(p=0.6),
        jitter_transform,
        GaussianSmoothing(1),
        transforms.ToTensor()
    ])
    return all_transforms


class CIFAR10C(datasets.CIFAR10):
    def __init__(self, *args, **kwargs):
        super(CIFAR10C, self).__init__(*args, **kwargs)
        self.transform = get_transforms()

    def __getitem__(self, index):
        img, target = self.data[index], self.targets[index]

        # doing this so that it is consistent with all other datasets
        # to return a PIL Image
        xi = Image.fromarray(img)
        xj = Image.fromarray(img)

        if self.transform is not None:
            xi = self.transform(xi)
            xj = self.transform(xj)

        if self.target_transform is not None:
            target = self.target_transform(target)

        return xi, xj, target


class Loader(object):
    def __init__(self, dataset_ident, file_path, download, batch_size, data_transform, target_transform, use_cuda):

        kwargs = {'num_workers': 4, 'pin_memory': True} if use_cuda else {}

        loader_map = {
            'CIFAR10C': CIFAR10C
        }

        num_class = {
            'CIFAR10C': 10
        }

        # Get the datasets
        train_dataset, test_dataset = self.get_dataset(loader_map[dataset_ident], file_path, download,
                                                       data_transform, target_transform)
        # Set the loaders
        self.train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, **kwargs)
        self.test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, **kwargs)

        tmp_batch, _, _ = self.train_loader.__iter__().__next__()
        self.img_shape = list(tmp_batch.size())[1:]
        self.num_class = num_class[dataset_ident]

    @staticmethod
    def get_dataset(dataset, file_path, download, data_transform, target_transform):

        # Check for transform to be None, a single item, or a list
        # None -> default to transform_list = [transforms.ToTensor()]
        # single item -> list
        if not data_transform:
            data_transform = [transforms.ToTensor()]
        elif not isinstance(data_transform, list):
            data_transform = list(data_transform)

        # Training and Validation datasets
        train_dataset = dataset(file_path, train=True, download=download,
                                transform=transforms.Compose(data_transform),
                                target_transform=target_transform)

        test_dataset = dataset(file_path, train=False, download=download,
                               transform=transforms.Compose(data_transform),
                               target_transform=target_transform)

        return train_dataset, test_dataset
