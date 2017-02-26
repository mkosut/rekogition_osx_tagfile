"""Loops through directory and gathers Rekogition tags for each image."""
import boto3
import os
import subprocess
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", 
    dest="source_image",
    help="Specify directory of photos to tag e.g. /Media/Photos/")

(options, args) = parser.parse_args()

sourceimage = options.source_image
minConfidence = 50

if __name__ == '__main__':

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

    def writexattrs(F,TagList):
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

    tags = gettags(sourceimage)
    writexattrs(sourceimage, tags)
