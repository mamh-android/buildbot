#!/usr/bin/python
# v1.0
#    Android By Patch Build (android_bpb)
#    Author: yfshi@marvell.com

import os
import sys
import subprocess
import getopt
import datetime
import ConfigParser

BUILD_TYPE = "rtvb"
BUILD_STDIO = ".stdout.log"
#BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/cosmo_by_patch_build/builds/"
BUILDBOT_URL = "http://10.38.116.72:8010/builders/rtvb_build/builds/"
SYNC_GIT_WORKING_DIR = "/home/buildfarm/aabs/rtvb_work"
OUT_WORKING_DIR = "/home/buildfarm/aabs/rtvb_out"
GERRIT_SERVER = "shgit.marvell.com"
GERRIT_ADMIN = "buildfarm"
REFERENCE_URL = "--reference=/mnt/mirror/default"
SRC_URL = "ssh://shgit.marvell.com/git/android/platform/manifest.git"
REPO_URL = "--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"
SCRIPT_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
FAILURE_COUNT = 0

# Internal variable
BRANCH_DICT = ".branch.pck"
CPATH_DICT = ".path.pck"

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def return_message(build_nr, result, branch=None):
    message =  "[%s] Buildbot finished compiling your patchset. " % BUILD_TYPE
    message += "Buildbot Url: [%s%s] " % (BUILDBOT_URL, build_nr)
    message += "Manifest Branch: [%s] " % branch
    message += "Android Increment Make: [%s] " % result
    # message
    message = '"' + message + '"'
    return message

def send_codereview(revision, message=None, verified=0, reviewed=0):
    command = ["ssh", "%s@%s" % (GERRIT_ADMIN, GERRIT_SERVER), "-p", "29418",
               "gerrit", "review"]
    if message:
        command.append("--message '%s'" % message)
    if verified:
        command.extend(["--verified %d" % int(verified)])
    if reviewed:
        command.extend(["--code-review %d" % int(reviewed)])
    command.append(str(revision))
    print command
    os.system(' '.join(command))

# return last build device from stdout log
def return_last_device(src_file, search):
    try:
        fp_src = open(src_file, 'r')
        fp_src.close()
    except IOError:
        print "failed to open file with read mode"
        exit(2)
    try:
        # return matching re
        arg = '''awk -F'=' '{if($1=="%s") print $2}' %s''' % (search, src_file)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        (out, nothing) = p.communicate()
        return out.split()[len(out.split())-1]
    except IOError:
        print "failed searching"
        exit(2)

def run(last_rev, build_nr=0, branch='master'):
    global FAILURE_COUNT
    # sync manifest
    print "[%s][%s] Start sync code" % (BUILD_TYPE, str(datetime.datetime.now()))
    if not os.path.isdir(SYNC_GIT_WORKING_DIR):
        FAILURE_COUNT += 1
        os.mkdir(SYNC_GIT_WORKING_DIR)
        c_fetch = "%s/fetchcode.py -u %s -b %s %s %s" % (SCRIPT_PATH, SRC_URL, branch, REFERENCE_URL, REPO_URL)
        print c_fetch
        subprocess.check_call(c_fetch, shell=True, cwd=SYNC_GIT_WORKING_DIR)
        # virtual aabs build
        if branch.split('_')[0] == 'rls':
           build_target = "%s-%s:%s" % (branch.split('_')[1], branch.split('_')[2], '_'.join(branch.split('_')[3:len(branch.split('_'))]))
        else:
           build_target = "%s" % branch
        print "[%s][%s] Start virtual aabs" % (BUILD_TYPE, str(datetime.datetime.now()))
        c_aabs = "%s/rtvb_aabs.sh %s %s %s | tee %s" % (SCRIPT_PATH, SYNC_GIT_WORKING_DIR, OUT_WORKING_DIR, build_target, BUILD_STDIO)
        subprocess.check_call(c_aabs, shell=True, cwd=SYNC_GIT_WORKING_DIR)
        ret_p = os.system("grep \">PASS<\" %s/%s" % (SYNC_GIT_WORKING_DIR, BUILD_STDIO))
        if not (ret_p==0):
            os.system('rm -rf %s' % SYNC_GIT_WORKING_DIR)
            print "[%s][%s] Failed virtual aabs" % (BUILD_TYPE, str(datetime.datetime.now()))
            exit(1)
        else:
            print "[%s][%s] End virtual aabs" % (BUILD_TYPE, str(datetime.datetime.now()))
    #else:
        #c_fetch = "repo sync"
        #subprocess.check_call(c_fetch, shell=True, cwd=SYNC_GIT_WORKING_DIR)
    print "[%s][%s] End sync code" % (BUILD_TYPE, str(datetime.datetime.now()))
    # chdir to source code location
    os.chdir(SYNC_GIT_WORKING_DIR)
    # Output project name and branch name into .name.pck
    c_getname = "%s/getname.py -o %s" % (SCRIPT_PATH, BRANCH_DICT)
    ret = os.system(c_getname)
    if not (ret==0):
        print "[%s][%s] Failed get branchname" % (BUILD_TYPE, str(datetime.datetime.now()))
        exit(1)
    # Output project name and client path into .path.pck
    c_getname = "%s/getname.py -p -o %s" % (SCRIPT_PATH, CPATH_DICT)
    ret = os.system(c_getname)
    if not (ret==0):
        print "[%s][%s] Failed get pathname" % (BUILD_TYPE, str(datetime.datetime.now()))
        exit(1)
    # check out revision
    print "[%s][%s] Start check-out patch %s" % (BUILD_TYPE, str(datetime.datetime.now()), last_rev)
    c_check_rev = "%s/android_bpb_pick.py -p %s -b %s" % (SCRIPT_PATH, last_rev, SYNC_GIT_WORKING_DIR)
    ret = os.system(c_check_rev)
    if not (ret==0):
        print "[%s][%s] Failed check-out patch %s" % (BUILD_TYPE, str(datetime.datetime.now()), last_rev)
        exit(1)
    print "[%s][%s] End check-out patch %s" % (BUILD_TYPE, str(datetime.datetime.now()), last_rev)
    # android build
    print "[%s][%s] Start android build" % (BUILD_TYPE, str(datetime.datetime.now()))
    product = return_last_device(BUILD_STDIO, 'TARGET_PRODUCT')
    variant = return_last_device(BUILD_STDIO, 'TARGET_BUILD_VARIANT')
    print "TARGET_PRODUCT:%s" % product
    print "TARGET_BUILD_VARIANT:%s" % variant
    c_rtvb_build = "%s/rtvb_build.sh %s %s" % (SCRIPT_PATH, product, variant)
    ret = os.system(c_rtvb_build)
    if not (ret==0):
        print "[%s][%s] Failed android build" % (BUILD_TYPE, str(datetime.datetime.now()))
        message = return_message(build_nr, 'failed', branch)
        send_codereview(last_rev, message, '0', '-1')
        FAILURE_COUNT += 1
        os.system("rm -rf %s" % SYNC_GIT_WORKING_DIR)
        return 1
    print "[%s][%s] End android build" % (BUILD_TYPE, str(datetime.datetime.now()))
    message = return_message(build_nr, 'success', branch)
    send_codereview(last_rev, message, '0', '1')
    exit(0)

#User help
def usage():
    print "\tandroid_bpb.py"
    print "\t      [-r] revision"
    print "\t      [-n] build nr from buildbot"
    print "\t      [-b] event.change.branch"
    print "\t      [-h] help"

def main(argv):
    last_rev = ""
    build_nr = ""
    branch = ""
    try:
        opts, args = getopt.getopt(argv,"r:n:b:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-r"):
            last_rev = arg
        elif opt in ("-n"):
            build_nr = arg
        elif opt in ("-b"):
            branch = arg.split('/')[0]
            global SYNC_GIT_WORKING_DIR
            SYNC_GIT_WORKING_DIR = SYNC_GIT_WORKING_DIR + '_' + branch
    if not last_rev or not build_nr:
        usage()
        sys.exit(2)

    while True:
        run(last_rev, build_nr, branch)
        print "FAILURE_COUNT %s" % FAILURE_COUNT
        if (FAILURE_COUNT == 0):
            exit(0)
        elif (FAILURE_COUNT > 1):
            exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])

