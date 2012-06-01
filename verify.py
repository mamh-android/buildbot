#!/usr/bin/python
# v1.0
#	verify hash number with revision dictionary

import getopt
import pickle
import re
import subprocess
import sys

def check_hash(d_rev, d_path, tag_name):
    for name, rev in d_rev.items():
        c_path = d_path.get(name)

        args = "cd " + c_path + "; git rev-parse " + tag_name
        data = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_out, cmd_err = data.communicate()
        if (cmd_err):
            print cmd_err
            sys.exit(2)
        if not re.match(rev, cmd_out):
            print "These two values are not matched"
            print "revision number %s tag hash number %s" % (rev, cmd_out)
            sys.exit(2)

def usage():
    print "\tverify.py [-t] <tag name> [--dict-revision=] <rev dictionary>"
    print "\t          [--dict-path] <path dictionary> [-h]"

def main(argv):
    f_path = ""
    f_rev = ""
    tag_name = ""
    try:
        opts, args = getopt.getopt(argv, "t:h", ["dict-revision=", "dict-path="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-t"):
            tag_name = arg
        elif opt in ("--dict-revision"):
            f_rev = arg
        elif opt in ("--dict-path"):
            f_path = arg

    if (f_rev == "") or (f_path == "") or (tag_name == ""):
        usage()
        sys.exit(2)

    fp = open(f_rev, "r")
    d_rev = pickle.load(fp)
    fp.close()
    fp = open(f_path, "r")
    d_path = pickle.load(fp)
    fp.close()

    check_hash(d_rev, d_path, tag_name)

if __name__ == "__main__":
    main(sys.argv[1:])
