#!/usr/bin/python
# v1.0
#    cp from Image Auto Test Script(IMAUTO)
#    the script will be triggered depends on cosmo build results
#    Author: yfshi@marvell.com

import os
import sys
import getopt
import datetime
from datetime import date
import glob
import shutil
import smtplib
import ConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/cosmo_image_auto_test/builds/"
IMAUTO_LOG = ".imauto.build.log"
TEST_CFG = "test.txt"
IMAGE_SERVER = "\\\\sh-srv06\\cosmo_build\\"
OUTPUTIMAGES = "\\cosmobuild\\test\\OutputImages\\"
OUTPUT_IMAUTO_SERVER = "\\\\sh-srv06\\cosmo_imauto\\"
BUILD_TYPE = "cosmo-imauto"

#Gerrit admin user
ADM_USER = "buildfarm"

#Gerrit server
GERRIT_SERVER = "privgit.marvell.com"

#Mavell SMTP server
SMTP_SERVER = "10.68.76.51"

#Buildfarm Maintainer
BF_ADMIN = "yfshi@marvell.com"

#Mail list
MAIL_LIST = []
MAIL_LIST.append(BF_ADMIN)

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def return_mail_text(build_type, branch, build_nr, result, failurelog, image_link=None):
    subject = "[imauto-%s][%s] %s %s" % (branch, str(date.today()), build_type, result)
    message =  "This is an automated email from auto build system.\n"
    message += "It was generated because %s was %s\n\n" % (build_type, result)
    message += "Buildbot Url:\n%s%s\n\n" % (BUILDBOT_URL, build_nr)
    if (result == 'failed'):
        message += "Last part of the build log is followed:\n%s\n\n" % failurelog
    if (result == 'success'):
        message += "You get imauto report at:\n"
        for r in image_link:
            message += "%s\n" % r
        message += "\n\n"
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

# return *_imauto test list from the last successful build
def return_last_image_imauto(branch):
    f = open('%sLAST_BUILD.%s' % (IMAGE_SERVER, branch), 'r')
    l = f.readlines()
    f.close()
    last_package = l[1].split()[1]
    print last_package
    imauto_l = glob.glob("%s%s*_imauto" % (last_package, OUTPUTIMAGES))
    print imauto_l
    return imauto_l

#create a folder according to git branch name and time.today
def check_publish_folder(IMAGE_SERVER, branch):
    today = date.today()
    folder = str(today) + "_" + branch
    folder_server = IMAGE_SERVER + folder
    f = folder_server
    if not os.path.isdir(f):
        #os.mkdir(f)
        return f
    else:
        i=1
        while os.path.isdir(folder_server):
            f = folder_server + "_" + str(i)
            if not os.path.isdir(f):
                #os.mkdir(f)
                return f
                break
            else:
                i=i+1

# copy OutputImages *_imauto to OUTPUT_IMAUTO_SERVER
def copy_outputimage(src, out):
    dst = "%s\\%s" % (out, src.split('\\')[len(src.split('\\'))-1])
    shutil.copytree(src,dst)
    return dst

def setup_testfile(filename, path, sensor=None, resolution=None, focus=None, testimage=None, isp=None, FWVersion=None, CalVersion=None):
    config = ConfigParser.RawConfigParser()
    config.add_section('optional')
    config.set('optional', 'Testimage', testimage)
    config.set('optional', 'ISP', isp)
    config.set('optional', 'FWVersion', FWVersion)
    config.set('optional', 'CalVersion', CalVersion)
    config.add_section('mandatory')
    if ' ' in path:
        config.set('mandatory', 'Path', ("\"%s\"") % path)
    else:
        config.set('mandatory', 'Path', ("%s") % path)
    config.set('mandatory', 'Sensor', sensor)
    config.set('mandatory', 'Resolution', resolution)
    config.set('mandatory', 'Focus', focus)
    # Writing our configuration file to 'example.cfg'
    with open(filename, 'w') as configfile:
        config.write(configfile)

def run(cfg_file, run_type='1', branch='master'):
    # git reset --hard branch
    print "[%s][%s] Start git reset --hard %s" % (BUILD_TYPE, str(datetime.datetime.now()), branch)
    c_gitfetch = ['git', 'fetch', 'origin']
    ret = os.system(' '.join(c_gitfetch))
    c_resetbranch = ['git', 'reset', '--hard', 'origin/%s' % branch]
    ret = os.system(' '.join(c_resetbranch))
    if not (ret==0):
        print "[%s][%s] Failed git reset --hard" % (BUILD_TYPE, str(datetime.datetime.now()))
        subject, text = return_mail_text('git-reset', branch, build_nr, 'failed', None, None, None)
        send_html_mail(subject,ADM_USER,BF_ADMIN.split(),text)
        exit(1)
    print "[%s][%s] End git reset --hard" % (BUILD_TYPE, str(datetime.datetime.now()))
    # imauto run
    print "[%s][%s] Start imauto" % (BUILD_TYPE, str(datetime.datetime.now()))
    c_imauto = ['perl test.pl %s %s' % (cfg_file, run_type)]
    print c_imauto
    ret = os.system(' '.join(c_imauto))
    if not (ret==0):
        print "[%s][%s] Failed imauto" % (BUILD_TYPE, str(datetime.datetime.now()))
    # All success
    print "[%s][%s] End Autotest" % (BUILD_TYPE, str(datetime.datetime.now()))
    return ret

def send_mail(ret, image_link, branch, build_nr):
    if not (ret==0):
        failure_log = return_failure_log(IMAUTO_LOG)
        subject, text = return_mail_text('image-auto-test', branch, build_nr, 'failed', failure_log, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    # All success
    print "[%s][%s] All success" % (BUILD_TYPE, str(datetime.datetime.now()))
    subject, text = return_mail_text('image-auto-test', branch, build_nr, 'success', None, image_link)
    send_html_mail(subject,ADM_USER,MAIL_LIST,text)
    exit(0)

#User help
def usage():
    print "\tdepend cosmo build imauto"
    print "\t      [-b] branch"
    print "\t      [-m] email for notification"
    print "\t      [-h] help"

def main(argv):
    branch = ""
    email = ""
    build_nr = ""
    try:
        opts, args = getopt.getopt(argv,"b:n:m:h")
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
        elif opt in ("-m"):
            email = arg
            MAIL_LIST.append(email)

    if not branch:
        usage()
        sys.exit(2)

    var_path = check_publish_folder(OUTPUT_IMAUTO_SERVER, branch)
    print var_path
    outputimage_l = return_last_image_imauto(branch)
    result_l = []
    ret = 0
    for i in outputimage_l:
        path = copy_outputimage(i, var_path)
        setup_testfile(TEST_CFG, path, path.split('\\')[len(path.split('\\'))-1].replace('_imauto', ''), '5M', None, None, i)
        ret += run(TEST_CFG, '2', branch)
        result_l.extend(glob.glob('%s\\result*\\Report\\*.xml' % path))
    send_mail(ret, result_l, branch, build_nr)

if __name__ == "__main__":
    main(sys.argv[1:])

