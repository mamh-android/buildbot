#!/usr/bin/python
# v1.0
#    current it only support gerrit 2.4.2 database structure
#    Author: yfshi@marvell.com

import subprocess
import getopt
import pickle
import re
import sys
import os
import csv

#Gerrit admin user
m_user = "buildfarm"

#Code remote server
m_remote_server = "shgit.marvell.com"

def return_gerrit_changes(path, branch, gerrit_open):
    global m_user
    global m_remote_server
    args = "ssh -p 29418 " + m_user + "@" + m_remote_server + " gerrit gsql -c \"select\ *\ from\ changes\ WHERE\ dest_branch_name=\\\'refs/heads/" + branch +  "\\\'\ AND\ open=\\\'" + gerrit_open + "\\\'\ AND\ dest_project_name\ REGEXP\ \\\'" + path + "\\\'\""
    return os.popen(args).read()

def setup_gerrit_changes_csv(fout, d_path, d_branch):
    out_csv = csv.writer(open(fout, 'wb'))
    f = open('tmptxt', 'w')
    f.write(return_gerrit_changes("X", "X", "X"))
    f.close()
    in_txt = csv.reader(open("tmptxt", "rb"), delimiter = '|')
    a = []
    for row in in_txt:
        a.append(row)
    a.pop(1)
    a.pop(len(a)-1)
    out_csv.writerows(a)
    for name, c_path in d_path.items():
        branch = d_branch.get(name)
        print name
        print branch
        f = open('tmptxt', 'w')
        f.write(return_gerrit_changes(c_path, branch, "Y"))
        in_txt = csv.reader(open("tmptxt", "rb"), delimiter = '|')
        f.close()
        a = []
        for row in in_txt:
            a.append(row)
        a.pop(0)  
        a.pop(0)
        a.pop(len(a)-1)
        out_csv.writerows(a)

#User help
def usage():
    print "\tcreate_csv [-o] <output file>"
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
    setup_gerrit_changes_csv(fout, d_path, d_branch)

if __name__ == "__main__":
    main(sys.argv[1:])
