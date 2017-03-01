"""Loops through directory and gathers Rekogition tags for each image."""
from __future__ import print_function
import io
import os
from optparse import OptionParser
import subprocess
import mimetypes
import concurrent.futures
import sys
import time
import boto3
from PIL import Image

if sys.version_info[0] < 3:
    from itertools import izip_longest as zip_longest
else:
    from itertools import zip_longest

IMG_RESIZE = (2000, 2000)


def get_tags_old(source_image, client, min_confidence):
    with open(source_image, 'rb') as image:
        response = client.detect_labels(
            Image={'Bytes': image.read()},
            MaxLabels=50,
            MinConfidence=min_confidence
        )
    return [tag["Name"] for tag in response["Labels"]]


def get_tags(source_image, client, min_confidence):
    """Returns Tags for requested image"""
    with open(source_image, 'rb') as image:
        img = Image.open(image)
        if img.size[0] > IMG_RESIZE[0] and img.size[1] > IMG_RESIZE[1]:
            img.thumbnail(IMG_RESIZE, Image.ANTIALIAS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", optimize=True, quality=85)
        buf.seek(0)
        response = client.detect_labels(
            Image={'Bytes': buf.read()},
            MaxLabels=50,
            MinConfidence=min_confidence
        )
    return [tag["Name"] for tag in response["Labels"]]


def writexattrs(fn, tags):
    print("Setting following tags for ", fn, " ", tags)
    plist = """\
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
        <array>{}</array>
    </plist>"""
    tag_string = ''.join(['<string>{}</string>'.format(tag.replace("'", "-")) for tag in tags])
    plist = plist.format(tag_string)
    optional_tag = "com.apple.metadata:"
    attr_list = ["kMDItemFinderComment", "_kMDItemUserTags", "kMDItemOMUserTags"]
    for field in attr_list:
        cmd = 'xattr -w {} \'{}\' "{}"'.format(optional_tag + field, plist, fn)
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)


def images_in_dir(source_directory, recursive):
    for root, dirs, files in os.walk(source_directory):
        for fn in files:
            pth = os.path.join(root, fn)
            ftype = mimetypes.guess_type(pth)[0]
            if not ftype or "image" not in ftype:
                print("Skipping {} is not a known type".format(pth))
                continue
            yield pth

        if not recursive:
            break


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def put_tags(images, min_confidence):
    client = boto3.client('rekognition')
    for image in images:
        if image:
            try:
                writexattrs(image, get_tags(image, client, min_confidence))
            except Exception as ex:
                print(ex, image)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-d", "--directory",
        dest="source_directory",
        default=".",
        help="Specify directory of photos to tag e.g. /Media/Photos/")
    parser.add_option(
        "-f", "--file",
        dest="source_file",
        help="Specify single file to tag e.g. /Media/Photos/myimage.jpg") 
    parser.add_option(
        "-c", "--confidence",
        dest="confidence",
        default=50,
        help="Specify the minimum confidence for a label to be applied")
    parser.add_option("-r", "--recursive",
        dest="recursive",
        default=False,
        action="store_true",
        help="Perform recursive search")
    (options, args) = parser.parse_args()

    start = time.time()
    if options.source_file:
        images = [options.source_file]
    else:
        images = list(images_in_dir(options.source_directory, options.recursive))

    # Use as many processes as we have CPU
    executor = concurrent.futures.ProcessPoolExecutor()
    # Use groups of 20 for each process
    futures = [executor.submit(put_tags, group, options.confidence) for group in grouper(images, 20)]
    results = concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
    for result in results.done:
        ex = result.exception()
        if ex:
            print(ex)
    end = time.time()
    print("Processed {} images in {:.2f} seconds".format(len(images), end - start))
