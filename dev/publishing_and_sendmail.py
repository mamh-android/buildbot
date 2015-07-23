#!/usr/bin/python

#publishing and send mail script


import os
import sys
#import core script
sys.path.append("..\\build_script\\core")
from generate_change_log import *
from send_mail import *
from publish_to_image_server import *

COSMO_OUT_DIR = "out\\"
IMAGE_SERVER = "\\\\sh-srv06\\cosmo_build\\"
MAIL_LIST = get_mail_list("cosmo-dev")
#add Simon Kershaw into MAIL_LIST for specical case
MAIL_LIST.append('skershaw@marvell.com')
COSMO_BUILD_LOG = ".cosmo.build.log"
COSMO_DAILY_TEST_LOG = ".cosmo.dailytest.log"
COSMO_CHANGELOG_BUILD = COSMO_OUT_DIR + "changelog.build"

def get_ret():
    infile = open(COSMO_BUILD_LOG,"r")
    text = infile.read()
    infile.close()
    search = "    0 Error(s)"
    no_err = text.find(search)
    infile = open(COSMO_DAILY_TEST_LOG,"r")
    text = infile.read()
    infile.close()
    search = "*** Cosmo Daily Test: all runnings success"
    no_failure = text.find(search)
    if not no_err == (-1) and not no_failure == (-1):
        buildresult = "success"
    elif not no_failure == (-1):
        buildresult = "failure"
    else:
        buildresult = "autotest_failure"
    print "*****BUILDR******" + buildresult
    return buildresult

def run(buildresult,build_nr):
    build_link = "http://buildbot.marvell.com:8010/builders/cosmo_build/builds/" + build_nr
    branch = os.popen("git branch").read().split()[1]
    last_build = IMAGE_SERVER + "LAST_BUILD."  + branch
    if os.path.isfile(last_build):
        infile = open(last_build, 'r')
        f = infile.read()
        infile.close()
        last_rev = f.split()[0]
    else:
        last_rev = ""
    current_rev = os.popen("git log -1 " + branch + " --pretty=format:%H").read().split()
    if current_rev[0] == last_rev:
#Nobuild mail
        subject = "[cosmo-autobuild-%s][%s] Nobuild" % (branch, str(date.today()))
        text = '''
This is an automated email from cosmo auto build system. The email
was generated because the system detects no significant change in
source code since last build.

BuildBot Url:
%s

Regards,
Team of Cosmo''' % (build_link)

        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        print "~~<result>PASS</result>"
        print "~~<result-details>No build</result-details>"
        exit(255)
    elif (buildresult == "success"):
        generate_change_log(last_rev)
        if os.path.isfile(COSMO_CHANGELOG_BUILD):
            infile = open(COSMO_CHANGELOG_BUILD, 'r')
            change_log = infile.read()
            infile.close()
        image_path = publish_file(COSMO_OUT_DIR, IMAGE_SERVER)
#Success mail
        subject = "[cosmo-autobuild-%s][%s] Success" % (branch, str(date.today()))
        text = '''
This is an automated email from cosmo auto build system. It was
generated because a new package was build successfully and passed
the smoke test.

BuildBot Url:
%s

You can download the package at:
%s

The change since last build is listed below:
%s

Regards,
Team of Cosmo''' % (build_link, image_path, change_log)

        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        if current_rev:
            f = open(last_build, 'w')
            f.write(current_rev[0])
            f.write("\nPackage: ")
            f.write(image_path)
            f.close()
            print "Publish is done"
            print "~~<result>PASS</result>"
            print "~~<result-dir>" + image_path + "</result-dir>"
        exit(0)
    elif (buildresult == "failure"):
        generate_change_log(last_rev)
        if os.path.isfile(COSMO_CHANGELOG_BUILD):
            infile = open(COSMO_CHANGELOG_BUILD, 'r')
            change_log = infile.read()
            infile.close()
        image_path = publish_file(COSMO_OUT_DIR, IMAGE_SERVER)
        failure_log = ""
        infile = open(COSMO_BUILD_LOG, 'r')
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
#Build Failed mail
        subject = "[cosmo-autobuild-%s][%s] Build Failed" % (branch, str(date.today()))
        text = '''
This is an automated email from cosmo auto build system. It was
generated because an error encountered while building the code.
The error can be resulted from newly checked in codes.

BuildBot Url:
%s

You can download the package at:
%s

The change since last build is listed below:
%s

Last part of the build log is followed:
%s

Regards,
Team of Cosmo''' % (build_link, image_path, change_log, failure_log)

        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(0)
    elif (buildresult == "autotest_failure"):
        generate_change_log(last_rev)
        if os.path.isfile(COSMO_CHANGELOG_BUILD):
            infile = open(COSMO_CHANGELOG_BUILD, 'r')
            change_log = infile.read()
            infile.close()
        failure_log = ""
        infile = open(COSMO_DAILY_TEST_LOG, 'r')
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
        subject = "[cosmo-autobuild-%s][%s] Autotest Failed" % (branch, str(date.today()))
        text = '''
This is an automated email from cosmo auto build system. It was
generated because an error encountered while building the code.
The error can be resulted from newly checked in codes.

BuildBot Url:
%s

The change since last build is listed below:
%s

Last part of the build log is followed:
%s

Regards,
Team of Cosmo''' % (build_link, change_log, failure_log)

        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(0)
    else:
        exit(1)

#User help
def usage():
    print "\tpublish_and_sendmail"
#    print "\t      [-r] result <success|failure|nobuild>"
    print "\t      [-h] help"

def main(argv):
    last_rev = ""
    build_nr = ""
    try:
        opts, args = getopt.getopt(argv,"n:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-n"):
            build_nr = arg
    if (build_nr == ""):
        usage()
        sys.exit(2)
    run(get_ret(),build_nr)

if __name__ == "__main__":
    main(sys.argv[1:])

