#!/usr/bin/python
# v1.0
# publish file to image server
# Need environment variables:
#       COSMO_WORKING_DIR:      working directory
#       IMAGE_SERVER:           image file server 

COSMO_OUT_DIR="/tmp/cosmo/out/"
IMAGE_SERVER="/tmp/image_server/"

import shutil
import os
import sys
from datetime import date

#copy bin and build files from {src} to out, {src} dict will be import from FILES_DICT in cosmo src code
def copy_dict():
    sys.path.append(os.getcwd())
    from COSMO_FILES_PUBLISH_DICT import FILES_DICT
    for i in FILES_DICT:
        print i
        if os.path.isdir(i):
            p = "copy directory: " + i + "-->" + FILES_DICT[i]
            print p
            path = os.path.dirname(FILES_DICT[i])
            if not os.path.isdir(path):
                os.makedirs(path)
            shutil.copytree(i,FILES_DICT[i])
        elif os.path.isfile(i):
            p = "copy file: " + i + "-->" + FILES_DICT[i]
            print p
            path = os.path.dirname(FILES_DICT[i])
            if not os.path.isdir(path):
                os.makedirs(path)
            shutil.copy2(i,FILES_DICT[i])
        else:
            print "publishing failed, file " + i + " dose not existed"
            exit(2)

def copy_file(src, dst):
    print src
    if os.path.isdir(src):
        p = "copy directory: " + src + "-->" + dst
        print p
        path = os.path.dirname(dst)
        if not os.path.isdir(path):
            os.makedirs(path)
        shutil.copytree(src, dst)
    if os.path.isfile(dst):
        p = "copy file: " + src + "-->" + dst
        print p
        path = os.path.dirname(dst)
        if not os.path.isdir(path):
            os.makedirs(path)
        shutil.copy(src, dst)
    else:
        print "publishing failed, file " + src + " dose not existed"
        exit(2)

#create a folder according to git branch name and time.today
def check_publish_folder(IMAGE_SERVER):
    branch = os.popen("git branch").read().split()[1]
    today = date.today()
    folder = str(today) + "_" + branch
    folder_server = IMAGE_SERVER + folder
    f = folder_server
    if not os.path.isdir(f):
        #os.mkdir(f)
        return f
    else:
        i=1
        while os.path.isdir(folder_server):
            f = folder_server + "_" + str(i)
            if not os.path.isdir(f):
                #os.mkdir(f)
                return f
                break
            else:
                i=i+1

#Publish all the files to out
def publish_file(src, dst):
    copy_dict()
    build = check_publish_folder(dst)
    path = os.path.dirname(build)
    if not os.path.isdir(path):
        os.makedirs(path)
    shutil.copytree(src, build)
    return build


#publish_file()
#run publishing
#publish_file(create_publish_folder(IMAGE_SERVER))
#publish_file(COSMO_OUT_DIR, IMAGE_SERVER)
