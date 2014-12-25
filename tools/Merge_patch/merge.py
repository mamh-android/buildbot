#!/usr/bin/python
# v1.0 Base function is ready
# v1.1 Push to remote function enabled
#    merge patch_list.diff

import os
import sys
import string
import getopt
import datetime
import csv

SCRIPT_TYPE = 'Merging_Patch'
C_PATH = os.getcwd()
SCRIPT_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
DREMOTE = None
DBRANCH = None
RENAME = False

#Define patchInfo object array class
class patchinfo:
    def __init__(self, project, patch, status):
        self.project = project
        self.patch = patch
        self.status = status
    def __repr__(self):
        return repr((self.project, self.patch, self.status))

#Return patch object from input_file
class XXTree:
    def __init__(self):
        pass

    def createTree(self, dir, op):
        list = self.getList(dir, 0, op)
        patchList = []

        for i in range(0, len(list)):
            realdir = os.path.realpath(dir) + '/'
            fullpath = os.path.realpath(list[i])
            parpath = os.path.dirname(fullpath)
            projectpath = parpath.replace(realdir, "")
            if os.path.splitext(fullpath)[1][1:] == 'patch' and os.path.isfile(fullpath):
                patchList.append(patchinfo(projectpath, fullpath, 'N/A'))

        return patchList

    def getList(self, dir, layer, op):
        list = []
        if layer == 0: list.append(dir)
        files = os.listdir(dir)
        for file in files:
            file = os.path.join(dir, file)
            if os.path.isdir(file):
                #list.append(file)  
                list += self.getList(file, layer + 1, op)
            elif op == '-d':
                pass
            else:
                list.append(file)
        return list

#git push
def gitPush(project, remote, branch):
    for i in range(5):
        cmd = "cd %s;" % project
        cmd += "git push %s HEAD:refs/heads/%s;" % (remote, branch)
        status = os.system(cmd)
        if (status==0):
            print "Success: %s" %cmd
            break
        else:
            print "Retry: %s" %cmd

def clrEnv(project):
    cmd = "cd %s;" % project
    cmd += "git clean -f;"
    cmd += "git reset --hard HEAD;"
    status = os.system(cmd)

#write to csv
def patchToCsv(patchList, outputfile):
    out_csv = csv.writer(open(outputfile, 'wb'))
    head = ['project', 'patches','status']
    out_csv.writerow(head)
    for i in patchList:
        project = i.project
        patch = os.path.relpath(i.patch)
        status = i.status
        out_csv.writerow([project, patch, status])

def run(input_file, output_file):
    #creating patchList
    t = XXTree()
    print "[%s][%s] Start" % (SCRIPT_TYPE, str(datetime.datetime.now()))
    patchList = t.createTree(input_file, op=None)
    patchList = sorted(patchList, key=lambda self: self.patch)
    #Apply patch
    for i in patchList:
        cmd = "cd %s;" % i.project
        cmd += "git am %s;" % i.patch
        print cmd
        status = os.system(cmd)
        if (status==0):
            i.status = 'P'
            m = i.patch + '.merged'
            if RENAME == True:
                os.rename(i.patch, m)
            if DREMOTE and DBRANCH:
                print "publishing out"
                gitPush(i.project, DREMOTE, DBRANCH)
        else:
            i.status = 'F'
            clrEnv(i.project)
    #write to csv
    patchToCsv(patchList, output_file)
    print "[%s][%s] Completed" % (SCRIPT_TYPE, str(datetime.datetime.now()))
    #print patchList
    exit(0)

#User help
def usage():
    print "\tmerge.py"
    print "\t       ===[mandatory section]==="
    print "\t      [-i] input patch.diff"
    print "\t       ===[optional section]==="
    print "\t      [-o] output results file by default <out.csv>"
    print "\t       Only both remote and branch is available, the patch will be push out"
    print "\t      [--remote={remote}]"
    print "\t      [--branch={branch}]"
    print "\t      [--rename] rename the patch if it's on"
    print "\t      [-h] help"

def main(argv):
    input_file = None
    output_file = 'out.csv'
    global DREMOTE
    global DBRANCH
    global RENAME
    try:
        opts, args = getopt.getopt(argv,"i:o:h",["rename","remote=", "branch="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-i"):
            input_file = arg
        elif opt in ("-o"):
            output_file = arg
        elif opt in ("--remote"):
            DREMOTE = arg
        elif opt in ("--branch"):
            DBRANCH = arg
        elif opt in ("--rename"):
            RENAME = True

    if not input_file:
        usage()
        sys.exit(2)

    run(input_file, output_file)

if __name__ == "__main__":
    main(sys.argv[1:])

