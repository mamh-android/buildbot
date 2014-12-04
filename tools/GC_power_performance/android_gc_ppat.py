#!/usr/bin/python
# v1.0
#    Author: yfshi@marvell.com

import subprocess
import sys
import os
import json
import shlex
import datetime
from datetime import date
import ConfigParser
import getopt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Gerrit admin user
m_user = "buildfarm"

#Code remote server
m_remote_server = "shgit.marvell.com"

#Gerrit admin user
ADM_USER = "srv-buildfarm@marvell.com"

#Mavell SMTP server
SMTP_SERVER = "10.93.76.20"

VERBOSE = False

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()
sys.stdout = flushfile(sys.stdout)

SCRIPT_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
ODVB_BASH = "/home/%s/buildbot_script/buildbot/od_virtual_build.sh" % m_user
PPAT_GIT = "ssh://%s@%s/git/android/shared/Buildbot/ppat.git" % (m_user, m_remote_server)
AUTOBUILD = "/autobuild/android/"
CFG_FILE = "/home/%s/buildbot_script/buildbot/tools/GC_power_performance/config" % m_user
GERRIT_REVIEW = "/home/%s/buildbot_script/buildbot/core/gerrit_review_update.py" % m_user
STD_LOG = "/home/%s/buildbot_script/stdio.log" % m_user

def run_command_status(*argv, **env):
    if VERBOSE:
        print(datetime.datetime.now(), "Running:", " ".join(argv))
    if len(argv) == 1:
        argv = shlex.split(str(argv[0]))
    newenv = os.environ
    newenv.update(env)
    p = subprocess.Popen(argv, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, env=newenv)
    (out, nothing) = p.communicate()
    out = out.decode('utf-8')
    return (p.returncode, out.strip())

def run_command(*argv, **env):
    (rc, output) = run_command_status(*argv, **env)
    return output

#return revision from cfg
def return_revision_via_cfg(cfg_file):
    config = ConfigParser.RawConfigParser()
    try:
        config.read(cfg_file)
    except IOError:
        print "failed to open file with read mode"
        exit(2)
    l_project = config.sections()
    l_project.remove('board.mk')
    jsonstr = []
    revision = []
    for i in l_project:
        cmd = "ssh -p 29418 %s@%s gerrit query --current-patch-set --format=JSON is:open label:Verified=0" % (m_user, m_remote_server)
        config.options(i)
        for j in config.options(i):
            cmd += ' ' + j + ':' + config.get(i, j)
        (status, remote_output) = run_command_status(cmd)
        l = remote_output.split('\n')
        l.pop()
        for k in l:
            j_str = json.loads(k)
            revision.append(j_str['currentPatchSet']['revision'])
    print revision
    return ','.join(revision)

#return board info from cfg
def return_board_via_cfg(cfg_file):
    config = ConfigParser.RawConfigParser()
    config.read(cfg_file)
    return config.get('board.mk', 'product'), config.get('board.mk', 'device'), config.get('board.mk', 'reason')

#return maillist from cfg
def return_mail_via_cfg(cfg_file):
    config = ConfigParser.RawConfigParser()
    config.read(cfg_file)
    return config.get('board.mk', 'owner').split(',')

# return device via branch
def return_device(branch):
    if branch.split('_')[0] == 'rls':
        device = branch.split('_')[1]
    else:
        device = branch.split('-')[0]
    return device

# return last build
def return_last_device(last_file):
    try:
        fp_src = open(last_file, 'r')
        l = fp_src.readlines()
        fp_src.close()
    except IOError:
        print "failed to open file with read mode"
        exit(2)
    return l[2].split(':')[1].strip()

# return last manifest.xml
def return_last_manifest(branch):
    last_file = "%s/%s/LAST_BUILD.%s" % (AUTOBUILD, return_device(branch), branch)
    return return_last_device(last_file)

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

# return last build from stdout log
def return_build_device(src_file):
    try:
        fp_src = open(src_file, 'r')
        fp_src.close()
    except IOError:
        print "failed to open file with read mode"
        exit(2)
    try:
        # return matching re
        arg = '''awk -F"<result-dir>http:|</result-dir>" ' /<result-dir>/ { print $2 } ' %s''' % src_file
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        (out, nothing) = p.communicate()
        return out.split()[len(out.split())-1]
    except IOError:
        print "failed searching"
        exit(2)

def return_mail_text(branch, result, image_link=None):
    subject = "[gcvb][%s-%s] %s" % (branch, str(date.today()), result)
    message =  "This is an automated email from auto build system.\n"
    message += "It was generated because gcvb was %s\n\n" % (result)
    if (result == 'success'):
        message += "You can get the package at:\n%s\n\n" % (image_link)
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

''' # Sample from master.cfg
odvb_and_ppat_factory.addStep(ShellCommand(command=["bash","/home/buildfarm/buildbot_script/buildbot/od_virtual_build.sh","-p",Property('Gerrit_Patch'),"-m",Property('Manifest_Xml'),"-b",Property('BRANCH_NAME'),"-d","ODVB_PPAT_AUTO","-v",Property('Product_Type'),"-de",Property('Build_Device')],haltOnFailure="True",flunkOnFailure="True"))
odvb_and_ppat_factory.addStep(Git_marvell(repourl='ssh://buildfarm@shgit/git/android/shared/Buildbot/ppat.git', mode='full', method='fresh', workdir="build_script", haltOnFailure="True"))
odvb_and_ppat_factory.addStep(ShellCommand(command=["bash","/home/buildfarm/buildbot_script/buildbot/tools/PPAT/startPPAT.sh", Property('Build_Device'), Property('Build_Blf'), Property('useremail'), Property('PPAT_Xml'), Property('Reason')]))
'''
def run(branch):
    print "[Self-build] get values"
    Gerrit_Patch = return_revision_via_cfg("%s/%s.cfg" % (CFG_FILE, branch))
    if not Gerrit_Patch:
        print "Gerrit patch is empty"
        print "~~<result>PASS</result>"
        print "~~<result-details>No build</result-details>"
        exit(-1)
    Manifest_Xml= "%s/manifest.xml" % return_last_manifest(branch)
    OUTPUT_DIR = "ODVB_PPAT_AUTO"
    (Product_Type, Build_Device, Purpose) = return_board_via_cfg("%s/%s.cfg" % (CFG_FILE, branch))
    print "[Self-build] start ODVB"
    cmd = ODVB_BASH
    cmd += " -p %s" % Gerrit_Patch
    cmd += " -m %s" % Manifest_Xml
    cmd += " -b %s" % branch
    cmd += " -d %s" % OUTPUT_DIR
    cmd += " -v %s -de %s" % (Product_Type, Build_Device)
    print cmd
    ret_p = os.system(cmd)
    if not (ret_p==0):
        print "[Self-build] Failed ODVB"
        print "[Self-build] Gerrit review update"
        cmd = GERRIT_REVIEW
        cmd += " -p %s -m \"GCVB base:%s\" -r failure" % (Gerrit_Patch, Manifest_Xml)
        print cmd
        ret_p = os.system(cmd)
        print "[Self-build] Send failure mail"
        subject, text = return_mail_text(branch, 'failed')
        send_html_mail(subject,ADM_USER,return_mail_via_cfg("%s/%s.cfg" % (CFG_FILE, branch)),text)
        os.system("%s/fail.py" % SCRIPT_PATH)
        exit(1)
    print "[Self-build] Gerrit review update"
    cmd = GERRIT_REVIEW
    cmd += " -p %s -m \"GCVB base:%s\" -r success -d %s" % (Gerrit_Patch, Manifest_Xml, return_build_device(STD_LOG))
    print cmd
    ret_p = os.system(cmd)
    print "[Self-build] Send success mail"
    subject, text = return_mail_text(branch, 'success', return_build_device(STD_LOG))
    send_html_mail(subject,ADM_USER,return_mail_via_cfg("%s/%s.cfg" % (CFG_FILE, branch)),text)
    os.system("%s/pass.py" % SCRIPT_PATH)
    print "[Self-build] start PPAT"
    cmd = "%s/trigger.py" % sync_build_code(PPAT_GIT)
    cmd += " --imagepath %s --device %s --purpose \"%s\" --mode gc" % (return_build_device(STD_LOG), Build_Device, Purpose)
    cmd += " --assigner %s" % ','.join(return_mail_via_cfg("%s/%s.cfg" % (CFG_FILE, branch)))
    print cmd
    ret_p = os.system(cmd)
    if not (ret_p==0):
        print "[Self-build] Failed startPPAT"
        exit(1)
    print "[Self-build] All Success"
    exit(0)

#User help
def usage():
    print "\tandroid_gc_ppat.py"
    print "\t      [-b] branch"
    print "\t      [-h] help"

def main(argv):
    branch = None
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

