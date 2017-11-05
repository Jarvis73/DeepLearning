#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
DCAN training procedure

@author: Jarvis ZHANG
@date: 2017/11/5
@framework: Tensorflow
@editor: VS Code
"""

import time
import logging
import tensorflow as tf
from datetime import datetime

import networks
FLAGS = networks.FLAGS

def train():
    if not tf.gfile.Exists(FLAGS.log_dir):
        tf.gfile.MakeDirs(FLAGS.log_dir)

    with tf.Graph().as_default():
        ckpt = tf.train.get_checkpoint_state(FLAGS.log_dir)
        global_step_init = -1
        global_step = tf.contrib.framework.get_or_create_global_step()
        if ckpt and ckpt.model_checkpoint_path:
            # Restores from checkpoint
            global_step_init = int(ckpt.model_checkpoint_path.split('/')[-1].split('-')[-1])

        # Get training patch
        

        class _LoggerHook(tf.train.SessionRunHook):
            """Logs loss and runtime."""

            def begin(self):
                self._step = global_step_init
                self._start_time = time.time()

            def before_run(self, run_context):
                self._step += 1
                return tf.train.SessionRunArgs(loss)  # Asks for loss value.
            
            def after_run(self, run_context, run_values):
                if self._step % FLAGS.log_frequency == 0:
                    current_time = time.time()
                    duration = current_time - self._start_time
                    self._start_time = current_time
                    loss_value = run_values.results
                    examples_per_sec = FLAGS.log_frequency * FLAGS.batch_size / duration
                    sec_per_batch = float(duration / FLAGS.log_frequency)
                    format_str = ('%s: step %d, loss = %.2f (%.1f examples/sec; %.3f '
                                  'sec/batch)')
                    print(format_str % (datetime.now(), self._step, loss_value,
                                        examples_per_sec, sec_per_batch))

        saver = tf.train.Saver()
        max_steps = int(FLAGS.epoches * NUM_EXAMPLES_PER_EPOCH / FLAGS.batch_size)
        with tf.train.MonitoredTrainingSession(
                checkpoint_dir=FLAGS.log_dir,
                hooks=[tf.train.StopAtStepHook(last_step=max_steps),
                       tf.train.NanTensorHook(loss),
                       _LoggerHook()],
                config=tf.ConfigProto(
                    log_device_placement=FLAGS.log_device_placement),
                save_checkpoint_secs=1000, save_summaries_steps=40) as mon_sess:

            ckpt = tf.train.get_checkpoint_state(FLAGS.log_dir)

            if ckpt:
                saver.restore(mon_sess, ckpt.model_checkpoint_path)
                logging.info("Model restored from file: %s" % ckpt.model_checkpoint_path)
            while not mon_sess.should_stop():
                mon_sess.run(train_op)

    
def main(argv=None):
    train()

if __name__ == '__main__':
    tf.app.run()