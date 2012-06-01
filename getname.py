#!/usr/bin/python
# v1.1
#   store data into output file by pickle

import getopt
import pickle
import subprocess
import sys

def store(fout, output):
    idict = {}
    while output:
    	mid = output.find(":")
    	project = output[:mid]
    	end = output.find("\n")
        lrev = output[mid+1:end]
    	output = output[end+1:]
    
        item = { project:lrev }
        idict.update(item)

    # store idict into output file
    fp = open(fout, "w")
    pickle.dump(idict, fp)
    fp.close()

def get_project_branch(fout):
    # store project name & RREV (branch name or revision number)
    process = subprocess.Popen(["repo", "forall", "-c",  """echo $REPO_PROJECT:$REPO_RREV"""], stdout=subprocess.PIPE)
    output, err = process.communicate()
    if (err):
        print err
    	sys.exit(2)
    store(fout, output)

def get_local_path(fout):
    # store project name & local path
    process = subprocess.Popen(["repo", "forall", "-c", """echo $REPO_PROJECT:$REPO_PATH"""], stdout=subprocess.PIPE)
    output, err = process.communicate()
    if (err):
        print err
        sys.exit(2)
    store(fout, output)

def usage():
    print "getname.py [-p] -o <output file> [-h]"
    print "\toutputs $REPO_PROJECT & $REPO_RREV."
    print "\t\t$REPO_RREV is either branch name or revision number."
    print "\t-p outputs $REPO_PROJECT & $REPO_PATH"
    print "\t-o stores output data into file"

def main(argv):
    fout = ""
    out_path = 0
    try:
        opts, args = getopt.getopt(argv, "o:ph")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-o"):
            fout = arg
        elif opt in ("-p"):
            out_path = 1

    if fout == "":
        usage()
        sys.exit(2)

    if out_path == 1:
        get_local_path(fout)
    else:
        get_project_branch(fout)

if __name__ == "__main__":
    main(sys.argv[1:])
