#!/usr/bin/python
# v1.0
# generate the change log from last rev

import os
import sys
import getopt
from datetime import datetime, timedelta

#days is mange days ago
def generate_log_since(date, files):
    date_N_days_ago = datetime.now() - timedelta(days=date)
    args = "git log --since=\"" + str(date_N_days_ago) + "\""
    print "****** generate" + files + "******"
    print args
    if not os.path.isdir("out"):
        os.mkdir("out")
    f = open(files, 'w')
    f.write(os.popen(args).read())
    f.close()

def generate_change_log(ref):
    args = "git log " + str(ref) + ".." + "HEAD"
    if not os.path.isdir("out"):
        os.mkdir("out")
    f = open('out/changelog.build', 'w')
    f.write(os.popen(args).read())
    f.close()
    generate_log_since(1, "out/changelog.day")
    generate_log_since(7, "out/changelog.week")
    generate_log_since(20, "out/changelog.month")
    
def usage():
    print "generate_change_log -r {last success rev} | [-h]"

def main(argv):
    rev = ""
    try:
        opts, args = getopt.getopt(argv, "r:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-r"):
            rev = arg

    if (rev == ""):
        usage()
        sys.exit(2)

    generate_change_log(rev)

if __name__ == "__main__":
    main(sys.argv[1:])

