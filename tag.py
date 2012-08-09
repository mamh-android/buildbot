#!/usr/bin/python
# v1.0
#   Mark tag on repo repository

import getopt
import re
import pickle
import subprocess
import sys

def tag_common(tag_name, input_file):
    fp = open(input_file, "r")  # read mode
    dic = pickle.load(fp)
    fp.close()

    for name, path in dic.items():
        cd_args = "cd " + path + " ; "
        args = cd_args + " git tag " + tag_name
        subprocess.check_call(args, shell=True)

def update_xml(src_file, pattern, repl):
    try:
        fp_src = open(src_file, 'r')
        contents = fp_src.readlines()
        fp_src.close()
    except IOError:
        print "failed to open manifest file with read mode"
        sys.exit(2)
    try:
        # replace revision
        fp_dst = open(src_file, 'w')
        prep = re.compile(pattern)
        for line in contents:
            data = prep.sub(repl, line)
            fp_dst.write(data)
        fp_dst.close()
    except IOError:
        print "failed to open manifest file with write mode"
        sys.exit(2)
        sys.exit(2)

def new_commit(dest_server, tag_name):
    src_file = ".repo/manifests/default.xml"
    # remove revision that is not default revision
    pattern = 'revision[ ]*=[ ]*\"[^\"]*\"[ ]*/>'
    repl = "/>"
    update_xml(src_file, pattern, repl)
    # replace default revision
    pattern = 'default revision[ ]*=[ ]*\"[^\"]*\"[ ]*'
    repl = "default revision=\"" + "refs/tags/" + tag_name + "\""
    update_xml(src_file, pattern, repl)
    # replace "remote name"
    pattern = 'remote[ ]*name[ ]*=[ ]*\"[^\"]*\"'
    repl = "remote  name=\"" + dest_server + "\""
    update_xml(src_file, pattern, repl)
    # replace "remote"
    pattern = 'remote[ ]*=[ ]*\"[^\"]*\"'
    repl = "remote=\"" + dest_server + "\""
    update_xml(src_file, pattern, repl)

    args = "cd .repo/manifests; git add default.xml"
    subprocess.check_call(args, shell=True)
    args = "cd .repo/manifests; git commit -m " + "\"" + tag_name + "\""
    subprocess.check_call(args, shell=True)

def tag_manifest(dest_server, tag_name):
    # checkout new branch
    cd_args = "cd .repo/manifests ; "
    args = cd_args + "git checkout -b " + tag_name
    subprocess.check_call(args, shell=True)
    # create new commit
    new_commit(dest_server, tag_name)
    # mark tag
    args = cd_args + "git tag " + tag_name
    subprocess.check_call(args, shell=True)

def usage():
    print "\ttag.py [-i] <input dictionary> [-r] <remote server name> [-t] <tag name>"
    print "\t    [-r] <remote server name>: the server name that is used in manifest xml file."
    print "\t       [-h]"

def main(argv):
    input_file = ""
    remote_server = ""
    tag_name = ""
    try:
        opts, args = getopt.getopt(argv, "i:t:r:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-t"):
            tag_name = arg
        elif opt in ("-i"):
            input_file = arg
        elif opt in ("-r"):
            remote_server = arg

    if (tag_name == "") or (input_file == "") or (remote_server == ""):
        usage()
        sys.exit(2)

    tag_common(tag_name, input_file)
    tag_manifest(remote_server, tag_name)

if __name__ == "__main__":
    main(sys.argv[1:])
