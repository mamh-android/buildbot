#!/usr/bin/python
# v1.0
#    Cosmo By Patch Build (Cosmo_BPB)
#    Author: yfshi@marvell.com

import os
import sys
import getopt

COSMO_OUT_DIR = "out\\"
IMAGE_SERVER = "\\\\sh-srv06\\cosmo_build\\"
COSMO_CHANGELOG_BUILD = COSMO_OUT_DIR + "changelog.build"
PROJECT = "cosmo"
BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/cosmo_build/builds/"

def return_message(build_type, build_nr, result):
    message =  "Buildbot finished compiling your patchset\n"
    message += "on configuration: %s\n" % build_type
    message += "Buildbot Url: %s\n" % build_nr
    message += "The result is: %s\n" % result
    # message
    message = '"' + message + '"'
    return message

def send_codereview(project, revision, message=None, verified=0, reviewed=0):
    command = ["ssh", "buildfarm@privgit.marvell.com", "-p", "29418",
               "gerrit", "review", "--project %s" % str(project)]
    if message:
        command.append("--message '%s'" % message.replace("'","\""))
    if verified:
        command.extend(["--verified %d" % int(verified)])
    if reviewed:
        command.extend(["--code-review %d" % int(reviewed)])
    command.append(str(revision))
    print command
    os.system(' '.join(command))

def run(last_rev, build_nr=0):
    # cherry pick last rev
    c_cherrypick = ['python']
    c_cherrypick.append('..\\build_script\\core\\cherry_pick_open_patch.py')
    c_cherrypick.append('-c %s' % last_rev)
    ret = os.system(' '.join(c_cherrypick))
    if not (ret==0):
        message = return_message('[cherry-pick]', BUILDBOT_URL + build_nr, 'failed')
        send_codereview(PROJECT, last_rev, message, '-1', '-1')
        exit(1)
    # MSBuild
    c_msbuild = ['MSBuild', 'Cosmo.sln', '/t:Rebuild', '/p:Configuration=Release']
    ret = os.system(' '.join(c_msbuild))
    if not (ret==0):
        message = return_message('[MSBuild]', BUILDBOT_URL + build_nr, 'failed')
        send_codereview(PROJECT, last_rev, message, '-1', '-1')
        exit(1)
    # auto test
    c_dailytest = ['..\\build_script\\DailyAutoTest.py']
    ret = os.system(' '.join(c_dailytest))
    if not (ret==0):
        message = return_message('[Package-auto-test]', BUILDBOT_URL + build_nr, 'failed')
        send_codereview(PROJECT, last_rev, message, '-1', '-1')
        exit(1)
    message = return_message('[By-Patch-Build]', BUILDBOT_URL + build_nr, 'success')
    send_codereview(PROJECT, last_rev, message, '1', '1')
    exit(0)

#User help
def usage():
    print "\tpublish_and_sendmail"
    print "\t      [-r] revision"
    print "\t      [-n] build nr from buildbot"
    print "\t      [-h] help"

def main(argv):
    last_rev = ""
    build_nr = ""
    try:
        opts, args = getopt.getopt(argv,"r:n:h")
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
    if not last_rev or not build_nr:
        usage()
        sys.exit(2)

    run(last_rev, build_nr)

if __name__ == "__main__":
    main(sys.argv[1:])

