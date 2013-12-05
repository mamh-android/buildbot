#!/usr/bin/python
# v1.0
#    publishing and send mail script
#    Author: yfshi@marvell.com


import os
import sys
#import core script
sys.path.append("/home/yfshi/workspace/cosmo_build/buildscript/core")
from generate_change_log import *
from send_mail import *
from publish_to_image_server import *

COSMO_OUT_DIR="/tmp/cosmo/out/"
IMAGE_SERVER="/tmp/image_server/"
MAIL_LIST = get_mail_list("gr_notice_mail")

def run(rev, buildresult):
    global MAIL_LIST
    if (buildresult == "success"):
        generate_change_log(rev)
        image_path = publish_file(COSMO_OUT_DIR, IMAGE_SERVER)
        send_html_mail("It's just a test, build success",ADM_USER,MAIL_LIST,buildresult, image_path)
    elif (buildresult == "failure"):
        send_html_mail("It's just a test, build failed",ADM_USER,MAIL_LIST,buildresult, "")
    else:
        print "~~<result>PASS</result>"
        print "~~<result-details>No build</result-details>"

#User help
def usage():
    print "\tpublish_and_sendmail [-p] last_patch_rev"
    print "\t      [-r] result <success|failure|nobuild>"
    print "\t      [-h] help"

def main(argv):
    last_rev = ""
    build_result = ""
    try:
        opts, args = getopt.getopt(argv,"p:r:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-p"):
            last_rev = arg
        elif opt in ("-r"):
            build_result = arg
    if (last_rev == "") or (build_result == ""):
        usage()
        sys.exit(2)
    else:
        run(last_rev,build_result)

if __name__ == "__main__":
    main(sys.argv[1:])

