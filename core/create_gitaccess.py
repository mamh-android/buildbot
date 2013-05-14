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

test_download_url = "repo init -u ssh://{username}@github.marvell.com:29418/platform/manifest.git -b pxa988_jb4.2.beta2-ss-sp1 --repo-url ssh://{username}@github.marvell.com:29418/tools/repo.git"

test_gitaccess_name = ""

#Gerrit admin user
r_user = "{username}"

#release git server
release_git_server = "github.marvell.com:29418"
 
#generate .gitaccess file and exit with gitaccess path
#use a=$(./create_gitaccess.py -b rls_pxa988_jb4.2 -t pxa988-jb4.2.beta2-sp3) pass it to shell script
def generate_gitaccess(branchname,tagname):
    s_branchname = branchname.split('_')
    s_tagname = tagname.split('.')
    if s_branchname[0] == "rls":
        del s_branchname[0]
    else:
        print "Please give a valid branchname"
        sys.exit(1)
    name_gitaccess = s_branchname[0] + '.' + '-'.join(s_branchname) + '.' + s_tagname[len(s_tagname)-1] + ".gitaccess"
    tmp_gitaccess = "/tmp/" + name_gitaccess
    try:
        f_gitaccess = open(tmp_gitaccess, 'w')
        f_gitaccess.write(generate_download_url(tagname))
        f_gitaccess.close()
    except IOError:
        print "Failed to create gitaccess file with name" + name_gitaccess
        sys.exit(1)
    print tmp_gitaccess
    sys.exit(0)

#generate downurl by tag name
def generate_download_url(tagname):
    global r_user
    global release_git_server
    download_url = "repo init -u ssh://" + r_user + "@" + release_git_server + "/platform/manifest.git -b " + tagname + " --repo-url ssh://" + r_user + "@" + release_git_server + "/tools/repo.git\n\nrepo sync\n"
    return download_url

#User help
def usage():
    print "\tcreate_gitaccess_file [-b] branchname"
    print "\t      [-t] tag name"
    print "\t      [-h] help"

def main(argv):
    branch = ""
    tag = ""
    try:
        opts, args = getopt.getopt(argv,"b:t:h",["showonly","username","remote"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-b"):
            branch = arg
        elif opt in ("-t"):
            tag = arg
    if (branch == "") or (tag == ""):
        usage()
        sys.exit(2)
    else:
        generate_gitaccess(branch,tag)

if __name__ == "__main__":
    main(sys.argv[1:])
