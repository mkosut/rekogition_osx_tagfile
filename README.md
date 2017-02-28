# rekognition_osx_tagfile
Takes local OSX directory of images and uses Amazon Rekognition to tag them using OSX tags

Simple fun quick hack to play with. Be sure to use the latest Boto, this was built with 1.4.4. Requires ~/.aws/credentials file.

**rek_osx_tag.py**
takes either a directory (-d) or single file (-f) argument and processes images by sending them to rekognition, getting tags, and applying them using OSX tags.

**rekognition_tagPhotos.workflow.zip**
Automator example to run the 'rek_osx_tag.py -f [imagename]' each time a new file is copied into that folder. As you copy new images into a folder, this will automatically tag them for you.

#TODO:
- [Done] ~~Consolidate single image processing into main script to support either --directory or --file~~
- [Done] ~~Test if image before sending to rekognition~~
- [Done] ~~Add threading to improve performance dramatically~~


