#!/usr/bin/python
# v1.0
#    Load wfd libs autobuild

import os
import sys
import getopt
import shutil
import subprocess
import datetime
from datetime import date

BUILD_LOG = ".wfd.build.log"
BUILD_STDIO = "/home/buildfarm/buildbot_script/stdio.log"
AABS_FOLDER = "/home/buildfarm/aabs"
PUBLISH_DEST = "/autobuild/wfd_libs/"
BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/android_develop_build/builds/"
FILE_SERVER = "\\\\sh-fs04"

# Gerrit admin user
ADM_USER = "buildfarm"

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

def return_failure_log(logfile):
    failure_log = ""
    if os.path.isfile(logfile):
        infile = open(logfile, 'r')
        f = infile.readlines()
        infile.close()
        if len(f) > 200:
            i = len(f)-100
            while i < len(f):
                failure_log = failure_log + f[i]
                i = i + 1
        else:
            for log in f:
                failure_log = failure_log + log
    return failure_log

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

#create a folder according to git branch name and time.today
def check_publish_folder(IMAGE_SERVER, branch):
    today = date.today()
    folder = str(today) + '_' + branch
    folder_server = IMAGE_SERVER + folder
    f = folder_server
    if not os.path.isdir(f):
        #os.mkdir(f)
        return f
    else:
        i=1
        while os.path.isdir(folder_server):
            f = folder_server + '_' + str(i)
            if not os.path.isdir(f):
                #os.mkdir(f)
                return f
                break
            else:
                i=i+1

def copy_file(src, dst):
    print src
    if os.path.isdir(src):
        p = "copy directory: " + src + "-->" + dst
        print p
        path = os.path.dirname(dst)
        if not os.path.isdir(path):
            os.makedirs(path)
        shutil.copytree(src, dst)
    if os.path.isfile(src):
        p = "copy file: " + src + "-->" + dst
        print p
        path = os.path.dirname(dst)
        if not os.path.isdir(path):
            os.makedirs(path)
        shutil.copy(src, dst)
    else:
        p = "publishing failed, file " + src + " dose not existed"
        print p
        exit(2)

def run(branch='master', build_nr=None):
    # check if aabs build passed
    ret_p = os.system("grep \">PASS<\" %s" % BUILD_STDIO)
    ret_n = os.system("grep \">No build<\" %s" % BUILD_STDIO)
    if not (ret_p==0) or (ret_n==0):
        print "No AABS build, exit 0"
        exit(0)
    # Set env
    print "[wfd-build][%s] Start set env" % str(datetime.datetime.now())
    product = return_last_device(BUILD_STDIO, 'TARGET_PRODUCT')
    variant = return_last_device(BUILD_STDIO, 'TARGET_BUILD_VARIANT')
    if branch.split('_')[0] == 'rls':
       src_dir = "src.%s-%s.%s" % (branch.split('_')[1], branch.split('_')[2], '_'.join(branch.split('_')[3:len(branch.split('_'))]))
    else:
       src_dir = "src.%s" % branch.replace('_', '-')
    src_dir_r = AABS_FOLDER + '/' + src_dir
    print "[wfd-build][%s] End set env" % (str(datetime.datetime.now()))
    # Start wfd build
    print "[wfd-build][%s] Start load updateWFDLibs.py" % (str(datetime.datetime.now()))
    c_build = ['%s/updateWFDLibs.py' % SCRIPT_PATH, '-m Autobuild', '-a %s' % src_dir_r, '-p %s-%s' % (product, variant)]
    ret = os.system(' '.join(c_build))
    if not (ret==0):
        print "[wfd-build][%s] Failed Build" % (str(datetime.datetime.now()))
        exit(1)
    print "[wfd-build][%s] End Build" % (str(datetime.datetime.now()))
    # All Success
    print "[Ipp-build][%s] All success" % (str(datetime.datetime.now()))
    exit(0)

#User help
def usage():
    print "\tLoad_wfd_build.py"
    print "\t      [-b] branch"
    print "\t      [-n] buildnumber from buildbot"
    print "\t      [-h] help"

def main(argv):
    branch = ""
    build_nr = ""
    try:
        opts, args = getopt.getopt(argv,"b:n:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-b"):
            branch = arg
        elif opt in ("-n"):
            build_nr = arg
    if not branch or not build_nr:
        usage()
        sys.exit(2)

    run(branch, build_nr)

if __name__ == "__main__":
    main(sys.argv[1:])

