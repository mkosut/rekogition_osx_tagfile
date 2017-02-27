"""Loops through directory and gathers Rekogition tags for each image."""
from __future__ import print_function
import boto3
import os
import subprocess
from optparse import OptionParser
import mimetypes
import concurrent.futures
import sys
if sys.version_info[0] < 3:
    from itertools import izip_longest as zip_longest
else:
    from itertools import zip_longest


def gettags(source_image, client):
    """Returns Tags for requested image"""
    with open(source_image, 'rb') as image:
        response = client.detect_labels(
            Image={'Bytes': image.read()},
            MaxLabels=50,
            MinConfidence=50
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


def images_in_dir(source_directory):
    for fn in os.listdir(os.path.expanduser(source_directory)):
        pth = os.path.join(source_directory, fn)
        if not os.path.isfile(pth):
            continue
        ftype = mimetypes.guess_type(pth)[0]
        imgsize = os.path.getsize(pth)
        if ftype not in ["image/png", "image/jpeg"]:
            print("Skipping {} is not a known type".format(pth))
            continue
        if imgsize >= 5242880:
            print("Skipping {} is over 5242880 bytes".format(pth))
            continue
        yield pth


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def put_tags(images):
    client = boto3.client('rekognition')
    for image in images:
        if image:
            try:
                writexattrs(image, gettags(image, client))
            except Exception as ex:
                print(ex, image)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-d", "--directory",
        dest="source_directory",
        default=".",
        help="Specify directory of photos to tag e.g. /Media/Photos/")
    (options, args) = parser.parse_args()
    images = images_in_dir(options.source_directory)
    # Use as many processes as we have CPU
    executor = concurrent.futures.ProcessPoolExecutor()
    # Use groups of 20 for each process
    futures = [executor.submit(put_tags, group) for group in grouper(images, 20)]
    concurrent.futures.wait(futures)
