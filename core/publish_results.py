#!/usr/bin/python
# v1.0
# publish file to image server

import os
import sys
import getopt
import shutil

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
            p = "publishing failed, file " + i + " dose not existed"
            print p
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
        p = "publishing failed, file " + src + " dose not existed"
        print p
        exit(2)

#create a folder according to git last rev
def check_publish_folder(IMAGE_SERVER, rev):
    folder_server = IMAGE_SERVER + str(rev)
    if not os.path.isdir(folder_server):
        return folder_server
    else:
        print "check publish folder %s failed" % rev
        exit(2)

#Publish all the files to out
def publish_file(src, dst, rev):
    copy_dict()
    build = check_publish_folder(dst, rev)
    #build = dst + str(rev)
    path = os.path.dirname(build)
    if not os.path.isdir(path):
        os.makedirs(path)
    shutil.copytree(src, build)
    print "Publishing packages to %s" % build
    return build

#User help
def usage():
    print "\tpublish"
    print "\t      [-s] source"
    print "\t      [-d] dest"
    print "\t      [-r] rev"
    print "\t      [-h] help"

def main(argv):
    source = ""
    dest = ""
    rev = ""
    try:
        opts, args = getopt.getopt(argv,"s:d:r:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-s"):
            source = arg
        elif opt in ("-d"):
            dest = arg
        elif opt in ("-r"):
            rev = arg
    if not source or not rev:
        usage()
        sys.exit(2)

    publish_file(source, dest, rev)

if __name__ == "__main__":
    main(sys.argv[1:])
