#!/usr/bin/python

# v1.0
#    Cosmo On Demaind Tuning (cosmo ODT)
#    Author: yfshi@marvell.com

import os
import sys
import getopt
import subprocess
import datetime
from datetime import date
import glob
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import shutil

COSMO_OUT_DIR = "out\\"
IMAGE_SERVER = "\\\\sh-srv06\\cosmo_build\\"
ODT_SERVER = "\\\\sh-srv06\\cosmo_odt\\"
PROJECT = "cosmo-odt"
BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/cosmo_odt/builds/"
COSMO_BUILD_LOG = ".cosmo.build.log"
IMAGEDATABASE = "W:"
IMAGEDATABASE_L = "\\\\sh-srv06\\common\\"

#Gerrit admin user
ADM_USER = "buildfarm"

#Gerrit server
GERRIT_SERVER = "privgit.marvell.com"

#Mavell SMTP server
SMTP_SERVER = "10.68.76.51"

#Buildfarm Maintainer
BF_ADMIN = "yfshi@marvell.com"

#MAIL_LIST
MAIL_LIST = []

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def return_mail_text(build_type, branch, build_nr, result, failurelog=None, image_link=None):
    subject = "[cosmo-odt-%s][%s] %s %s" % (branch, str(date.today()), build_type, result)
    message =  "This is an automated email from cosmo auto build system.\n"
    message += "It was generated because %s was %s\n\n" % (build_type, result)
    message += "Buildbot Url:\n%s%s\n\n" % (BUILDBOT_URL, build_nr)
    if (result == 'failed'):
        message += "Last part of the build log is followed:\n%s\n\n" % failurelog
    if (result == 'success'):
        message += "You can get the OutputImages at:\n%s\\OutputImages\n\n" % (image_link)
    message +="Regards,\nTeam of Cosmo\n"
    return subject, message

# sync the imagedatabase and return last rev
def sync_imagedatabase():
    os.system("net use")
    if not os.path.isdir(IMAGEDATABASE):
        os.system("net use %s %s" % (IMAGEDATABASE, IMAGEDATABASE_L))
    p = subprocess.Popen('git fetch origin',shell=True, stdout=subprocess.PIPE, cwd=IMAGEDATABASE)
    (out, nothing) = p.communicate()
    print out
    p = subprocess.Popen('git reset --hard remotes/origin/master', shell=True, stdout=subprocess.PIPE, cwd=IMAGEDATABASE)
    (out, nothing) = p.communicate()
    print out
    p = subprocess.Popen('git log -1 --pretty=format:%H', shell=True, stdout=subprocess.PIPE, cwd=IMAGEDATABASE)
    (out, nothing) = p.communicate()
    return (p.returncode, out.strip())

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

#setup tuning env
def setup_env(datafolder):
    # remove all the xml sim
    xml_file = glob.glob("xml\\*.xml")
    for i in xml_file:
        os.remove(i)
    sim_file = glob.glob("test\\*.sim")
    for i in sim_file:
        os.remove(i)
    #copy xml and sim
    xml_file = glob.glob("%s\\*.xml" % datafolder)
    for i in xml_file:
        p = "copy file: " + i + "-->" + "xml\\."
        print p
        shutil.copy2(i, "xml\\.")
    sim_file = glob.glob("%s\\*.sim" % datafolder)
    for i in sim_file:
        p = "copy file: " + i + "-->" + "test\\."
        print p
        shutil.copy2(i, "test\\.")

#create a valued folder according email and time.today
def check_publish_folder(SERVER, useremail):
    today = date.today()
    folder = useremail + '_' + str(today)
    folder_server = SERVER + folder
    f = folder_server
    if not os.path.isdir(f):
        os.mkdir(f)
        return f
    else:
        i=1
        while os.path.isdir(folder_server):
            f = folder_server + "_" + str(i)
            if not os.path.isdir(f):
                os.mkdir(f)
                return f
                break
            else:
                i=i+1

def run(build_nr, branch, datafolder, email):
    # git sync (both code and imagedatabase)
    print "[Cosmo-odt][%s] Start git reset --hard %s" % (str(datetime.datetime.now()), branch)
    c_gitfetch = ['git', 'fetch', 'origin']
    ret = os.system(' '.join(c_gitfetch))
    c_resetbranch = ['git', 'reset', '--hard', 'remotes/origin/%s' % branch]
    ret = os.system(' '.join(c_resetbranch))
    if not (ret==0):
        print "[Cosmo-odt][%s] Failed git reset --hard" % (str(datetime.datetime.now()))
        subject, text = return_mail_text('git-reset', branch, build_nr, 'failed', None, None)
        send_html_mail(subject,ADM_USER,BF_ADMIN,text)
        exit(1)
    print "[Cosmo-odt][%s] End git reset --hard" % (str(datetime.datetime.now()))
    ret, imagedatabase_rev = sync_imagedatabase()
    if not (ret==0):
        print "[Cosmo-odt][%s] Failed sync imagedatabase" % (str(datetime.datetime.now()))
        subject, text = return_mail_text('sync imagedatabase', branch, build_nr, 'failed', None, None)
        send_html_mail(subject,ADM_USER,BF_ADMIN,text)
        exit(1)
    # MSBuild release
    print "[Cosmo-odt][%s] Start MSBuild release" % (str(datetime.datetime.now()))
    c_msbuild = ['MSBuild', 'Cosmo.sln', '/t:Rebuild', '/p:Configuration=Release']
    ret = os.system(' '.join(c_msbuild))
    if not (ret==0):
        print "[Cosmo-odt][%s] Failed MSBuild release" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(COSMO_BUILD_LOG)
        subject, text = return_mail_text('[MSBuild]', branch, build_nr, 'failed', failure_log, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    print "[Cosmo-odt][%s] End MSBuild release" % (str(datetime.datetime.now()))
    # Setup tuning env
    # 1. remove all the xml and sim in build package
    # 2. copy masse tuning *.xml and *.sim from datafolder
    print "[Cosmo-odt][%s] Start Setup env" % (str(datetime.datetime.now()))
    setup_env(datafolder)
    print "[Cosmo-odt][%s] End Setup env" % (str(datetime.datetime.now()))
    # Load all calib and simu from xml and test
    calib_commands = []
    xml_file = glob.glob("xml\\*.xml")
    for i in xml_file:
        calib_commands.append("-c ..\\%s" % (i))
    simu_commands = []
    sim_file = glob.glob("test\\*.sim")
    for i in sim_file:
        simu_commands.append("-s ..\\%s" % (i))
    # auto test calib
    print "[Cosmo-odt][%s] Start calib" % (str(datetime.datetime.now()))
    c_calib = ['..\\build_script\\core\\mulit_core_task_run.py -c "..\\bin\\cosmo.exe" -l "%s"' % (','.join(calib_commands))]
    ret = os.system(' '.join(c_calib))
    if not (ret==0):
        print "[Cosmo-odt][%s] Failed calib" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(COSMO_BUILD_LOG)
        subject, text = return_mail_text('[Package-calib]', branch, build_nr, 'failed', failure_log, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    # auto test simu
    print "[Cosmo-odt][%s] Start simu" % (str(datetime.datetime.now()))
    c_simu = ['..\\build_script\\core\\mulit_core_task_run.py -c "..\\bin\\cosmo.exe" -l "%s"' % (','.join(simu_commands))]
    ret = os.system(' '.join(c_simu))
    if not (ret==0):
        print "[Cosmo-odt][%s] Failed simu" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(COSMO_BUILD_LOG)
        subject, text = return_mail_text('[Package-simu]', branch, build_nr, 'failed', failure_log, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    # Publishing
    print "[Cosmo-odt][%s] Start Publishing" % (str(datetime.datetime.now()))
    output_path = check_publish_folder(ODT_SERVER, email)
    #publish xml and sim
    xml_file = glob.glob("%s\\*.xml" % datafolder)
    for i in xml_file:
        shutil.copy2(i, "%s\\." % output_path)
    sim_file = glob.glob("%s\\*.sim" % datafolder)
    for i in sim_file:
        shutil.copy2(i, "%s\\." % output_path)
    #publish outputimages
        shutil.copytree("test\\OutputImages", "%s\\OutputImages" % output_path)
    print "[Cosmo-odt][%s] End Publishing" % (str(datetime.datetime.now()))
    # All Success
    print "[Cosmo-odt][%s] All success" % (str(datetime.datetime.now()))
    subject, text = return_mail_text('[Cosmo-odt]', branch, build_nr, 'success', None, output_path)
    send_html_mail(subject,ADM_USER,MAIL_LIST,text)
    exit(0)

#User help
def usage():
    print "\tCosmo_odt.py"
    print "\t      [-n] build nr from buildbot"
    print "\t      [-b] branch"
    print "\t      [-f] datafolder"
    print "\t      [-m] useremail who triggered test"
    print "\t      [-h] help"

def main(argv):
    build_nr = ""
    branch = ""
    datafolder = ""
    useremail = ""
    try:
        opts, args = getopt.getopt(argv,"n:b:f:m:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-n"):
            build_nr = arg
        elif opt in ("-b"):
            branch = arg
        elif opt in ("-f"):
            datafolder = arg
        elif opt in ("-m"):
            useremail = arg
            MAIL_LIST.append(useremail)
    if not build_nr or not branch:
        usage()
        sys.exit(2)

    run(build_nr, branch, datafolder, useremail)

if __name__ == "__main__":
    main(sys.argv[1:])

