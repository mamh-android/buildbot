#!/usr/bin/python
# v1.1 init code
# v1.2 added branch sum function
# v1.3 polished output csv style
#    input owner (yfshi,ylin8,wchyan)
#    regex of branch (kk4.4,lp5.1)

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

#Code remote server
m_remote_server = "shgit.marvell.com"

VERBOSE = False

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
    b_l = branch.split(';')
    morse = ''
    for i in branch_l:
        if b_l.count(i):
            morse += 'M;'
        else:
            morse += ';'
    return morse

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
    branch_l.sort()
    out_csv = csv.writer(open(fout, 'wb'))
    NameList.extend(branch_l)
    out_csv.writerow(NameList)
    for c in changeid_l:
        Branch = ''
        for f in return_via_change([c]):
            ChangeID = f['id'][0:7]
            Author = f['currentPatchSet']['author']['email']
            Project = f['project']
            Branch += '%s;' % f['branch']
            Subject = f['subject']
        row = [ChangeID,Author,Project,Subject]
        row.extend(return_mcode(Branch, branch_l).split(';'))
        out_csv.writerow(row)

#User help
def usage():
    print "\tgen_patch_tab"
    print "\t      [-o] owner (for multi owner split them with ,)"
    print "\t      [-b] regex branch {kk4.4|lp5.1} (for multi branch split them with ,)"
    print "\t      [-h] help"

def main(argv):
    owner = None
    branchregex = None
    try:
        opts, args = getopt.getopt(argv, "o:b:h")
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

    if (owner == None) or (branchregex == None):
        usage()
        sys.exit(2)
    else:
        run(owner, branchregex)

if __name__ == "__main__":
    main(sys.argv[1:])
