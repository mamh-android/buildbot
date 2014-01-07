#!/usr/bin/python

import os
import sys
import datetime
import subprocess
from subprocess import Popen, list2cmdline

def cpu_count():
    ''' Returns the number of CPUs in the system
    '''
    num = 1
    if sys.platform == 'win32':
        try:
            num = int(os.environ['NUMBER_OF_PROCESSORS'])
        except (ValueError, KeyError):
            pass
    elif sys.platform == 'linux2':
        try:
            num = int(os.popen("cat /proc/cpuinfo | grep -i 'processor' | wc -l").read())
        except ValueError:
            pass
    else:
        try:
            num = os.sysconf('SC_NPROCESSORS_ONLN')
        except (ValueError, OSError, AttributeError):
            pass

    return num

def exec_commands(cmds):
    ''' Exec commands in parallel in multiple process 
    (as much as we have CPU)
    '''
    if not cmds: return # empty list

    def done(p):
        return p.poll() is not None
    def success(p):
        '''Print stdout and return 0 after a task success
        '''
        print "[AutoTest][%s][PID:%s] exit with Zero" % (str(datetime.datetime.now()), p.pid)
        print p.stdout.read()
        return 0
    def fail(p):
        print "[AutoTest][%s][PID:%s] exit with none Zero" % (str(datetime.datetime.now()), p.pid)
        print p.stdout.read()
        sys.exit(1)
    
    '''MAX task count 
    '''
    max_task = cpu_count()
    processes = {}
    while True:
        while cmds and len(processes) < max_task:
            task = cmds.pop(0)
            p = subprocess.Popen(task, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            processes[p.pid] = p
            print "[AutoTest][%s][PID:%s]'%s' append to CPU" % (str(datetime.datetime.now()), p.pid, list2cmdline(task))
     
        if not processes and not cmds:
            print "tasklist done"
            break
        elif processes:
            print "wait for cpu idle..."
            (pid, status) = os.wait()
            if pid in processes:
                if not status:
                    success(processes[pid])
                    del processes[pid]
                else:
                    fail(processes[pid])

commands_1 = [
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test1.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test2.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test3.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test4.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test1.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test2.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test3.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test4.py"]
]

commands_2 = [
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test1.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test2.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test3.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test4.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test1.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test2.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test3.py"],
    ["/home/yfshi/workspace/cosmo_build/buildscript/dev/test4.py"]
]

cmds_array = []
cmds_array.append(commands_1)
cmds_array.append(commands_2)

for raw in cmds_array:
    exec_commands(raw)
