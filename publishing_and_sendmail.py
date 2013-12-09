#!/usr/bin/python
# v1.0
#    publishing and send mail script
#    Author: yfshi@marvell.com


import os
import sys
#import core script
sys.path.append("..\\build_script\\core")
from generate_change_log import *
from send_mail import *
from publish_to_image_server import *

COSMO_OUT_DIR="out\\"
IMAGE_SERVER="\\\\sh-srv06\\cosmo_build\\"
MAIL_LIST = get_mail_list("cosmo-dev")
COSMO_BUILD_LOG=".cosmo.build.log"

def get_ret(build_log):
    global COSMO_BUILD_LOG
    infile = open(COSMO_BUILD_LOG,"r")
    text = infile.read()
    infile.close()
    search = "    0 Error(s)"
    index = text.find(search)
    if not index == (-1):
        buildresult = "success"
    else:
        buildresult = "failure"
    return buildresult

def run(buildresult):
    global MAIL_LIST
    global COSMO_OUT_DIR
    global IMAGE_SERVER
    branch = os.popen("git branch").read().split()[1]
    last_build = IMAGE_SERVER + "LAST_BUILD."  + branch
    if os.path.isfile(last_build):
        infile = open(last_build, 'r')
        f = infile.read()
        infile.close()
        last_rev = f
    else:
        last_rev = ""
    current_rev = os.popen("git log -1 " + branch + " --pretty=format:%H").read().split()
    if current_rev[0] == last_rev:
        subject = "[cosmo-auto-build] [" + str(date.today()) + "] Nobuild"
        text = "This is an automated email from the autobuild script. The \
email was generated because the script detects no significant change in \
source code since last build.\n\
\n=============================================================\n\
Team of APSE\n"
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        print "~~<result>PASS</result>"
        print "~~<result-details>No build</result-details>"
        exit(255)
    elif (buildresult == "success"):
        generate_change_log(last_rev)
        image_path = publish_file(COSMO_OUT_DIR, IMAGE_SERVER)
        subject = "[cosmo-auto-build] [" + str(date.today()) + "] Success"
        text = "This is an automated email from the autobuild script. It was \
generated because a new package is generated successfully and \
the package is changed since last day.\n\
You can get the package from:\n" + image_path + "\n=============================================================\n\
Team of APSE\n"
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        if current_rev:
            f = open(last_build, 'w')
            f.write(current_rev[0])
            f.close()
            print "Publish is done"
            print "~~<result>PASS</result>"
            print "~~<result-dir>" + image_path + "</result-dir>"
        exit(0)
    elif (buildresult == "failure"):
        subject = "[cosmo-auto-build] [" + str(date.today()) + "] Failed"
        text = "This is an automated email from the autobuild script. It was \
generated because an error encountered while building the code. \
The error can be resulted from newly checked in codes.\n\
\n=============================================================\n\
Team of APSE\n"
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
    build_result = ""
    try:
        opts, args = getopt.getopt(argv,"r:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-r"):
            build_result = arg
    run(get_ret(COSMO_BUILD_LOG))

if __name__ == "__main__":
    main(sys.argv[1:])

