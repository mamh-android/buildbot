#!/usr/bin/python
# v1.0
#    Load ipp autobuild
#    Author: yfshi@marvell.com

import os
import sys
import getopt
import subprocess
import datetime
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BUILD_LOG = ".core.build.log"
IPP_REPO_URL = "ssh://shgit/git/android/shared/mrvl_extractor.git"
BUILD_STDIO = "/home/buildfarm/buildbot_script/stdio.log"
AABS_FOLDER = "/home/buildfarm/aabs"

# Gerrit admin user
ADM_USER = "buildfarm"

# Mavell SMTP server
SMTP_SERVER = "10.68.76.51"

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def return_mail_text(build_type, branch, result, failurelog=None):
    subject = "[ipp-autobuild-%s][%s] %s %s" % (branch, str(date.today()), build_type, result)
    message =  "This is an automated email from auto build system.\n"
    message += "It was generated because %s %s\n\n" % (build_type, result)
    if (result == 'failed'):
        message += "Last part of the build log is followed:\n%s\n\n" % failurelog
    if (result == 'success'):
        message += "You can download the package at:\n%s\n\n"
    message +="Regards,\nBuildfarm\n"
    return subject, message

# sync the build code
def sync_build_code(repo_url):
    repo_folder = repo_url.split('.')[0].split('/')[len(repo_url.split('/'))-1]
    if not os.path.isdir(repo_folder):
        subprocess.check_call('git clone %s' % repo_url, shell=True)
    else:
        subprocess.check_call('git fetch', shell=True, cwd=repo_folder)
        subprocess.check_call('git reset --hard master', shell=True, cwd=repo_folder)
        subprocess.check_call('git checkout master', shell=True, cwd=repo_folder)
    return "%s/%s" % (os.getcwd(), repo_folder)

def get_mail_list(maintainer_f):
    #email_list = open('/tmp/mrvl_extractor/maintainer', 'r').read().split()
    email_list = open("%s/maintainer" % maintainer_f, 'r').read().split()
    return email_list


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

def run(branch='master'):
    # ipp git sync
    print "[Ipp-build][%s] Start sync mrvl_extractor" % str(datetime.datetime.now())
    mrvl_extractor_folder = sync_build_code(IPP_REPO_URL)
    MAIL_LIST = get_mail_list(mrvl_extractor_folder)
    print "[Ipp-build][%s] End sync" % (str(datetime.datetime.now()))
    # Set env
    product = return_last_device(BUILD_STDIO, 'TARGET_PRODUCT')
    variant = return_last_device(BUILD_STDIO, 'TARGET_BUILD_VARIANT')
    if branch.split('_')[0] == 'rls':
       src_dir = "src.%s-%s.%s" % (branch.split('_')[1], branch.split('_')[2], branch.lstrip('%s_%s_%s' % (branch.split('_')[0], branch.split('_')[1], branch.split('_')[2])))
    else:
       src_dir = "src.%s" % branch.replace('_', '-')
    src_dir_r = AABS_FOLDER + '/' + src_dir
    subprocess.check_call('repo sync', shell=True, cwd=src_dir_r)
    # Start ipp build
    print "[Ipp-build][%s] Start load core.sh" % (str(datetime.datetime.now()))
    os.chdir(src_dir_r)
    c_build = ['%s/core.sh' % mrvl_extractor_folder, branch, '%s-%s' % (product, variant)]
    ret = os.system(' '.join(c_build))
    if not (ret==0):
        print "[Ipp-build][%s] Failed Build" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(BUILD_LOG)
        subject, text = return_mail_text('[Ipp-build]', branch, 'failed', failure_log)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    print "[Ipp-build][%s] End Build" % (str(datetime.datetime.now()))
    # All Success
    print "[Ipp-build][%s] All success" % (str(datetime.datetime.now()))
    failure_log = return_failure_log(BUILD_LOG)
    subject, text = return_mail_text('[Ipp-build]', branch, 'success', failure_log)
    send_html_mail(subject,ADM_USER,MAIL_LIST,text)
    exit(0)

#User help
def usage():
    print "\tLoad_core.py"
    print "\t      [-b] branch"
    print "\t      [-h] help"

def main(argv):
    branch = ""
    try:
        opts, args = getopt.getopt(argv,"b:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-b"):
            branch = arg
    if not branch:
        usage()
        sys.exit(2)

    run(branch)

if __name__ == "__main__":
    main(sys.argv[1:])

