#!/usr/bin/python
# v1.0
#    work around for gerrit project path does not match with manifest
#    please import this script and use function gerrit_path_convert_to_manifest_path(gerrit_path)
#    Author: yfshi@marvell.com

import subprocess
import getopt
import pickle
import re
import sys
import os

#Global dict for gerrit project path and manifest project path
PROJECT_DICT = dict()

#Please add new project path here if there is any
def generate_project_dict():
    global PROJECT_DICT
    PROJECT_DICT["ose/linux/mrvl-3.4"] = "vendor/marvell/ose/mrvl-3.4"
    PROJECT_DICT["ose/linux/ttc_telephony"] = "vendor/marvell/ose/ttc_telephony"
    PROJECT_DICT["ose/linux/uboot"] = "vendor/marvell/ose/uboot"
    PROJECT_DICT["ose/linux/wtptp_pxa910"] = "vendor/marvell/ose/wtptp_pxa910"
    PROJECT_DICT["pie/camera-engine-marvell"] = "vendor/marvell/pie/camera-engine-marvell"

def gerrit_path_convert_to_manifest_path(gerrit_path):
    global PROJECT_DICT
    generate_project_dict()
    return PROJECT_DICT[gerrit_path]


#User help
def usage():
    print "\tgerrit_project_path_and_manifest_path_conversion [-p] patch gerrit project path"
    print "\t      [-m] patch manifest project path"
    print "\t      [-h] help"

def main(argv):
    gerrit_path = ""
    manifest_path = ""
    try:
        opts, args = getopt.getopt(argv,"p:m",["showonly","username","remote"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-p"):
            gerrit_path = arg
        elif opt in ("-m"):
            manifest_path = arg
    if (gerrit_path == "") and (manifest_path == ""):
        usage()
        sys.exit(2)
    else:
        print gerrit_path_convert_to_manifest_path(gerrit_path)

if __name__ == "__main__":
    main(sys.argv[1:])
