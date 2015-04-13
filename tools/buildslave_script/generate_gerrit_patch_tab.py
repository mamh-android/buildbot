#!/usr/bin/python
# v1.1 init code
# v1.2 added branch sum function
# v1.3 polished output csv style
# v1.3.1 branch naming filter function added
# v1.4 added scan shgit function
#    input owner (yfshi,ylin8,wchyan)
#    regex of branch (kk4.4,lp5.1)
#    codebase

import subprocess
import json
import shlex
import getopt
import pickle
import csv
import time
from datetime import date
import sys
import os
import re
import pexpect
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

#Code remote server
m_remote_server = "shgit.marvell.com"
smtpserver = 'smtp.marvell.com'
smtp = smtplib.SMTP()
sender = 'chaoyang@marvell.com'
receiver = []

VERBOSE = False

def send_email(msg,file_name):
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = file_name
    msgText = MIMEText('%s'%msg,'html','utf-8')
    msgRoot.attach(msgText)
    att = MIMEText(open('%s'%file_name, 'rb').read(), 'base64', 'utf-8')
    att["Content-Type"] = 'application/octet-stream'
    att["Content-Disposition"] = 'attachment; filename="%s"'%file_name
    msgRoot.attach(att)
    smtp.connect(smtpserver)
    smtp.sendmail(sender, receiver, msgRoot.as_string())

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

#Return different value from gerrit query
def return_gerrit_query_jsonstr(owner, branchregex=None):
    json_list = []
    for o in owner:
        for b in branchregex:
            cmd = "ssh -p 29418 %s gerrit query --current-patch-set --format=JSON status:merged owner:%s branch:^.*%s.*" % (m_remote_server, o, b)
            (status, remote_output) = run_command_status(cmd)
            for output in remote_output.split('\n'):
                jsonstr = json.loads(output)
                if not jsonstr.has_key('runTimeMilliseconds'):
                    json_list.append(jsonstr)
    return json_list

#Return via changeID
def return_via_change(changeid_l):
    json_list = []
    for c in changeid_l:
        cmd = "ssh -p 29418 %s gerrit query --current-patch-set --format=JSON status:merged message:%s" % (m_remote_server, c)
        (status, remote_output) = run_command_status(cmd)
        for output in remote_output.split('\n'):
            jsonstr = json.loads(output)
            if not jsonstr.has_key('runTimeMilliseconds'):
                json_list.append(jsonstr)
    return json_list

#branch name to morse code
def return_mcode(branch, branch_l):
    branch_l.sort()
    branch=list(set(branch))
    morse = ''
    for i in branch_l:
        if branch.count(i):
            morse += 'M;'
        else:
            morse += ';'
    return morse

#filter the branch regex
def filter_branch(branchregex, branch_l):
    r_branch = []
    for i in branch_l:
        for j in branchregex:
            if re.match('.*%s.*' % j,i):
                r_branch.append(i)
    r_branch=list(set(r_branch))
    return r_branch

#execute ssh shgit cmd and return value
class ScanRev:
    def __init__(self, rev, project, branch_l):
        self.rev = rev
        self.project = project
        self.branch_l = branch_l
    def shgit_cmd(self, cmd):
        ip = "guest2@shgit.marvell.com -p 2222"
        passwd = "shmarvell99"
        ret = -1
        ssh = pexpect.spawn('ssh %s "%s"' % (ip, cmd))
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=5)
            if i == 0 :
                ssh.sendline(passwd)
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
            ssh.sendline(cmd)
            ret = ssh.expect(["commit %s" % self.rev, pexpect.EOF])
            r = ssh.read()
        except pexpect.EOF:
            print "EOF"
            ssh.close()
            ret = -1
        except pexpect.TIMEOUT:
            print "TIMEOUT"
            ssh.close()
            ret = -2
        return ret
    def scan_branch(self):
        branch_n = []
        for b in self.branch_l:
            cmd = "git -C /git/%s.git log %s | grep %s" % (self.project, b, self.rev)
            index = self.shgit_cmd(cmd)
            if index == 0:
                branch_n.append(b)
        return branch_n

def run(owner, branchregex):
    #setup gerrit patch change csv
    NameList = ['ChangeID', 'Author', 'Project', 'Subject']
    fout = str(date.today()) + '.csv'
    changeid_l = []
    branch_l = []
    wout = []
    for jstr in return_gerrit_query_jsonstr(owner, branchregex):
        changeid_l.append(jstr['id'])
    changeid_l=list(set(changeid_l))
    for j in return_via_change(changeid_l):
            branch_l.append(j['branch'])
    branch_l=list(set(branch_l))
    branch_l=filter_branch(branchregex, branch_l)
    branch_l.sort()
    out_csv = csv.writer(open(fout, 'wb'))
    NameList.extend(branch_l)
    out_csv.writerow(NameList)
    p_count = 0
    for c in changeid_l:
        Branch = []
        for f in return_via_change([c]):
            ChangeID = f['id'][0:7]
            Author = f['currentPatchSet']['author']['email']
            Project = f['project']
            Revision = f['currentPatchSet']['revision']
            fc = ScanRev(Revision, Project, branch_l)
            Branch.append(f['branch'])
            Branch.extend(fc.scan_branch())
            Subject = f['subject']
        p_count += 1
        print "=== %s/%s === Running ===" % (p_count, len(changeid_l))
        row = [ChangeID,Author,Project,Subject]
        row.extend(return_mcode(Branch, branch_l).split(';'))
        out_csv.writerow(row)
    if (len(receiver) > 0):
        send_email("Patch Status Report Attachment", fout)

#User help
def usage():
    print "\tgen_patch_tab"
    print "\t      [-o] owner (for multi owner split them with ,)"
    print "\t      [-b] regex branch name{kk4.4|lp5.1} (for multi branch split them with ,)"
    print "\t      [-t] receiver mail address (shg@marvell.com)"
    print "\t      [-h] help"

def main(argv):
    owner = None
    branchregex = None
    global receiver
    try:
        opts, args = getopt.getopt(argv, "o:b:t:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-o"):
            owner = arg.split(',')
        elif opt in ("-b"):
            branchregex = arg.split(',')
	elif opt in ("-t"):
            receiver = arg.split(',')

    if (owner == None) or (branchregex == None):
        usage()
        sys.exit(2)
    else:
        run(owner, branchregex)

if __name__ == "__main__":
    main(sys.argv[1:])
