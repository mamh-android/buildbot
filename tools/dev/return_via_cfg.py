#!/usr/bin/python
# v1.0

import subprocess
import sys
import os
import json
import shlex
import datetime
import ConfigParser

#Gerrit admin user
m_user = "buildfarm"

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

def run_command(*argv, **env):
    (rc, output) = run_command_status(*argv, **env)
    return output

#return revision from cfg
def return_revision_via_cfg(cfg_file):
    config = ConfigParser.RawConfigParser()
    config.read(cfg_file)
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
    return config.get('board.mk', 'device'), config.get('board.mk', 'blf')

#User help
def usage():
    print "\treturn via cfg"
    print "\t      [-h] help"

def main(argv):
    #run_args(args_list)

if __name__ == "__main__":
    main(sys.argv[1:])
