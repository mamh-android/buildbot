#!/usr/bin/python
# v1.0
#    Author: yfshi@marvell.com

import subprocess
import getopt
import pickle
import re
import sys
import os
import csv
import json
import shlex
import datetime
from datetime import datetime, timedelta

#Gerrit admin user
m_user = "buildfarm"

#Code remote server
m_remote_server = "privgit.marvell.com"

cosmo_branch = "origin/master"

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

def run_command(*argv, **env):
    (rc, output) = run_command_status(*argv, **env)
    return output

#return a reversed open patch list
def return_dependencies_list():
    depend_list = []
    i = 1
    while True:
        arg = "git log -%s " % (i) + "--pretty=format:%H"
        (status, remote_output) = run_command_status(arg)
        revision = remote_output.split('\n')[i-1]
        if return_gerrit_patch_status(revision):
            depend_list.append(revision)
            i=i+1
        else:
            break
    depend_list.reverse()
    return depend_list

#Return gerrit patch status. True for open, False for none-open
def return_gerrit_patch_status(revision):
    cmd = "ssh -p 29418 %s@%s gerrit query --current-patch-set --format=JSON commit:%s is:open" % (m_user, m_remote_server, revision)
    (status, remote_output) = run_command_status(cmd)
    jsonstr = json.loads(remote_output.split('\n')[0])
    return not jsonstr.has_key('runTimeMilliseconds')

#re-setup code by cherry-pick the patches
def setup_code_by_cherry_pick(revisions, branch='master'):
    arg = "git reset --hard remotes/origin/%s" % (branch)
    subprocess.check_call(arg, shell=True)
    print "%s patches will be cherry-picked to origin/%s" % (len(revisions), branch)
    for rev in revisions:
        arg = "git cherry-pick %s" % (rev)
        (status, remote_output) = run_command_status(arg)
        if status:
            print "cherry-pick failed when cherry pich %s" % (rev)
            print remote_output
            exit(1)
    print "git cherry-pick completed"

#checkout the commit
def gerrit_checkout(revision):
    cmd = "ssh -p 29418 %s@%s gerrit query --current-patch-set --format=JSON commit:%s" % (m_user, m_remote_server, revision)
    (status, remote_output) = run_command_status(cmd)
    jsonstr = json.loads(remote_output.split('\n')[0])
    arg = "git fetch ssh://%s@%s:29418/cosmo %s && git checkout FETCH_HEAD" % (m_user, m_remote_server, jsonstr['currentPatchSet']['ref'])
    print arg
    subprocess.check_call(arg, shell=True)

#merge the commit
def gerrit_merge(revision):
    cmd = "ssh -p 29418 %s@%s gerrit query --current-patch-set --format=JSON commit:%s" % (m_user, m_remote_server, revision)
    (status, remote_output) = run_command_status(cmd)
    jsonstr = json.loads(remote_output.split('\n')[0])
    arg = "git fetch ssh://%s@%s:29418/cosmo %s && git merge FETCH_HEAD" % (m_user, m_remote_server, jsonstr['currentPatchSet']['ref'])
    print arg
    subprocess.check_call(arg, shell=True)

# return branch from the commit
def return_gerrit_branch(revision):
    cmd = "ssh -p 29418 %s@%s gerrit query --current-patch-set --format=JSON commit:%s" % (m_user, m_remote_server, revision)
    (status, remote_output) = run_command_status(cmd)
    jsonstr = json.loads(remote_output.split('\n')[0])
    return jsonstr['branch']

def run(revision, branch='master'):
   arg = "git fetch origin"
   subprocess.check_call(arg, shell=True)
   arg = "git reset --hard remotes/origin/%s" % branch
   subprocess.check_call(arg, shell=True)
   gerrit_checkout(revision)
   rev_list = return_dependencies_list()
   setup_code_by_cherry_pick(rev_list, branch)

#User help
def usage():
    print "\tcherry-pick all the dependencies patch and gerrit status open patch"
    print "\t      [-c] commitID"
    print "\t      [-b] working on branch {optinol}"
    print "\t      [-h] help"

def main(argv):
    commit_id = ""
    branch = ""
    try:
        opts, args = getopt.getopt(argv, "c:b:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-c"):
            commit_id = arg
            print commit_id
        elif opt in ("-b"):
            branch = arg

    if not commit_id:
        usage()
        sys.exit(2)
    if not branch:
        branch = return_gerrit_branch(commit_id)
    run(commit_id, branch)

if __name__ == "__main__":
    main(sys.argv[1:])
