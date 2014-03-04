#!/usr/bin/python
# v1.0
#    Cosmo By Patch Build (Cosmo_BPB)
#    Author: yfshi@marvell.com

import os
import sys
import getopt
import datetime
import ConfigParser

COSMO_OUT_DIR = "out\\"
IMAGE_SERVER = "\\\\sh-srv06\\cosmo_build_bpb\\"
PROJECT = "cosmo"
BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/cosmo_by_patch_build/builds/"

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

def run(last_rev, build_nr=0, branch='master', config_file='..\\test\\example.cfg'):
    # cherry pick last rev
    print "[Cosmo-BPB][%s] Start patch cherry-pick" % (str(datetime.datetime.now()))
    c_cherrypick = []
    c_cherrypick.append('..\\build_script\\core\\cherry_pick_open_patch.py')
    c_cherrypick.append('-c %s' % last_rev)
    c_cherrypick.append('-b %s' % branch)
    ret = os.system(' '.join(c_cherrypick))
    if not (ret==0):
        print "[Cosmo-BPB][%s] Failed patch cherry-pick" % (str(datetime.datetime.now()))
        message = return_message('[cherry-pick]', BUILDBOT_URL + build_nr, 'failed')
        send_codereview(PROJECT, last_rev, message, '-1', '-1')
        exit(1)
    print "[Cosmo-BPB][%s] End patch cherry-pick" % (str(datetime.datetime.now()))
    # MSBuild
    print "[Cosmo-BPB][%s] Start MSBuild" % (str(datetime.datetime.now()))
    c_msbuild = ['MSBuild', 'Cosmo.sln', '/t:Rebuild', '/p:Configuration=Release']
    ret = os.system(' '.join(c_msbuild))
    if not (ret==0):
        print "[Cosmo-BPB][%s] Failed MSBuild" % (str(datetime.datetime.now()))
        message = return_message('[MSBuild]', BUILDBOT_URL + build_nr, 'failed')
        send_codereview(PROJECT, last_rev, message, '-1', '-1')
        exit(1)
    print "[Cosmo-BPB][%s] End MSBuild" % (str(datetime.datetime.now()))
    # Load ConfigParser from config_file
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    calib_commands = filter(lambda x: len(x) > 0, config.get('Calib', 'calib_commands').replace('\\\\','\\').split('\n'))
    simu_commands = filter(lambda x: len(x) > 0, config.get('Simu', 'simu_commands').replace('\\\\','\\').split('\n'))
    # auto test calib
    print "[Cosmo-BPB][%s] Start calib" % (str(datetime.datetime.now()))
    c_calib = ['..\\build_script\\core\\mulit_core_task_run.py -c "..\\bin\\cosmo.exe" -l "%s"' % (','.join(calib_commands))]
    ret = os.system(' '.join(c_calib))
    if not (ret==0):
        print "[Cosmo-BPB][%s] Failed calib" % (str(datetime.datetime.now()))
        message = return_message('[Package-calib]', BUILDBOT_URL + build_nr, 'failed')
        send_codereview(PROJECT, last_rev, message, '-1', '-1')
        exit(1)
    # auto test simu
    print "[Cosmo-BPB][%s] Start simu" % (str(datetime.datetime.now()))
    c_simu = ['..\\build_script\\core\\mulit_core_task_run.py -c "..\\bin\\cosmo.exe" -l "%s"' % (','.join(simu_commands))]
    ret = os.system(' '.join(c_simu))
    if not (ret==0):
        print "[Cosmo-BPB][%s] Failed simu" % (str(datetime.datetime.now()))
        message = return_message('[Package-simu]', BUILDBOT_URL + build_nr, 'failed')
        send_codereview(PROJECT, last_rev, message, '-1', '-1')
        exit(1)
    # Publishing
    print "[Cosmo-BPB][%s] Start Publishing" % (str(datetime.datetime.now()))
    c_publishing = ['..\\build_script\\core\\publish_results.py']
    c_publishing.append('-s %s' % COSMO_OUT_DIR)
    c_publishing.append('-d %s' % IMAGE_SERVER)
    c_publishing.append('-r %s' % last_rev)
    ret = os.system(' '.join(c_publishing))
    if not (ret==0):
        print "[Cosmo-BPB][%s] Failed Publishing" % (str(datetime.datetime.now()))
        message = return_message('[Package-publishing]', BUILDBOT_URL + build_nr, 'failed')
        send_codereview(PROJECT, last_rev, message, '-1', '-1')
        exit(1)
    print "[Cosmo-BPB][%s] End Autotest" % (str(datetime.datetime.now()))
    print "[Cosmo-BPB][%s] All success, updating gerritreview" % (str(datetime.datetime.now()))
    message = return_message('[By-Patch-Build]', BUILDBOT_URL + build_nr, 'success', last_rev)
    send_codereview(PROJECT, last_rev, message, '1', '1')
    exit(0)

#User help
def usage():
    print "\tCosmo_PBP.py"
    print "\t      [-r] revision"
    print "\t      [-n] build nr from buildbot"
    print "\t      [-b] event.change.branch"
    print "\t      [-f] test set cfg file"
    print "\t      [-h] help"

def main(argv):
    last_rev = ""
    build_nr = ""
    branch = ""
    config_file = ""
    try:
        opts, args = getopt.getopt(argv,"r:n:b:f:h")
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
        elif opt in ("-f"):
            config_file = arg
    if not last_rev or not build_nr or not branch or not config_file:
        usage()
        sys.exit(2)

    run(last_rev, build_nr, branch, config_file)

if __name__ == "__main__":
    main(sys.argv[1:])

