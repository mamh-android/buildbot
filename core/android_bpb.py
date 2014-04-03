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
BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/cosmo_by_patch_build/builds/"
SYNC_GIT_WORKING_DIR = "/home/yfshi/aabs/rtvb_work"
OUT_WORKING_DIR = "/home/yfshi/aabs/rtvb_out"
GERRIT_SERVER = "shgit.marvell.com"
GERRIT_ADMIN = "buildfarm"
REFERENCE_URL = "--reference=/mnt/mirror/default"
SRC_URL = "ssh://shgit.marvell.com/git/android/platform/manifest.git"
REPO_URL = "--repo-url=ssh://shgit.marvell.com/git/android/tools/repo"
SCRIPT_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def return_message(build_type, build_nr, result, rev=None):
    message =  "Buildbot finished compiling your patchset "
    message += "on configuration: %s " % build_type
    message += "Buildbot Url: %s " % build_nr
    message += "The result is: %s " % result
    if (result == 'success'):
        message += "Package at: http:%s%s/ " % (IMAGE_SERVER.replace('\\','/'), rev)
        message += "OutputImages at: http:%s%s/cosmobuild/test/OutputImages/ " % (IMAGE_SERVER.replace('\\','/'), rev)
    # message
    message = '"' + message + '"'
    return message

def send_codereview(project, revision, message=None, verified=0, reviewed=0):
    command = ["ssh", "buildfarm@privgit.marvell.com", "-p", "29418",
               "gerrit", "review", "--project %s" % str(project)]
    if message:
        command.append("--message '%s'" % message)
    if verified:
        command.extend(["--verified %d" % int(verified)])
    if reviewed:
        command.extend(["--code-review %d" % int(reviewed)])
    command.append(str(revision))
    print command
    os.system(' '.join(command))

def run(last_rev, build_nr=0, branch='master'):
    # sync manifest
    print "[%s][%s] Start sync code" % (BUILD_TYPE, str(datetime.datetime.now()))
    if not os.path.isdir(SYNC_GIT_WORKING_DIR):
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
        c_aabs = "%s/rtvb_aabs.sh %s %s %s" % (SCRIPT_PATH, SYNC_GIT_WORKING_DIR, OUT_WORKING_DIR, build_target)
        ret = os.system(c_aabs)
        if not (ret==0):
            print "[%s][%s] Failed virtual aabs" % (BUILD_TYPE, str(datetime.datetime.now()))
            exit(1)
        print "[%s][%s] End virtual aabs" % (BUILD_TYPE, str(datetime.datetime.now()))
    else:
        c_fetch = "repo sync"
        subprocess.check_call(c_fetch, shell=True, cwd=SYNC_GIT_WORKING_DIR)
    print "[%s][%s] End sync code" % (BUILD_TYPE, str(datetime.datetime.now()))
    # check out revision
    print "[%s][%s] Start check-out patch %s" % (BUILD_TYPE, str(datetime.datetime.now()), last_rev)
    c_check_rev = "%s/android_bpb_pick.py -p %s -b %s" % (SCRIPT_PATH, last_rev, SYNC_GIT_WORKING_DIR)
    ret = os.system(c_check_rev)
    if not (ret==0):
        print "[%s][%s] Failed check-out patch %s" % (BUILD_TYPE, str(datetime.datetime.now()), last_rev)
        exit(1)
    print "[%s][%s] End check-out patch %s" % (BUILD_TYPE, str(datetime.datetime.now()), last_rev)
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
    if not last_rev or not build_nr:
        usage()
        sys.exit(2)

    run(last_rev, build_nr, branch)

if __name__ == "__main__":
    main(sys.argv[1:])

