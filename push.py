#!/usr/bin/python
# v1.0
#    Successfully update it to dest server

import subprocess
import getopt
import pickle
import re
import sys

# manifest git name
m_name = "platform/manifest.git"

#r_name is hardcoding. This name should be avoided in git repository.
r_name = "_rmt_dst"

def new_git(dest_server, dest_root, c_path, p_name):
    # Check whether client path is valid
    args = "test -e " + c_path
    subprocess.check_call(args, shell=True)

    path = dest_root + p_name
    ssh_args = "ssh -o StrictHostKeyChecking=no -C " + dest_server
    args = ssh_args + " \"test -e " + path + "\""
    ret = subprocess.call(args, shell=True)
    if (ret != 0):
        args = ssh_args + " \"mkdir -p " + path + "\""
        subprocess.check_call(args, shell=True)
        args = ssh_args + " \"git init --bare " + path + "\""
        subprocess.check_call(args, shell=True)

def upload_single_git(c_path, d_path, branch_name, tag_name):
    cd_args = "cd " + c_path + " ; "
    rmt_add_args = cd_args + "git remote add " + r_name + " ssh://" + d_path
    rmt_del_args = cd_args + "git remote rm " + r_name
    p_args = cd_args + "git push " + r_name + " refs/tags/" + tag_name + ":refs/heads/" + branch_name
    ptag_args = cd_args + "git push " + r_name + " refs/tags/" + tag_name + ":refs/tags/" + tag_name
    #print rmt_add_args
    #print p_args
    #print ptag_args
    #print rmt_del_args
    data = subprocess.Popen(rmt_add_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_out, cmd_err = data.communicate()
    if (cmd_err):
        if (cmd_err.find("already exists") == -1):
            subprocess.check_call(rmt_del_args, shell=True)
            subprocess.check_call(rmt_add_args, shell=True)
    print p_args
    subprocess.check_call(p_args, shell=True)
    subprocess.check_call(ptag_args, shell=True)
    subprocess.check_call(rmt_del_args, shell=True)

# parse remote server and root from remote url
def get_remote_url(d_path):
    global m_name
    cd_args = "cd .repo/manifests; "
    args = cd_args + "git config remote.origin.url"
    data = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_out, cmd_err = data.communicate()
    if (cmd_err):
        print cmd_err
        sys.exit(2)
    # remove "ssh://"
    data = re.compile("ssh://")
    cmd_out = data.sub("", cmd_out)
    # find remote origin server
    mid = cmd_out.find("/")
    r_server = cmd_out[:mid]
    cmd_out = cmd_out[mid:]
    # project may be "platform/.." or "android/platform/.."
    for name in d_path.keys():
        i = name.find("platform/")
        if i == -1:
            continue
        m_name = name[:i] + m_name
        break
    # remove manifest path to get root
    i = cmd_out.find(m_name)
    r_root = cmd_out[:i]
    return r_server, r_root

# Upload commits for common projects
def push_git_bdict(dest_server, dest_root, d_path, d_branch, tag_name):
    for name, c_path in d_path.items():
        branch = d_branch.get(name)
        print name
        print branch
        p_name = name + ".git"
        # create empty git if necessary
        new_git(dest_server, dest_root, c_path, p_name)
        path = dest_server + dest_root + p_name
        upload_single_git(c_path, path, branch, tag_name)

def push_git_bname(dest_server, dest_root, d_path, branch_name, tag_name):
    for name, c_path in d_path.items():
        p_name = name + ".git"
        # create empty git if necessary
        new_git(dest_server, dest_root, c_path, p_name)
        path = dest_server + dest_root + p_name
        upload_single_git(c_path, path, branch_name, tag_name)

# Upload commits for manifest git
def push_manifest(dest_server, dest_root, branch_name, tag_name):
    path = dest_server + dest_root + m_name
    # create empty git if necessary
    new_git(dest_server, dest_root, ".repo/manifests", m_name)
    upload_single_git(".repo/manifests", path, branch_name, tag_name)

def usage():
    print "\tpush [-d] <dest server> [-r] <dest root directory> [-b] <manifest branch>"
    print "\t     [--dict-path] <path dictionary> [--dict-branch] <branch dictionary>"
    print "\t     [-t] <tag name> [--tagsrc] [-h]"

def main(argv):
    dest_server = ""
    dest_root = ""
    f_path = ""
    f_branch = ""
    tag_back = 0
    tag_name = ""
    branch_name = ""
    try:
        opts, args = getopt.getopt(argv, "b:d:r:t:h", ["tagsrc", "dict-path=", "dict-branch="])
    except getopt.GetoptError:
    	usage()
    	sys.exit(2)
    for opt, arg in opts:
    	if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-b"):
            branch_name = arg
    	elif opt in ("-d"):
    	    dest_server = arg
    	elif opt in ("-r"):
    	    dest_root = arg
    	elif opt in ("-t"):
    	    tag_name = arg
    	elif opt in ("--tagsrc"):
    	    tag_back = 1
        elif opt in ("--dict-path"):
            f_path = arg
        elif opt in ("--dict-branch"):
            f_branch = arg

    if (f_path == "") or (f_branch == "") or (tag_name == ""):
        usage()
        sys.exit(2)

    # --tagsrc can't work with "-d" or "-r" or "-b" together
    if (tag_back == 0) and ((dest_server == "") or (dest_root == "") or (branch_name == "")):
        usage()
        sys.exit(2)

    fp = open(f_path, "r")
    d_path = pickle.load(fp)
    fp.close()
    fp = open(f_branch, "r")
    d_branch = pickle.load(fp)
    fp.close()

    if tag_back == 1:
        r_server, r_root = get_remote_url(d_path)
        # upload common git
        push_git_bdict(r_server, r_root, d_path, d_branch, tag_name)
        # upload manifest git (use tag name as branch name)
        push_manifest(r_server, r_root, tag_name, tag_name)
    else:
        # upload common git
        push_git_bname(dest_server, dest_root, d_path, branch_name, tag_name)
        # upload manifest git (use tag name as branch name)
        push_manifest(dest_server, dest_root, tag_name, tag_name)

if __name__ == "__main__":
    main(sys.argv[1:])
