#!/usr/bin/python

import os
import sys
import datetime
import subprocess
import time
from subprocess import Popen

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
    print "CPU core counter:%d" % (num)

    return num

def exec_commands(cmds):
    ''' Exec commands in parallel in multiple process 
    (as much as we have CPU)
    '''
    if not cmds: return # empty list

    def done(p):
        return p.poll() is not None
    def success(p):
        return p.returncode == 0
    def fail(p):
        print "[AutoTest][%s][PID:%s] exit with none Zero" % (str(datetime.datetime.now()), p.pid)
        print p.stdout.read()
        sys.exit(1)
    
    '''MAX task count 
    '''
    max_task = cpu_count()
    processes = []
    while True:
        while cmds and len(processes) < max_task:
            task = os.getcwd() + '\\' + cmds.pop(0)
            p = subprocess.Popen(task, stdout=subprocess.PIPE,stderr=subprocess.STDOUT, shell='Ture')
            processes.append(p)
            print "[AutoTest][%s][PID:%s]'%s' append to CPU" % (str(datetime.datetime.now()), p.pid, task)

        for p in processes:
            if done(p):
                if success(p):
                    '''Print stdout after a task success
                    '''
                    print "[AutoTest][%s][PID:%s] exit with Zero" % (str(datetime.datetime.now()), p.pid)
                    print p.stdout.read()
                    processes.remove(p)
                    print processes
                else:
                    fail(p)

        if not processes and not cmds:
            print "tasklist done"
            break
            '''(pid, status) = os.wait()
               Availability: Unix
            '''
        else:
            time.sleep(5)

def create_dir(d):
    try:
        os.rmdir(d)
        print "Remove %s" % (d)
    except Exception:
        os.mkdir(d)
        print "Create %s" % (d)

commands_1 = [
    "bin\\cosmo.exe -c xml\\cosmo_3H5.xml",
    "bin\\cosmo.exe -c xml\\c1.1_3H5.xml",
    "bin\\cosmo.exe -c xml\\us2_3H5.xml",
    "bin\\cosmo.exe -c xml\\c1_3H5.xml",
    "bin\\cosmo.exe -c xml\\c1_3H7.xml",
    "bin\\cosmo.exe -c xml\\c1_IMX132.xml",
    "bin\\cosmo.exe -c xml\\c1_IMX135.xml",
    "bin\\cosmo.exe -c xml\\c1_OV5647_QTech.xml",
    "bin\\cosmo.exe -c xml\\c1_OV5647_Darling.xml",
    "bin\\cosmo.exe -c xml\\c1_OV5647_Sunny.xml",
    "bin\\cosmo.exe -c xml\\c1_OV5647_Suyin.xml",
    "bin\\cosmo.exe -c xml\\c1_OV8825.xml",
    "bin\\cosmo.exe -c xml\\c1_OV8850.xml"
]

commands_2 = [
    "bin\\cosmo.exe -s test\\cosmo_3H5.sim",
    "bin\\cosmo.exe -s test\\c1.1_3H5.sim",
    "bin\\cosmo.exe -s test\\us2_3H5.sim",
    "bin\\cosmo.exe -s test\\c1_3H5_lab.sim",
    "bin\\cosmo.exe -s test\\c1_3H7_lab.sim",
    "bin\\cosmo.exe -s test\\c1_IMX132_lab.sim",
    "bin\\cosmo.exe -s test\\c1_IMX135_lab.sim",
    "bin\\cosmo.exe -s test\\c1_OV5647_QTech_lab.sim",
    "bin\\cosmo.exe -s test\\c1_OV5647_Darling_lab.sim",
    "bin\\cosmo.exe -s test\\c1_OV5647_Sunny_lab.sim",
    "bin\\cosmo.exe -s test\\c1_OV5647_Suyin_lab.sim",
    "bin\\cosmo.exe -s test\\c1_OV8825_lab.sim",
    "bin\\cosmo.exe -s test\\c1_OV8850_lab.sim"
]

def main(argv):
    print "[Cosmo Daily Test][%s]=======Start=======" % (str(datetime.datetime.now()))
    print "working dir:%s" % (os.getcwd())
    create_dir('DailyAutoTestResult')
    cmds_array = []
    cmds_array.append(commands_1)
    cmds_array.append(commands_2)
    for raw in cmds_array:
        exec_commands(raw)
    print "[Cosmo Daily Test][%s]=======End=======" % (str(datetime.datetime.now()))
    print "*** Cosmo Daily Test: all runnings success"

if __name__ == "__main__":
    main(sys.argv[1:])
