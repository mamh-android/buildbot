#!/usr/bin/python
# v1.1
#    Author: yfshi@marvell.com

import subprocess
import getopt
import pickle
import re
import sys
import os
import csv
import json
import shlex
import datetime
from datetime import datetime, timedelta

#Gerrit admin user
m_user = "buildfarm"

#Code remote server
m_remote_server = "shgit.marvell.com"

VERBOSE = False

def run_command_status(*argv, **env):
    if VERBOSE:
        print(datetime.datetime.now(), "Running:", " ".join(argv))
    if len(argv) == 1:
        argv = shlex.split(str(argv[0]))
    newenv = os.environ
    newenv.update(env)
    p = subprocess.Popen(argv, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, env=newenv)
    (out, nothing) = p.communicate()
    out = out.decode('utf-8')
    return (p.returncode, out.strip())


def run_command(*argv, **env):
    (rc, output) = run_command_status(*argv, **env)
    return output

#project: branch: is:open (Verified<=0 or CodeReview>=0)
def return_json_str_list(project, branch):
    cmd = "ssh -p 29418 %s@%s gerrit query --current-patch-set --format=JSON NOT age:5day project:^.*%s branch:%s is:open (Verified<=0 OR CodeReview>=0)" % (m_user, m_remote_server, project, branch)
    (status, remote_output) = run_command_status(cmd)
    json_list = []
    for output in remote_output.split('\n'):
        jsonstr = json.loads(output)
        if not jsonstr.has_key('runTimeMilliseconds'):
            json_list.append(jsonstr)
    return json_list

#
def setup_json_str_file(fout, d_path, d_branch):
    print "Setup patches list file for rtvb"
    all_json_list = []
    for path_name, c_path in d_path.items():
        branch = d_branch.get(path_name)
        print path_name
        print branch
        #Create all list
        all_json_list.extend(return_json_str_list(path_name, branch))
    all_json_list = sorted(all_json_list, key=lambda patch: patch['currentPatchSet']['createdOn'])
    outfile = open(fout, 'w')
    for json_str in all_json_list:
        json.dump(json_str, outfile)
        outfile.write('\n')
    outfile.close()

#User help
def usage():
    print "\tcreate_rtvb [-o] <output file>"
    print "\t      [-b] {branch file from getname}"
    print "\t      [-p] {path file from getname}"
    print "\t      [-h] help"

def main(argv):
    fout = ""
    branch_list = ""
    path_list = ""
    try:
        opts, args = getopt.getopt(argv, "o:b:p:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-o"):
            fout = arg
            print fout
        elif opt in ("-b"):
            branch_list = arg
            print branch_list
        elif opt in ("-p"):
            path_list = arg
            print path_list

    if fout == "" or branch_list == "" or path_list == "":
        usage()
        sys.exit(2)
    fp = open(path_list, "r")
    d_path = pickle.load(fp)
    fp.close()
    fp = open(branch_list, "r")
    d_branch = pickle.load(fp)
    fp.close()
    setup_json_str_file(fout, d_path, d_branch)

if __name__ == "__main__":
    main(sys.argv[1:])
