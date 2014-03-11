#!/usr/bin/python
# v1.1
#    Cosmo Daily Build Script(Cosmo_daily)
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

COSMO_OUT_DIR = "out\\"
IMAGE_SERVER = "\\\\sh-srv06\\cosmo_build\\"
PROJECT = "cosmo"
BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/cosmo_build/builds/"
COSMO_BUILD_LOG = ".cosmo.build.log"
COSMO_CHANGELOG_BUILD = COSMO_OUT_DIR + "changelog.build"
IMAGEDATABASE = "W:"
IMAGEDATABASE_F = "out\\imagedatabase.revision"

#Gerrit admin user
ADM_USER = "buildfarm"

#Gerrit server
GERRIT_SERVER = "privgit.marvell.com"

#Mavell SMTP server
SMTP_SERVER = "10.68.76.51"

#Buildfarm Maintainer
BF_ADMIN = "yfshi@marvell.com"

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def return_mail_text(build_type, branch, build_nr, result, changelog, failurelog=None, image_link=None):
    subject = "[cosmo-autobuild-%s][%s] %s %s" % (branch, str(date.today()), build_type, result)
    message =  "This is an automated email from cosmo auto build system.\n"
    message += "It was generated because %s %s\n\n" % (build_type, result)
    message += "Buildbot Url:\n%s%s\n\n" % (BUILDBOT_URL, build_nr)
    if (result == 'failed'):
        message += "The change since last build is listed below:\n%s\n\n" % changelog
        message += "Last part of the build log is followed:\n%s\n\n" % failurelog
    if (result == 'success'):
        message += "You can download the package at:\n%s\n\n" % (image_link)
        message += "The change since last build is listed below:\n%s\n\n" % changelog
    message +="Regards,\nTeam of Cosmo\n"
    return subject, message

# sync the imagedatabase and return last rev
def sync_imagedatabase():
    p = subprocess.Popen('git fetch origin',shell=True, stdout=subprocess.PIPE, cwd=IMAGEDATABASE)
    (out, nothing) = p.communicate()
    print out
    p = subprocess.Popen('git reset --hard remotes/origin/master', shell=True, stdout=subprocess.PIPE, cwd=IMAGEDATABASE)
    (out, nothing) = p.communicate()
    print out
    p = subprocess.Popen('git log -1 --pretty=format:%H', shell=True, stdout=subprocess.PIPE, cwd=IMAGEDATABASE)
    (out, nothing) = p.communicate()
    return (p.returncode, out.strip())

def get_mail_list(mail_list):
    global ADM_USER
    global GERRIT_SERVER
    email_list = []
    args = "ssh -p 29418 " + ADM_USER + "@" + GERRIT_SERVER + " gerrit gsql -c \"select\ group_id\ from\ account_groups\ WHERE\ name=\\\'" + mail_list + "\\\'\""
    #group_id is the gr_id in the gerrit database where matching PROJECT_GROUP
    group_id = os.popen(args).read().split()[2]
    args = "ssh -p 29418 " + ADM_USER + "@" + GERRIT_SERVER + " gerrit gsql -c \"select\ account_id\ from\ account_group_members\ WHERE\ group_id=\\\'" + group_id + "\\\'\""
    #account_id is the account_id in the gerrit database where matching PROJECT_GROUP
    account_id = os.popen(args).read().split()
    account_id.pop()
    account_id.pop()
    account_id.pop()
    account_id.pop()
    account_id.pop(0)
    account_id.pop(0)
    for i in account_id:
        args = "ssh -p 29418 " + ADM_USER + "@" + GERRIT_SERVER + " gerrit gsql -c \"select\ preferred_email\ from\ accounts\ WHERE\ account_id=\\\'" + i + "\\\'\""
        email_list.append(os.popen(args).read().split()[2])
    return email_list

MAIL_LIST = get_mail_list("cosmo-dev")
#add Simon Kershaw into MAIL_LIST for specical case
MAIL_LIST.append('skershaw@marvell.com')

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

def return_text(changefile):
    change_log = ""
    if os.path.isfile(changefile):
            infile = open(COSMO_CHANGELOG_BUILD, 'r')
            change_log = infile.read()
            infile.close()
    return change_log

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

def run(build_nr=0, branch='master', rev='Release'):
    # git sync (both code and imagedatabase)
    print "[Cosmo-daily][%s] Start git reset --hard %s" % (str(datetime.datetime.now()), branch)
    c_gitfetch = ['git', 'fetch', 'origin']
    ret = os.system(' '.join(c_gitfetch))
    c_resetbranch = ['git', 'reset', '--hard', 'remotes/origin/%s' % branch]
    ret = os.system(' '.join(c_resetbranch))
    if not (ret==0):
        print "[Cosmo-daily][%s] Failed git reset --hard" % (str(datetime.datetime.now()))
        subject, text = return_mail_text('git-reset', branch, build_nr, 'failed', None, None, None)
        send_html_mail(subject,ADM_USER,BF_ADMIN,text)
        exit(1)
    print "[Cosmo-daily][%s] End git reset --hard" % (str(datetime.datetime.now()))
    ret, imagedatabase_rev = sync_imagedatabase()
    if not (ret==0):
        print "[Cosmo-daily][%s] Failed sync imagedatabase" % (str(datetime.datetime.now()))
        subject, text = return_mail_text('sync imagedatabase', branch, build_nr, 'failed', None, None, None)
        send_html_mail(subject,ADM_USER,BF_ADMIN,text)
        exit(1)
    # Generate change log
    print "[Cosmo-daily][%s] Start generate change log" % (str(datetime.datetime.now()))
    last_build = IMAGE_SERVER + "LAST_BUILD."  + branch
    if os.path.isfile(last_build):
        infile = open(last_build, 'r')
        f = infile.read()
        infile.close()
        last_rev = f.split()[0]
    else:
        last_rev = "none"
    current_rev = os.popen("git log -1 --pretty=format:%H").read().split()
    if current_rev[0] == last_rev:
        # Nobuild mail
        subject, text = return_mail_text('[Cosmo-daily]', branch, build_nr, 'nobuild', None, None, None)
        send_html_mail(subject,BF_ADMIN,MAIL_LIST,text)
        exit(0)
    c_gcl = ['..\\build_script\\core\\generate_change_log.py -r %s' % last_rev]
    ret = os.system(' '.join(c_gcl))
    if not (ret==0):
        print "[Cosmo-daily][%s] Failed generate change log" % (str(datetime.datetime.now()))
        subject, text = return_mail_text('[Generate-change-log]', branch, build_nr, 'failed', None, None, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    if imagedatabase_rev:
            f = open(IMAGEDATABASE_F, 'w')
            f.write("ImageDataBase Rev: %s" % imagedatabase_rev)
            f.close()
    print "[Cosmo-daily][%s] End generate change log" % (str(datetime.datetime.now()))
    # MSBuild
    print "[Cosmo-daily][%s] Start MSBuild" % (str(datetime.datetime.now()))
    c_msbuild = ['MSBuild', 'Cosmo.sln', '/t:Rebuild', '/p:Configuration=Release']
    ret = os.system(' '.join(c_msbuild))
    if not (ret==0):
        print "[Cosmo-daily][%s] Failed MSBuild" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(COSMO_BUILD_LOG)
        change_log = return_text(COSMO_CHANGELOG_BUILD)
        subject, text = return_mail_text('[MSBuild]', branch, build_nr, 'failed', change_log, failure_log, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    print "[Cosmo-daily][%s] End MSBuild" % (str(datetime.datetime.now()))
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
    print "[Cosmo-daily][%s] Start calib" % (str(datetime.datetime.now()))
    c_calib = ['..\\build_script\\core\\mulit_core_task_run.py -c "..\\bin\\cosmo.exe" -l "%s"' % (','.join(calib_commands))]
    ret = os.system(' '.join(c_calib))
    if not (ret==0):
        print "[Cosmo-daily][%s] Failed calib" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(COSMO_BUILD_LOG)
        change_log = return_text(COSMO_CHANGELOG_BUILD)
        subject, text = return_mail_text('[Package-calib]', branch, build_nr, 'failed', change_log, failure_log, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    # auto test simu
    print "[Cosmo-daily][%s] Start simu" % (str(datetime.datetime.now()))
    c_simu = ['..\\build_script\\core\\mulit_core_task_run.py -c "..\\bin\\cosmo.exe" -l "%s"' % (','.join(simu_commands))]
    ret = os.system(' '.join(c_simu))
    if not (ret==0):
        print "[Cosmo-daily][%s] Failed simu" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(COSMO_BUILD_LOG)
        change_log = return_text(COSMO_CHANGELOG_BUILD)
        subject, text = return_mail_text('[Package-simu]', branch, build_nr, 'failed', change_log, failure_log, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    # Publishing
    print "[Cosmo-daily][%s] Start Publishing" % (str(datetime.datetime.now()))
    publish_folder = check_publish_folder(IMAGE_SERVER, branch)
    c_publishing = ['..\\build_script\\core\\publish_results.py']
    c_publishing.append('-s %s' % COSMO_OUT_DIR)
    c_publishing.append('-d %s' % IMAGE_SERVER)
    c_publishing.append('-r %s' % publish_folder)
    ret = os.system(' '.join(c_publishing))
    if not (ret==0):
        print "[Cosmo-daily][%s] Failed Publishing" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(COSMO_BUILD_LOG)
        change_log = return_text(COSMO_CHANGELOG_BUILD)
        subject, text = return_mail_text('[Package-publishing]', branch, build_nr, 'failed', change_log, failure_log, None)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    # All Success
    current_rev = os.popen("git log -1 --pretty=format:%H").read().split()
    if current_rev:
            f = open(last_build, 'w')
            f.write("%s\nPackage: %s\nImageDataBase Rev: %s" % (current_rev[0], publish_folder, imagedatabase_rev))
            f.close()
    print "[Cosmo-daily][%s] End Autotest" % (str(datetime.datetime.now()))
    print "[Cosmo-daily][%s] All success" % (str(datetime.datetime.now()))
    change_log = return_text(COSMO_CHANGELOG_BUILD)
    subject, text = return_mail_text('[Cosmo-daily]', branch, build_nr, 'success', change_log, None, publish_folder)
    send_html_mail(subject,ADM_USER,MAIL_LIST,text)
    exit(0)

#User help
def usage():
    print "\tCosmo_daily.py"
    print "\t      [-n] build nr from buildbot"
    print "\t      [-b] event.change.branch"
    print "\t      [-r] rev {Release|Debug}"
    print "\t      [-h] help"

def main(argv):
    build_nr = ""
    branch = ""
    rev = ""
    try:
        opts, args = getopt.getopt(argv,"r:n:b:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-r"):
            rev = arg
        elif opt in ("-n"):
            build_nr = arg
        elif opt in ("-b"):
            branch = arg.split('/')[0]
    if not build_nr or not branch:
        usage()
        sys.exit(2)

    run(build_nr, branch)

if __name__ == "__main__":
    main(sys.argv[1:])

