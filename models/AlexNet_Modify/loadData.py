#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Load cifar-10 data set

@author: Jarvis ZHANG
@date: 2017/7/30
@framework: Tensorflow
@editor: VS Code
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from matplotlib import gridspec
import cifar10, cifar10_input

IMAGE_SIZE = 24

path = "/home/jarvis/DataSet/cifar-10-batches-bin"
label_name = "batches.meta.txt"
bin_file = "data_batch_1.bin"

def next_distorted_batch(size):
    ''' Get a batch of distorted data.  
    This function is used to generate training data.
    ### Params:
        * size - integer: number of images in one batch
    ### Return:
        * images - tensor: a batch of images
        * labels - tensor: a batch of labels
    '''
    images, labels = cifar10_input.distorted_inputs(
        data_dir=path, 
        batch_size=size
    )
    return images, labels

def next_original_batch(size):
    ''' Get a batch of original data.  
    This function is used to generate test data.
    ### Params:
        * size - integer: number of images in one batch
    ### Return:
        * images - tensor: a batch of images
        * labels - tensor: a batch of labels
    '''
    images, labels = cifar10_input.inputs(
        eval_data=True, 
        data_dir=path, 
        batch_size=size
    )
    return images, labels

def read_cifar10(file, size):
    ''' Read cifar-10 data sets
    ### Params:
        * file - string: file path
        * size - integer: size of batch
    ### Return:
        * images - ndarray: images array
        * labels - ndarray: labels array
    '''
    bytestream = open(file, 'rb')
    buf = bytestream.read(size * (32 * 32 * 3 + 1))
    data = np.frombuffer(buf, dtype=np.uint8).reshape(size, -1)
    labels_images = np.hsplit(data, [1])
    labels = labels_images[0].reshape(size).astype(np.int)
    images = labels_images[1].reshape(size, 3, 32, 32)
    bytestream.close()
    return images, labels


def summary_cifar_img():
    ''' Display the cifar-10 data sets '''
    # Get classes from file
    with open(os.path.join(path, label_name)) as f:
        classes = f.readlines()[:-1]
        classes = np.array(classes)

    # Get data
    file_path = os.path.join(path, bin_file)
    images, labels = read_cifar10(file_path, 1000)
    images = images.transpose(0, 2, 3, 1)

    # Display in figure
    fig = plt.figure(figsize=(9, 40))
    gs = gridspec.GridSpec(10, 2, width_ratios=[1, 5])
    for i in range(10):
        plt.subplot(gs[i, 0])
        plt.axis('off')
        plt.text(0, 0, classes[i], fontdict={'fontsize': 20})
        plt.subplot(gs[i, 1])
        plt.axis('off')
        idx = np.argwhere(labels == i)[:8].flatten()
        imgs = np.column_stack(images[idx])
        plt.imshow(imgs)

    plt.show()

def distorted_cifar_image():
    ''' Create distorted images and display. '''
    file_path = os.path.join(path, bin_file)
    images, labels = read_cifar10(file_path, 1)
    images = images.transpose(0, 2, 3, 1)
    _images = tf.constant(images, shape=[32, 32, 3])

    # distort the images
    changed1 = tf.image.central_crop(_images, central_fraction=0.6)
    changed2 = tf.image.flip_left_right(_images)
    changed3 = tf.image.flip_up_down(_images)
    changed4 = tf.image.adjust_brightness(_images, delta=0.2)
    changed5 = tf.image.adjust_contrast(_images, contrast_factor=1.2)

    # Calculate
    sess = tf.InteractiveSession()
    fig1, fig2, fig3, fig4, fig5 = sess.run([changed1, changed2, changed3, changed4, changed5])
    sess.close()

    # Display
    fig, axes = plt.subplots(2, 3, figsize=(3, 2))
    axes[0,0].axis('off')
    axes[0,0].imshow(images.reshape(32, 32, 3))
    axes[0,1].axis('off')
    axes[0,1].imshow(fig1)
    axes[0,2].axis('off')
    axes[0,2].imshow(fig2)
    axes[1,0].axis('off')
    axes[1,0].imshow(fig3)
    axes[1,1].axis('off')
    axes[1,1].imshow(fig4)
    axes[1,2].axis('off')
    axes[1,2].imshow(fig5)
    plt.show()

distorted_cifar_image()