#!/usr/bin/python
# v1.0
# compare whether key is same in these two dictionary

import getopt
import pickle
import sys

# Return 0 if these two dictionary are same. Return negative if different.
# Return 1 if dictionary A is subset of dictionary B.
# Return 2 if dictionary B is subset of dictionary A.
def compare(filea, fileb):
    fpa = open(filea, "r")  # read mode
    da = pickle.load(fpa)
    fpa.close()

    fpb = open(fileb, "r")  # read mode
    db = pickle.load(fpb)
    fpb.close()

    if da.keys() == db.keys():
        return 0
    else:
        if len(da) == len(db):
            return -1
        elif len(da) < len(db):
            for k in da.iterkeys():
                if k not in db:
                    return -1
            return 1
        else:
            # len(da) > len(db)
            for k in db.iterkeys():
                if k not in da:
                    return -1
            return 2

def usage():
    print "comparedict -s {src dict file} -d {dst dict file} | [-h]"

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "s:d:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-s"):
            filea = arg
        elif opt in ("-d"):
            fileb = arg

    if (filea == "") or (fileb == ""):
        usage()
        sys.exit(2)

    ret = compare(filea, fileb)
    if ret == 0:
        print "These two dictionaries have same keys."
    else:
        print "Different keys existed in these two dictionaries."
        sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])
