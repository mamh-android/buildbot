#!/usr/bin/python
# v1.1
#    Load ipp autobuild

import os
import sys
import getopt
import shutil
import subprocess
import datetime
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BUILD_LOG = ".wfd_core.build.log"
BSCRIPT = "wfd_core.sh"
BMAINTAINERS = "wfd_maintainer"
BBRANCH = "wfd_release_branch_list"
IPP_REPO_URL = "ssh://shgit.marvell.com/git/android/shared/mrvl_extractor.git"
BUILD_STDIO = "/home/buildfarm/buildbot_script/stdio.log"
AABS_FOLDER = "/home/buildfarm/aabs"
PUBLISH_DEST = "/miscbuild/mrvl_extractor/"
BUILDBOT_URL = "http://buildbot.marvell.com:8010/builders/android_develop_build/builds/"
FILE_SERVER = "\\\\sh-fs04"
KEYWORD = "_wfd"

# admin user
ADM_USER = "srv-buildfarm@marvell.com"

# Mavell SMTP server
SMTP_SERVER = "10.93.76.20"

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def return_mail_text(build_type, branch, build_nr, result, package_link=None, failurelog=None):
    subject = "[ipp-autobuild-%s][%s] %s %s" % (branch, str(date.today()), build_type, result)
    message =  "This is an automated email from auto build system.\n"
    message += "It was generated because %s %s\n\n" % (build_type, result)
    message += "Buildbot Url:\n%s%s\n\n" % (BUILDBOT_URL, build_nr)
    if (result == 'failed'):
        message += "Last part of the build log is followed:\n%s\n\n" % failurelog
    if (result == 'success'):
        message += "You can download the package at:\n%s%s\n\n" % (FILE_SERVER, package_link.replace('/','\\'))
    message +="Regards,\nBuildfarm\n"
    return subject, message

# sync the build code
def sync_build_code(repo_url):
    repo_folder = repo_url.split('.')[len(repo_url.split('.'))-2].split('/')[len(repo_url.split('.')[len(repo_url.split('.'))-2].split('/'))-1]
    if not os.path.isdir(repo_folder):
        subprocess.check_call('git clone %s' % repo_url, shell=True)
    else:
        subprocess.check_call('git fetch', shell=True, cwd=repo_folder)
        subprocess.check_call('git clean -d -f', shell=True, cwd=repo_folder)
        subprocess.check_call('git reset --hard origin/master', shell=True, cwd=repo_folder)
        subprocess.check_call('git checkout origin/master', shell=True, cwd=repo_folder)
    return "%s/%s" % (os.getcwd(), repo_folder)

def get_mail_list(maintainer_f):
    #email_list = open('/tmp/mrvl_extractor/maintainer', 'r').read().split()
    email_list = open("%s/%s" % (maintainer_f, BMAINTAINERS), 'r').read().split()
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
    f = folder_server + KEYWORD
    if not os.path.isdir(f):
        #os.mkdir(f)
        return f
    else:
        i=1
        while os.path.isdir(f):
            f = folder_server + '_' + str(i) + KEYWORD
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
    # ipp git sync
    print "[Ipp-wfd-build][%s] Start sync mrvl_extractor" % str(datetime.datetime.now())
    mrvl_extractor_folder = sync_build_code(IPP_REPO_URL)
    MAIL_LIST = get_mail_list(mrvl_extractor_folder)
    print "[Ipp-wfd-build][%s] End sync" % (str(datetime.datetime.now()))
    # Set env
    print "[Ipp-wfd-build][%s] Start set env and repo sync" % str(datetime.datetime.now())
    product = return_last_device(BUILD_STDIO, 'TARGET_PRODUCT')
    variant = return_last_device(BUILD_STDIO, 'TARGET_BUILD_VARIANT')
    if branch.split('_')[0] == 'rls':
       src_dir = "src.%s-%s.%s" % (branch.split('_')[1], branch.split('_')[2], '_'.join(branch.split('_')[3:len(branch.split('_'))]))
    else:
       src_dir = "src.%s" % branch.replace('_', '-')
    src_dir_r = AABS_FOLDER + '/' + src_dir
    if not os.path.isdir(src_dir_r):
        print "Can not identify where is the android codebase!"
        exit(0)
    subprocess.check_call('repo sync', shell=True, cwd=src_dir_r)
    print "[Ipp-wfd-build][%s] End set env" % (str(datetime.datetime.now()))
    # Start ipp build
    print "[Ipp-wfd-build][%s] Start load %s" % (str(datetime.datetime.now()), BSCRIPT)
    if branch.split('_')[0] == 'rls':
        c_build = ['%s/%s' % (mrvl_extractor_folder, BSCRIPT), branch, '%s-%s' % (product, variant)]
    else:
        c_build = ['%s/%s' % (mrvl_extractor_folder, BSCRIPT), branch.replace('_', '-'), '%s-%s' % (product, variant)]
    ret = os.system(' '.join(c_build))
    if (ret==512):
        print "[Ipp-wfd-build] %s do not require build" % branch
        exit(0)
    if not (ret==0):
        print "[Ipp-wfd-build][%s] Failed Build" % (str(datetime.datetime.now()))
        failure_log = return_failure_log(BUILD_LOG)
        subject, text = return_mail_text('[Ipp-wfd-build]', branch, build_nr, 'failed', None, failure_log)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
        exit(1)
    print "[Ipp-wfd-build][%s] End Build" % (str(datetime.datetime.now()))
    # Start publishing
    print "[Ipp-wfd-build][%s] Start publishing" % (str(datetime.datetime.now()))
    publish_file = "%s/%s_release_list" % (mrvl_extractor_folder, product)
    publish_folder = check_publish_folder(PUBLISH_DEST, branch)
    if os.path.isdir('out'):
        os.system('rm -rf out')
    with open(publish_file, 'r') as file:
        for line in file:
            line = line.rstrip('\n' + '')
            if os.path.isfile(line.split(':')[0].replace(' ', '')):
                try:
                    copy_file(line.split(':')[0].replace(' ', ''), "out/%s/" % line.split(':')[1].replace(' ', ''))
                except IOError:
                    print "[Ipp-wfd-build][%s] Failed Publising" % (str(datetime.datetime.now()))
                    failure_log = return_failure_log(BUILD_LOG)
                    subject, text = return_mail_text('[Ipp-wfd-build]', branch, build_nr, 'failed', None, failure_log)
                    send_html_mail(subject,ADM_USER,MAIL_LIST,text)
                    exit(1)
            else:
                print "[Ipp-wfd-build][%s] Failed Publising" % (str(datetime.datetime.now()))
                failure_log = return_failure_log(BUILD_LOG)
                subject, text = return_mail_text('[Ipp-wfd-build]', branch, build_nr, 'failed', None, failure_log)
                send_html_mail(subject,ADM_USER,MAIL_LIST,text)
                exit(1)
    shutil.copytree('out/', publish_folder)
    print "[Ipp-wfd-build][%s] End publishing" % (str(datetime.datetime.now()))
    # All Success
    print "[Ipp-wfd-build][%s] All success" % (str(datetime.datetime.now()))
    failure_log = return_failure_log(BUILD_LOG)
    subject, text = return_mail_text('[Ipp-wfd-build]', branch, build_nr, 'success', publish_folder, None)
    send_html_mail(subject,ADM_USER,MAIL_LIST,text)
    exit(0)

#User help
def usage():
    print "\tLoad_core.py"
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

