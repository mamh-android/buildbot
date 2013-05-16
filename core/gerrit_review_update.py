#!/usr/bin/python
# v1.0
#    create a gitaccess file for external git release
#    The tag_name should be followed naming conventions doc
#    input: branchname, tag_name. output: *.gitaccess included the description(download url)
#    Author: yfshi@marvell.com

import subprocess
import getopt
import pickle
import re
import sys
import os

#Gerrit admin user
r_user = "buildfarm"

#release git server
gerrit_server = "shgit.marvell.com"

#generate and return gerrit review args by patch_list, manifest_xml, results & dir_path
#args[i] = "ssh -p 29418 " + r_user + "@" + gerrit_server + " gerrit review --code-review +1 --verified +1 -m " + generate_message(patch_list,manifest_xml,results,dir_path) + " " + s_patch_list[i]
def generate_args(patch_list,manifest_xml,results,dir_path):
    global r_user
    global gerrit_server
    s_patch_list = patch_list.split(',')
    args = [[]] * len(s_patch_list)    
    if (results == "success"):
        for i in range(len(args)):
            args[i] = "ssh -p 29418 " + r_user + "@" + gerrit_server + " gerrit review --code-review +1 -m " + generate_message(patch_list,manifest_xml,results,dir_path) + " " + s_patch_list[i]
    else:
        for i in range(len(args)):
            args[i] = "ssh -p 29418 " + r_user + "@" + gerrit_server + " gerrit review --code-review -1 -m " + generate_message(patch_list,manifest_xml,results,dir_path) + " " + s_patch_list[i]

    return args

#generate and return gerrit review message by patch_list, manifest_xml, results & dir_path
def generate_message(patch_list,manifest_xml,results,dir_path):
    message = ""
    if (results == "success"):
        message = "'\"" + "**Success** Manifest: [" + manifest_xml + "] PatchSets: [" +  patch_list + "] Package Link: [" + dir_path + "]\"'"
    else:
        message = "'\"" + "**Failure** Manifest: [" + manifest_xml + "] PatchSets: [" +  patch_list + "]\"'"
    return message

#Run args[i] by shell
def run_args(args):
    for i in range(len(args)):
        #print args[i]
        subprocess.check_call(args[i], shell=True)

#User help
def usage():
    print "\tgerrit_review_update [-p] patch_list"
    print "\t      [-m] manifest.xml"
    print "\t      [-r] result <success|failure>"
    print "\t      [-d] image path"
    print "\t      [-h] help"

def main(argv):
    patch_list = ""
    manifest_xml = ""
    results = ""
    dir_path = ""
    try:
        opts, args = getopt.getopt(argv,"p:m:r:d:h",["showonly","username","remote"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-p"):
            patch_list = arg
        elif opt in ("-m"):
            manifest_xml = arg
        elif opt in ("-r"):
            results = arg
        elif opt in ("-d"):
            dir_path = arg
    if (patch_list == "") or (manifest_xml == "") or (results == ""):
        usage()
        sys.exit(2)
    else:
        g_args = generate_args(patch_list,manifest_xml,results,dir_path)
        run_args(g_args)

if __name__ == "__main__":
    main(sys.argv[1:])
