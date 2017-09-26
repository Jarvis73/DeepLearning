#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
UNet implementation

@author: Jarvis ZHANG
@date: 2017/9/3
@framework: Tensorflow
@editor: VS Code
"""

import re
import math
import prepare_data
import numpy as np
import tensorflow as tf

FLAGS = tf.app.flags.FLAGS

# Basic model parameters.
tf.app.flags.DEFINE_integer('batch_size', 1,
                            """Number of images to process in a batch.""")
tf.app.flags.DEFINE_string('data_dir', prepare_data.WQU_ROOT_DIR,
                           """Path to the WQU data directory.""")
tf.app.flags.DEFINE_boolean('use_fp16', False,
                            """Train the model using float point 16.""")
tf.app.flags.DEFINE_integer('num_layers', 6,
                            """Number of layers in model.""")
tf.app.flags.DEFINE_integer('num_classes', 2,
                            """Number of output classes.""")
tf.app.flags.DEFINE_integer('feat_root', 32,
                            """Feature root.""")
tf.app.flags.DEFINE_integer('deconv_root', 8,
                            """Transposed convolution upscaling factor.""")



# Global constants describing the Warwick QU data set.
IMAGE_WIDTH = prepare_data.IMAGE_WIDTH
IMAGE_HEIGHT = prepare_data.IMAGE_HEIGHT
NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = prepare_data.NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN
NUM_EXAMPLES_PER_EPOCH_FOR_TEST = prepare_data.NUM_EXAMPLES_PER_EPOCH_FOR_TEST

# Constants describing the training process.
MOVING_AVERAGE_DECAY = 0.9995  # The decay to use for the moving average.
NUM_EPOCHS_PER_DECAY = 72.0  # Epochs after which learning rate decays.
LEARNING_RATE_DECAY_FACTOR = 0.1  # Learning rate decay factor.
INITIAL_LEARNING_RATE = 0.001  # Initial learning rate.
DROPOUT_RATE = 0.5  # Probability for dropout layers.
C_CLASS_PROP = .1638  # Contours proportion of pixels in class 1.
S_CLASS_PROP = .2249  # Segments proportion of pixels in class 1.

TOWER_NAME = 'tower'

def _activation_summary(x):
    """Helper to create summaries for activations.
    Creates a summary that provides a histogram of activations.
    Creates a summary that measures the sparsity of activations.

    Args:
        x: Tensor
    """
    # Remove 'tower_[0-9]/' from the name in case this is a multi-GPU training
    # session. This helps the clarity of presentation on tensorboard.
    tensor_name = re.sub('%s_[0-9]*/' % TOWER_NAME, '', x.op.name)
    tf.summary.histogram(tensor_name + '/activations', x)
    tf.summary.scalar(tensor_name + '/sparsity', tf.nn.zero_fraction(x))


def _variable_on_cpu(name, shape, initializer):
    """Helper to create a Variable stored on CPU memory.
    Args:
        name: name of the variable
        shape: list of ints
        initializer: initializer for Variable
    Returns:
        Variable Tensor
    """
    dtype = tf.float16 if FLAGS.use_fp16 else tf.float32
    var = tf.get_variable(name, shape, initializer=initializer, dtype=dtype)
    return var


def _variable_with_weight_decay(name, shape, stddev, wd):
    """Helper to create an initialized Variable with weight decay.
    Note that the Variable is initialized with a truncated normal distribution.
    A weight decay is added only if one is specified.
    Args:
        name: name of the variable
        shape: list of ints
        stddev: standard deviation of a truncated Gaussian
        wd: add L2Loss weight decay multiplied by this float. If None, weight
            decay is not added for this Variable.
    Returns:
        Variable Tensor
    """
    dtype = tf.float16 if FLAGS.use_fp16 else tf.float32
    var = _variable_on_cpu(
        name,
        shape,
        tf.truncated_normal_initializer(stddev=stddev, dtype=dtype))
    if wd is not None and not tf.get_variable_scope().reuse:
        weight_decay = tf.multiply(tf.nn.l2_loss(var), wd, name='weight_loss')
        tf.add_to_collection('losses', weight_decay)
    return var


def distorted_inputs():
    """Construct distorted input for BBBC006 training using the Reader ops.
    Returns:
        images: Images. 4D tensor of [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, 3] size.
        labels: Labels. 4D tensor of [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, 2] size.
    Raises:
        ValueError: If no data_dir
    """
    if not FLAGS.data_dir:
        raise ValueError('Please supply a data_dir')
    images, labels = prepare_data.distorted_inputs(batch_size=FLAGS.batch_size)
    if FLAGS.use_fp16:
        images = tf.cast(images, tf.float16)
        labels = tf.cast(labels, tf.float16)
    return images, labels


def inputs(eval_data):
    """Construct input for BBBC006 evaluation using the Reader ops.
    Args:
        eval_data: bool, indicating if one should use the train or eval data set.
    Returns:
        images: Images. 4D tensor of [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, 3] size.
        labels: Labels. 4D tensor of [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, 2] size.

    Raises:
        ValueError: If no data_dir
    """
    if not FLAGS.data_dir:
        raise ValueError('Please supply a data_dir')
    images, labels = prepare_data.inputs(eval_data=eval_data,
                                          batch_size=FLAGS.batch_size)
    if FLAGS.use_fp16:
        images = tf.cast(images, tf.float16)
        labels = tf.cast(labels, tf.float16)
    return images, labels


def get_deconv_filter(shape):
    """Return deconvolution weight tensor w/bilinear interpolation.
    Args:
        shape: 4D list of weight tensor shape.
    Returns:
        Tensor containing weight variable.

    Source:
        https://github.com/MarvinTeichmann/tensorflow-fcn/blob/master/fcn16_vgg.py#L245
    """
    width = shape[0]
    height = shape[0]
    f = math.ceil(width / 2.0)
    c = (2.0 * f - 1 - f % 2) / (2.0 * f)

    bilinear = np.zeros([shape[0], shape[1]])
    for x in range(width):
        for y in range(height):
            bilinear[x, y] = (1 - abs(x / f - c)) * (1 - abs(y / f - c))

    weights = np.zeros(shape)
    for i in range(shape[2]):
        weights[:, :, i, i] = bilinear

    init = tf.constant_initializer(value=weights, dtype=tf.float32)
    return tf.get_variable(name='up_filter', initializer=init, shape=weights.shape)


def _deconv_layer(in_layer, w, b, dc, ds, scope):
    """Return deconvolution layer tensor.
    Args:
        in_layer: Input tensor layer.
        w: Weight tensor.
        b: Bias tensor.
        dc: Deconvolution constant.
        ds: Deconvolution layer output shape in list format.
        scope: Enclosing variable scope.
    Returns:
        Tensor for deconvolution layer.
    """
    deconv = tf.nn.conv2d_transpose(in_layer, w, ds, strides=[1, dc, dc, 1],
                                    padding='SAME')
    deconv = tf.nn.bias_add(deconv, bias=b, name=scope.name)
    deconv = tf.nn.relu(deconv)
    _activation_summary(deconv)
    return deconv


def inference(images, train=True):
    """Build the model.
    Args:
        images: Images returned from distorted_inputs() or inputs().
    Returns:
        c_fuse: List of fused contours 4D tensors of [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, 2] size.
        s_fuse: List of fused segments 4D tensors of [batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, 2] size.
    """
    # We instantiate all variables using tf.get_variable() instead of
    # tf.Variable() in order to share variables across multiple GPU training runs.
    feat_out = FLAGS.feat_root
    in_layer = images

    # Deconvolution constant: kernel size = 2 * dc, stride = dc
    # Deconvolution output shape
    dc = FLAGS.deconv_root
    ds = [FLAGS.batch_size, IMAGE_HEIGHT, IMAGE_WIDTH, FLAGS.num_classes]

    # Up-sampled layers 4-6 output maps for contours and segments, respectively
    c_outputs = []
    s_outputs = []

    for layer in range(FLAGS.num_layers):
        # CONVOLUTION
        with tf.variable_scope('conv{}'.format(layer + 1)) as scope:
            # Double the number of feat_out for all but convolution layer 4
            feat_out *= 2 if layer != 4 else 1
            conv = tf.layers.conv2d(in_layer, feat_out, (3, 3), padding='same',
                                    activation=tf.nn.relu, name=scope.name)

            if train and layer > 3:  # During training, add dropout to layers 5 and 6
                conv = tf.nn.dropout(conv, keep_prob=DROPOUT_RATE)
            _activation_summary(conv)

        # POOLING
        # First and convolution layers has no pooling afterwards
        if layer <= 2:
            pool = tf.layers.max_pooling2d(conv, 2, 2, padding='same')

            _activation_summary(pool)
            in_layer = pool
        else:
            in_layer = conv

        # Transposed convolution and output mapping for segments and contours
        if layer > 2:  # Only applies to layers 3-5
            for i in range(2):
                # TRANSPOSED CONVOLUTION
                with tf.variable_scope('deconv{0}_{1}'.format(layer + 1, i)) as scope:
                    feat_in = in_layer.get_shape().as_list()[-1]
                    shape = [dc * 2, dc * 2, FLAGS.num_classes, feat_in]
                    w = get_deconv_filter(shape)
                    b = _variable_on_cpu('biases', [FLAGS.num_classes],
                                         tf.constant_initializer(0.1))

                    deconv = _deconv_layer(in_layer, w, b, dc, ds, scope)

                with tf.variable_scope('output{0}_{1}'.format(layer + 1, i)) as scope:
                    output = tf.layers.conv2d(deconv, FLAGS.num_classes, (1, 1),
                                              padding='same', activation=tf.nn.relu,
                                              name=scope.name)
                    if i == 0:
                        c_outputs.append(output)
                    else:
                        s_outputs.append(output)
    c_fuse = tf.add_n(c_outputs)
    s_fuse = tf.add_n(s_outputs)

    return c_fuse, s_fuse


def _add_cross_entropy(labels, logits, pref):
    """Compute average cross entropy and add to loss collection.
    Args:
        labels: Single dimension labels from distorted_inputs() or inputs().
        logits: Output map from inference().
        pref: Either 'c' or 's', for contours or segments, respectively.
    """
    with tf.variable_scope('{}_cross_entropy'.format(pref)) as scope:
        class_prop = C_CLASS_PROP if pref == 'c' else S_CLASS_PROP
        weight_per_label = tf.scalar_mul(class_prop, tf.cast(tf.equal(labels, 0),
                                                             tf.float32)) + \
                           tf.scalar_mul(1.0 - class_prop, tf.cast(tf.equal(labels, 1),
                                                                   tf.float32))
        cross_entropy = tf.losses.sparse_softmax_cross_entropy(
            labels=tf.squeeze(labels, squeeze_dims=[3]), logits=logits)
        cross_entropy_weighted = tf.multiply(weight_per_label, cross_entropy)
        cross_entropy_mean = tf.reduce_mean(cross_entropy_weighted, name=scope.name)
        tf.add_to_collection('losses', cross_entropy_mean)


def loss(c_fuse, s_fuse, labels):
    """Add L2Loss to all the trainable variables.
    Add summary for "Loss" and "Loss/avg".
    Args:
        c_fuse: Contours output map from inference().
        s_fuse: Segments output map from inference().
        labels: Labels from distorted_inputs or inputs().

    Returns:
      Loss tensor of type float.
    """
    # Calculate the average cross entropy loss across the batch.

    # Split the labels tensor into contours and segments image tensors
    # Each has shape [FLAGS.batch_size, 696, 520, 1]
    contours_labels, segments_labels = tf.split(labels, 2, 3)

    _add_cross_entropy(contours_labels, c_fuse, 'c')
    _add_cross_entropy(segments_labels, s_fuse, 's')

    return tf.add_n(tf.get_collection('losses'), name='total_loss')


def _add_loss_summaries(total_loss):
    """Add summaries for losses in BBBC006 model.
    Generates moving average for all losses and associated summaries for
    visualizing the performance of the network.

    Args:
        total_loss: Total loss from loss().
    Returns:
        loss_averages_op: op for generating moving averages of losses.
    """
    # Compute the moving average of all individual losses and the total loss.
    loss_averages = tf.train.ExponentialMovingAverage(0.9, name='avg')
    losses = tf.get_collection('losses')
    loss_averages_op = loss_averages.apply(losses + [total_loss])

    # Attach a scalar summary to all individual losses and the total loss; do the
    # same for the averaged version of the losses.
    for l in losses + [total_loss]:
        # Name each loss as '(raw)' and name the moving average version of the loss
        # as the original loss name.
        tf.summary.scalar(l.op.name + '_raw', l)
        tf.summary.scalar(l.op.name, loss_averages.average(l))

    return loss_averages_op


def train(total_loss, global_step):
    """Train BBBC006 model.
    Create an optimizer and apply to all trainable variables. Add moving
    average for all trainable variables.

    Args:
        total_loss: Total loss from loss().
        global_step: Integer Variable counting the number of training steps
        processed.
    Returns:
        train_op: op for training.
    """
    # Variables that affect learning rate.
    num_batches_per_epoch = NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN / FLAGS.batch_size
    decay_steps = int(num_batches_per_epoch * NUM_EPOCHS_PER_DECAY)

    # Decay the learning rate exponentially based on the number of steps.
    lr = tf.train.exponential_decay(INITIAL_LEARNING_RATE,
                                    global_step,
                                    decay_steps,
                                    LEARNING_RATE_DECAY_FACTOR,
                                    staircase=True)
    tf.summary.scalar('learning_rate', lr)

    # Generate moving averages of all losses and associated summaries.
    loss_averages_op = _add_loss_summaries(total_loss)

    # Compute gradients.
    with tf.control_dependencies([loss_averages_op]):
        opt = tf.train.MomentumOptimizer(learning_rate=lr, momentum=0.2)
        grads = opt.compute_gradients(total_loss, var_list=tf.trainable_variables())

    # Apply gradients.
    apply_gradient_op = opt.apply_gradients(grads, global_step=global_step)

    # Add histograms for trainable variables.
    for var in tf.trainable_variables():
        tf.summary.histogram(var.op.name, var)

    # Add histograms for gradients.
    for grad, var in grads:
        if grad is not None:
            tf.summary.histogram(var.op.name + '/gradients', grad)

    # Track the moving averages of all trainable variables.
    variable_averages = tf.train.ExponentialMovingAverage(
        MOVING_AVERAGE_DECAY, global_step)
    variables_averages_op = variable_averages.apply(tf.trainable_variables())

    with tf.control_dependencies([apply_gradient_op, variables_averages_op]):
        train_op = tf.no_op(name='train')

    return train_op


def get_show_preds(c_fuse, s_fuse):
    """Compute and view logits.
    Args:
        c_fuse: Contours fuse layer.
        s_fuse: Segments fuse layer.
    Returns:
        c_logits: Softmax applied to contours fuse layer.
        s_logits: Softmax applied to segments fuse layer.
    """
    # Index 1 of fuse layers correspond to foreground, so discard index 0.
    _, c_logits = tf.split(tf.cast(tf.nn.softmax(c_fuse), tf.float32), 2, 3)
    _, s_logits = tf.split(tf.cast(tf.nn.softmax(s_fuse), tf.float32), 2, 3)

    tf.summary.image('c_logits', c_logits)
    tf.summary.image('s_logits', s_logits)
    return c_logits, s_logits


def get_show_labels(labels):
    """Get and view labels.
    Args:
        labels: Labels from distorted_inputs or inputs().
    Returns:
        c_labels: Contours labels.
        s_labels: Segments labels.
    """
    c_labels, s_labels = tf.split(labels, 2, 3)
    c_labels = tf.cast(c_labels, tf.float32)
    s_labels = tf.cast(s_labels, tf.float32)

    tf.summary.image('c_labels', c_labels)
    tf.summary.image('s_labels', s_labels)
    return c_labels, s_labels


def get_dice_coef(logits, labels):
    """Compute dice coefficient.
    Args:
        logits: Softmax probability applied to fuse layers.
        labels: Correct annotations (0 or 1).
    Returns:
        Mean dice coefficient over full tensor.

    Source:
        https://github.com/zsdonghao/tensorlayer/blob/master/tensorlayer/cost.py#L125
    """
    smooth = 1e-5
    inter = tf.reduce_sum(tf.multiply(logits, labels))
    l = tf.reduce_sum(logits)
    r = tf.reduce_sum(labels)
    return tf.reduce_mean((2.0 * inter + smooth) / (l + r + smooth))


def dice_op(c_fuse, s_fuse, labels):
    """Compute mean dice coefficient for both contours and segments outputs.
    Args:
        c_fuse: Contours output map from inference().
        s_fuse: Segments output map from inference().
        labels: Labels from distorted_inputs or inputs().
    Returns:
        c_dice: Float representing average dice coefficient for contours.
        s_dice: Float representing average dice coefficient for segments.
    """
    c_logits, s_logits = get_show_preds(c_fuse, s_fuse)
    c_labels, s_labels = get_show_labels(labels)

    c_dice = get_dice_coef(c_logits, c_labels)
    s_dice = get_dice_coef(s_logits, s_labels)

    return c_dice, s_dice


