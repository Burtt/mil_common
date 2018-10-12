"""
Usage:
  # From tensorflow/models/
  # Create train data:
  python generate_tfrecord.py --csv_input=train/train_labels.csv --image_dir=train --output_path=train.record

  # Create test data:
  python generate_tfrecord.py --csv_input=test/test_labels.csv  --image_dir=test --output_path=test.record
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import io
import sys
import pandas as pd
import tensorflow as tf

from PIL import Image
from object_detection.utils import dataset_util
from collections import namedtuple, OrderedDict

flags = tf.app.flags
# flags.DEFINE_string('csv_input', '', 'Path to the CSV input')
# flags.DEFINE_string('image_dir', '', 'Path to the image directory')
# flags.DEFINE_string('output_path', '', 'Path to output TFRecord')
# flags.DEFINE_string('labelmap_path', '', 'Path to labelmap.pbtxt')
FLAGS = flags.FLAGS
# dictionary = {}

# TO-DO replace this with label map


def create_dict():
    global dictionary
    with open(('../data/' + FLAGS.labelmap_path)) as f:
        txt = f.read()
    labels = []
    ids = []
    # print(txt)
    # txt = txt[2, :]
    full_split = [s.strip().split(': ') for s in txt.splitlines()]
    # print(full_split)
    full_split = full_split[1:]
    # try:
    for i in full_split:
        if len(i) < 2:
            continue
        if isinstance(i[1], str):
            if i[1].isdigit():
                # print(i[1])
                ids.append(int(i[1]))
            else:
                # print(i[1].strip("'"))
                labels.append(i[1].strip("'"))
        else:
            print(
                "Error, incorrect key located in labelmap. Should be only id or name. Instead found: ", i[1])
    # except:
        # print("It errored! Whomp whomp. ", i)
    dictionary = dict(zip(labels, ids))
    # print(dictionary)


def class_text_to_int(row_label):
    # print(dictionary)
    # print(row_label)
    # print(dictionary.get(row_label))
    return dictionary.get(row_label)


def split(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]


def create_tf_example(group, path):
    with tf.gfile.GFile(os.path.join(path, '{}'.format(group.filename)), 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)
    width, height = image.size

    filename = group.filename.encode('utf8')
    image_format = b'jpg'
    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    for index, row in group.object.iterrows():
        xmins.append(row['xmin'] / width)
        xmaxs.append(row['xmax'] / width)
        ymins.append(row['ymin'] / height)
        ymaxs.append(row['ymax'] / height)
        classes_text.append(row['class'].encode('utf8'))
        new_class = class_text_to_int(row['class'])
        # print("width: ", width)
        # print("height: ", height)
        if new_class is None:
            continue
        classes.append(new_class)
    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))
    return tf_example

