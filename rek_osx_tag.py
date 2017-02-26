import boto3
import os
import subprocess
from optparse import OptionParser

def gettags(sourceimage):
    """Returns Tags for requested image"""
    taglist = []
    client = boto3.client('rekognition')

    print "Analyzing ", sourceimage
    with open(sourceimage, 'rb') as image:

        response = client.detect_labels(
            Image={'Bytes': image.read()},
            MaxLabels=50,
            MinConfidence=minConfidence
        )

    for tag in response["Labels"]:
        print tag["Confidence"], tag["Name"]
        taglist.append(tag["Name"])

    return taglist

def writexattrs(F, TagList):
    print "Setting following tags for ", F, " ", TagList
    Result = ""
    plistFront = '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><array>'
    plistEnd = '</array></plist>'
    plistTagString = ''
    for Tag in TagList:
        plistTagString = plistTagString + '<string>{}</string>'.format(Tag.replace("'","-"))
    TagText = plistFront + plistTagString + plistEnd

    OptionalTag = "com.apple.metadata:"
    XattrList = ["kMDItemFinderComment","_kMDItemUserTags","kMDItemOMUserTags"]
    for Field in XattrList:
        XattrCommand = 'xattr -w {0} \'{1}\' "{2}"'.format(OptionalTag + Field,TagText.encode("utf8"),F)
        ProcString = subprocess.check_output(XattrCommand, stderr=subprocess.STDOUT,shell=True)
        Result += ProcString
    return Result

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-d", "--directory",
        dest="source_directory",
        default=".",
        help="Specify directory of photos to tag e.g. /Media/Photos/")
    (options, args) = parser.parse_args()
    sourceDirectory = options.source_directory
    minConfidence = 50

    for fn in os.listdir(sourceDirectory):
        imagename = sourceDirectory + "/" + fn
        imagesize = os.path.getsize(imagename) 
        print imagename
        if imagesize > 5242880:
            print "Skipping %s: filesize exceeds maximum of 5242880 bytes" % imagename
        elif os.path.isfile(imagename):
            tags = gettags(fn)
            writexattrs(imagename, tags)
        else:
            print imagename + " is not a file"
