#!/usr/bin/python

import os
import getopt
import sys
import datetime
import subprocess
import time
from subprocess import Popen

''' Force Python's print function to output to the screen.
'''
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

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
    def fail(p,log):
        print "[Cosmo-MCR][%s][PID:%s] exit with none Zero, please check the log %s" % (str(datetime.datetime.now()), p.pid, log)
        sub_path = 'DailyAutoTestLog\\'
        stdout_tmp = sub_path + log
        f = open(stdout_tmp, 'r')
        print f.read()
        f.close
        sys.exit(1)
    
    '''MAX task count 
    '''
    max_task = cpu_count()-1
    processes = []
    stdout_pid = {}
    stdout_log = {}
    for i in range(max_task):
        stdout_log[str(i)] = 0
    while True:
        while cmds and len(processes) < max_task:
            task = cmds.pop(0)
            stdout_tmp = return_idel_log_file(max_task, stdout_log)
            sub_path = 'DailyAutoTestLog\\'
            stdout_tmp_s = sub_path + str(stdout_tmp)
            p = subprocess.Popen(task, stdout=open(stdout_tmp_s, 'a'), cwd=os.getcwd())
            stdout_pid[p.pid] = stdout_tmp
            print stdout_pid
            stdout_log[stdout_tmp] = p.pid
            print stdout_log
            processes.append(p)
            print "[Cosmo-MCR][%s][PID:%s]'%s' append to CPU log captured to >> %s" % (str(datetime.datetime.now()), p.pid, task, stdout_tmp)

        for p in processes:
            if done(p):
                if success(p):
                    '''Print stdout after a task success and remove the tmp log
                    '''
                    print "[Cosmo-MCR][%s][PID:%s] exit with Zero" % (str(datetime.datetime.now()), p.pid)
                    #f = open(stdout_pid[p.pid], 'r')
                    #print f.read()
                    #f.close
                    #os.remove(stdout_pid[p.pid])
                    stdout_log[stdout_pid[p.pid]] = 0
                    processes.remove(p)
                else:
                    fail(p,stdout_pid[p.pid])

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

def return_idel_log_file(max_task, stdout_log):
    for i in stdout_log:
        log_name = str(i)
        if not stdout_log[i]:
            break
    return log_name

def run(main_exe, cmd_list):
    print "[Cosmo-MCR][%s]=======Start=======" % (str(datetime.datetime.now()))
    print "working dir:%s" % (os.getcwd())
    if not os.path.isdir('DailyAutoTestResult'):
        create_dir('DailyAutoTestResult')
    os.chdir('DailyAutoTestResult')
    if not os.path.isdir('DailyAutoTestLog'):
        create_dir('DailyAutoTestLog')
    #create a command list for xml
    commands = []
    for i in cmd_list:
        commands.append("%s %s" % (main_exe, i))
    cmds_array = []
    cmds_array.append(commands)
    for raw in cmds_array:
        print raw
        exec_commands(raw)
    print "[Cosmo-MCR][%s]=======End=======" % (str(datetime.datetime.now()))
    print "*** Cosmo Daily Test: all runnings success"

#User help
def usage():
    print "\tcosmo mulit core auto test"
    print "\t      [-c] main exe ..\\bin\\cosmo.exe"
    print "\t      [-l] command list ..\\test\\*.xml"
    print "\t      [-h] help"

def main(argv):
    main_exe = ""
    command_list = []
    try:
        opts, args = getopt.getopt(argv,"c:l:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-c"):
            main_exe = arg
        elif opt in ("-l"):
            command_list = arg.split(',')
    if not main_exe or not command_list:
        usage()
        sys.exit(2)
    run(main_exe, command_list)

if __name__ == "__main__":
    main(sys.argv[1:])
