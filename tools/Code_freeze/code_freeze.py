#!/usr/bin/python
# v1.0
#    Code freeze Script
#    Author: yfshi@marvell.com

import os
import sys
import re
import shutil
import getopt
import datetime
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ALL_PROJECT="ssh://shgit.marvell.com/All-Projects"
#Mavell SMTP server
SMTP_SERVER = "10.93.76.20"
#Gerrit admin user
ADM_USER = "yfshi@marvell.com"
#Mail list
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

def return_mail_text(build_type, branch):
    subject = "[Attention][%s][branch: %s] code %s " % (str(date.today()), branch, build_type)
    message =  "This is an automated email from auto build system.\n"
    message += "The code is %s\n\n" % build_type
    message +="Regards,\nTeam of APSE\n"
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

#Add permission
def code_freeze(branch):
    with open("project.config", "rt") as fin:
        for line in fin:
            rx = re.match("\[access \"refs/heads/%s\"\]" % branch, line)
            if not rx:
                up=1
                continue
            else:
                up=None
                break
    if not up:
        print "Nothing update for %s" % branch
        exit(0)
    else:
        print "Code freeze for %s" % branch
        with open("out", "wt") as fout:
            with open("project.config", "rt") as fin:
                for line in fin:            
                    fout.write(line)
            fout.write("[access \"refs/heads/%s\"]\n" % branch)
            fout.write("\tsubmit = group releaseadmin\n")
            fout.write("\tsubmit = block group Registered Users\n")
            fout.write("\tpush = block group Registered Users\n")

#rm permission
def code_defreeze(branch):
    with open("project.config", "rt") as fin:
        for line in fin:
            rx = re.match("\[access \"refs/heads/%s\"\]" % branch, line)
            if not rx:
                up=1
                continue
            else:
                up=None
                break
    if not up:
        print "Code defreeze for %s" % branch
        i = 3
        with open("out", "wt") as fout:
            with open("project.config", "rt") as fin:
                for line in fin:
                    if not re.match("\[access \"refs/heads/%s\"\]" % branch, line) and (i > 2):
                        fout.write(line)
                    elif (i <= 2):
                        i = i + 1
                    else:
                        i = 0
    else:
        print "Nothing update for %s" % branch
        exit(0)

def run(branch, rev, mail):
    #clone the All-project
    if os.path.isdir("All-Projects"):
        print "[%s] Removing All-Projects" % (str(datetime.datetime.now()))
        shutil.rmtree("All-Projects")
    cmd = "git clone " + ALL_PROJECT
    print "[%s] %s" % (str(datetime.datetime.now()), cmd)
    os.system(cmd)
    os.chdir("All-Projects")
    if rev == 'F':
        code_freeze(branch)
    elif rev == 'D':
        code_defreeze(branch)
    else:
        exit(0)
    #git commit&push
    os.system("git config --local --replace-all user.email  %s" % mail)
    os.system("cp out project.config")
    if rev == 'F':
        os.system("git commit -asm \"Code freeze for branch %s\"" % branch)
        subject, text = return_mail_text('freeze', branch)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
    elif rev == 'D':
        os.system("git commit -asm \"Code defreeze for branch %s\"" % branch)
        subject, text = return_mail_text('defreeze', branch)
        send_html_mail(subject,ADM_USER,MAIL_LIST,text)
    os.system("git push origin HEAD:refs/meta/config")
    print "[%s] All-Projects Code update done" % (str(datetime.datetime.now()))
    
#User help
def usage():
    print "\tcode_freeze.py"
    print "\t      [-b] branch name"
    print "\t      [-r] {F|D}"
    print "\t      [-m] email for notification"
    print "\t      [-h] help"

def main(argv):
    branch = None
    rev = None
    mail = None
    try:
        opts, args = getopt.getopt(argv,"b:r:m:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-b"):
            branch = arg
        elif opt in ("-r"):
            rev = arg
        elif opt in ("-m"):
            mail = arg
            MAIL_LIST.append(mail)
    if not branch or not rev:
        usage()
        sys.exit(2)

    run(branch, rev, mail)

if __name__ == "__main__":
    main(sys.argv[1:])
