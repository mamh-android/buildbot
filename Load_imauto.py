#!/usr/bin/python
# v1.0
#    Image Auto Test Script(IMAUTO)
#    Author: yfshi@marvell.com

import os
import sys
import getopt
import datetime
from datetime import date
import glob
import smtplib
import ConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/image_auto_test/builds/"
IMAUTO_LOG = ".imauto.build.log"
TEST_CFG = "test.txt"

#Gerrit admin user
ADM_USER = "buildfarm"

#Gerrit server
GERRIT_SERVER = "privgit.marvell.com"

#Mavell SMTP server
SMTP_SERVER = "10.68.76.51"

#Buildfarm Maintainer
BF_ADMIN = "yfshi@marvell.com"
CAM_QAE_ADMIN = "yzhan45@marvell.com"

#Mail list
MAIL_LIST = []
MAIL_LIST.append(CAM_QAE_ADMIN)

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def return_mail_text(build_type, branch, build_nr, result, failurelog, cfg_file, image_link=None):
    subject = "[imauto-%s][%s] %s %s" % (branch, str(date.today()), build_type, result)
    message =  "This is an automated email from auto build system.\n"
    message += "It was generated because %s %s\n\n" % (build_type, result)
    message += "Buildbot Url:\n%s%s\n\n" % (BUILDBOT_URL, build_nr)
    if (result == 'failed'):
        message += "CFG file is followed:\n%s\n\n" % cfg_file
        message += "Last part of the build log is followed:\n%s\n\n" % failurelog
    if (result == 'success'):
        message += "CFG file is followed:\n%s\n\n" % cfg_file
        message += "You can download the package at:\n%s\n\n" % (image_link)
    message +="Regards,\nTeam of CameraQAE\n"
    return subject, message

def send_html_mail(subject, from_who, to_who, text):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_who
    msg['To'] = ", ".join(to_who)
    part1 = MIMEText(text, 'plain')
    msg.attach(part1)
    s = smtplib.SMTP(SMTP_SERVER)
    s.sendmail(from_who, to_who, msg.as_string())
    s.quit()

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

def setup_testfile(filename, path, sensor, resolution, focus, testimage=None, isp=None, FWVersion=None, CalVersion=None):
    config = ConfigParser.RawConfigParser()
    config.add_section('optional')
    config.set('optional', 'Testimage', testimage)
    config.set('optional', 'ISP', isp)
    config.set('optional', 'FWVersion', FWVersion)
    config.set('optional', 'CalVersion', CalVersion)
    config.add_section('mandatory')
    config.set('mandatory', 'Path', path)
    config.set('mandatory', 'Sensor', sensor)
    config.set('mandatory', 'Resolution', resolution)
    config.set('mandatory', 'Focus', focus)
    # Writing our configuration file to 'example.cfg'
    with open(filename, 'w') as configfile:
        config.write(configfile)

def run(build_nr, cfg_file, image_link, run_type='1', branch='master'):
    # git reset --hard branch
    print "[imauto][%s] Start git reset --hard %s" % (str(datetime.datetime.now()), branch)
    c_gitfetch = ['git', 'fetch', 'origin']
    ret = os.system(' '.join(c_gitfetch))
    c_resetbranch = ['git', 'reset', '--hard', 'origin/%s' % branch]
    ret = os.system(' '.join(c_resetbranch))
    if not (ret==0):
        print "[imauto][%s] Failed git reset --hard" % (str(datetime.datetime.now()))
        subject, text = return_mail_text('git-reset', branch, build_nr, 'failed', None, None, None)
        send_html_mail(subject,ADM_USER,BF_ADMIN.split(),text)
        exit(1)
    print "[imauto][%s] End git reset --hard" % (str(datetime.datetime.now()))
    # imauto run
    print "[imauto][%s] Start imauto" % (str(datetime.datetime.now()))
    c_imauto = ['perl test.pl %s %s' % (cfg_file, run_type)]
    ret = os.system(' '.join(c_imauto))
    if not (ret==0):
        print "[imauto][%s] Failed imauto" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(IMAUTO_LOG)
        cfg_file = return_failure_log(TEST_CFG)
        subject, text = return_mail_text('[imauto]', branch, build_nr, 'failed', failure_log, cfg_file,None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    # All success
    print "[imauto][%s] End Autotest" % (str(datetime.datetime.now()))
    print "[imauto][%s] All success" % (str(datetime.datetime.now()))
    cfg_file = return_failure_log(TEST_CFG)
    subject, text = return_mail_text('[imauto]', branch, build_nr, 'success', None, cfg_file, image_link)
    send_html_mail(subject,ADM_USER,MAIL_LIST,text)
    exit(0)

#User help
def usage():
    print "\timauto.py"
    print "\t      [mandatory] section"
    print "\t      [-p] Path sample: \\\\10.38.34.209\\home\\home\\wangnian\\git_folder\\multimedia_testsuite\\tools\\IMAUTO\\OriImg"
    print "\t      [-s] Sensor {3H5#8}"
    print "\t      [-r] Resolution {8M|2M|5M|8M|13M}"
    print "\t      [-f] Focus {AF|FF}"
    print "\t      [-n] build_nr"
    print "\t      [optional] section"
    print "\t      [-b] imauto branch defult=master"
    print "\t      [-t] TestImage sample: 2014-02-18_pxa988-kk4.4"
    print "\t      [-i] ISP {Dx0}"
    print "\t      [-w] FWVersion {0215delivery}"
    print "\t      [-c] CalVersion {0215delivery}"
    print "\t      [-m] email for notification"
    print "\t      [-h] help"

def main(argv):
    path = ""
    sensor = ""
    resolution = ""
    focus = ""
    build_nr = ""
    branch = ""
    testimage = ""
    isp = ""
    fwversion = ""
    calversion = ""
    email = ""
    try:
        opts, args = getopt.getopt(argv,"p:s:r:f:n:b:t:i:w:c:m:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-p"):
            path = arg
        elif opt in ("-s"):
            sensor = arg
        elif opt in ("-r"):
            resolution = arg
        elif opt in ("-f"):
            focus = arg
        elif opt in ("-n"):
            build_nr = arg
        elif opt in ("-b"):
            branch = arg
        elif opt in ("-t"):
            testimage = arg
        elif opt in ("-i"):
            isp = arg
        elif opt in ("-w"):
            fwversion = arg
        elif opt in ("-c"):
            calversion = arg
        elif opt in ("-m"):
            email = arg
            MAIL_LIST.append(email)

    if not path or not sensor or not resolution or not focus:
        usage()
        sys.exit(2)

    setup_testfile(TEST_CFG, path, sensor, resolution, focus, testimage, isp, fwversion, calversion)
    run(build_nr, TEST_CFG, path, '1')

if __name__ == "__main__":
    main(sys.argv[1:])

