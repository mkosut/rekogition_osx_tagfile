# rekognition_osx_tagfile
Takes local OSX directory of images and uses Amazon Rekognition to tag them using OSX tags

Simple fun quick hack to play with. Be sure to use the latest Boto, this was built with 1.4.4.

**rek_osx_tag.py**
takes a directory argument and processes all images by sending them to rekognition, getting tags, and applying them using OSX tags.

**rek_osx_tagfile.py**
takes a file argument and processes just that single image with rekognition and sets the tags using OSX tags. Quickly done to use with an OSX Finder Automator workflow

**rekognition_tagPhotos.workflow.zip**
Automator example to run the rek_osx_tagfile.py each time a new file is copied into that folder. As you copy new images into a folder, this will automatically tag them for you.

#TODO:
- [Open, Easy] Consolidate single image processing into main script to support either --directory or --file
- [Done ~~Test if image before sending to rekognition~~
- [Done] ~~Add threading to improve performance dramatically~~


