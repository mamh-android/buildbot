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
MAIL_LIST = get_mail_list("gr_notice_mail")

def run(buildresult):
    global MAIL_LIST
    global COSMO_OUT_DIR
    global IMAGE_SERVER
    if (buildresult == "success"):
        branch = os.popen("git branch").read().split()[1]
        last_build = IMAGE_SERVER + "LAST_BUILD."  + branch
        if os.path.isfile(last_build):
            f = open(last_build, 'r')
            last_rev = f.readline().strip()
            f.close()
        else:
            last_rev = ""
        current_rev = os.popen("git log -1 " + branch + " --pretty=format:%H").read().split()
        generate_change_log(last_rev)
        image_path = publish_file(COSMO_OUT_DIR, IMAGE_SERVER)
        send_html_mail("It's just a test, build success",ADM_USER,MAIL_LIST,buildresult, image_path)
        if current_rev:
            f = open(last_build, 'w')
            f.write(current_rev[0])
            f.close()
    elif (buildresult == "failure"):
        send_html_mail("It's just a test, build failed",ADM_USER,MAIL_LIST,buildresult, "")
    else:
        print "~~<result>PASS</result>"
        print "~~<result-details>No build</result-details>"
        exit(0)

#User help
def usage():
    print "\tpublish_and_sendmail"
    print "\t      [-r] result <success|failure|nobuild>"
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
    if (build_result == ""):
        usage()
        sys.exit(2)
    else:
        run(build_result)

if __name__ == "__main__":
    main(sys.argv[1:])

