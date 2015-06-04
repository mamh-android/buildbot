#!/usr/bin/python

import getopt
import ConfigParser
import string, os, sys
import subprocess
import shutil
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GIT_BASE='ssh://shgit.marvell.com:29418/git/android/'
MAX_PROJECT_NUM=10
PUBLISH_DEST = '/autobuild/temp/binary_release'
# Mavell SMTP server
SMTP_SERVER = '10.93.76.20'
ADMIN_MAIL='wchyan@marvell.com'
BUILDBOT_URL = 'http://buildbot.marvell.com:8010/builders/'
BUILD_STDIO = "/home/buildfarm/buildbot_script/stdio.log"
FILE_SERVER = '\\\\sh-fs04'
CONFIG_FILE='/autobuild/temp/binary_release/bin_release.cfg'

def runCMD( cmd , workDir=None):
    printedLines = []
    if workDir is None:
        p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=workDir)
    while p.poll()==None:
        line = p.stdout.readline()
        line = line.replace("\n","")
        printedLines.append( line )
        print line
    p.wait()
    return (p.returncode, printedLines)

def runCMDNeedShellBuiltin( cmd , workDir=None):
    printedLines = []
    if workDir is None:
        p = subprocess.Popen( cmd, shell=True, executable="/bin/bash", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        p = subprocess.Popen( cmd, shell=True, executable="/bin/bash", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=workDir)
    while p.poll()==None:
        line = p.stdout.readline()
        line = line.replace("\n","")
        printedLines.append( line )
        print line
    p.wait()
    return (p.returncode, printedLines)

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
        return 1
    return 0

#create a folder according to git branch name and time.today
def get_publish_folder(base, project, module, branch, product):
    today = date.today()
    folder = str(today) + '_' + product + '_' + branch
    folder_server = base + '/' + project + '/' + module + '/' + folder
    f = folder_server
    if not os.path.isdir(f):
        #os.mkdir(f)
        return f
    else:
        i=1
        while os.path.isdir(folder_server):
            f = folder_server + '_' + str(i)
            if not os.path.isdir(f):
                #os.mkdir(f)
                return f
                break
            else:
                i = i + 1 

def return_mail_text(project, board, branch, build_type, build_nr, result, package_link=None, failurelog=None):
    build_type_url = "android_develop_build"
    if build_type == 'ODVB':
        build_type_url = 'on_demand_virtual_build'
    elif build_type == 'DISB':
        build_type_url = 'android_distraction_build'
    elif build_type == 'RTVB':
        build_type_url = 'android_develop_build'
    subject = "[binary autobuild][%s-%s] %s %s" % (board, branch, str(date.today()), result)
    message =  "This is an automated email from auto build system.\n"
    message += "It was generated because build %s %s\n\n" % (project, result)
    message += "Buildbot Url:\n%s%s/builds/%s\n\n" % (BUILDBOT_URL, build_type_url, build_nr)
    if (result == 'failed'):
        message += "Last part of the build log is followed:\n%s\n\n" % failurelog
    if (result == 'success'):
        message += "You can download the package at:\n%s%s\n\n" % (FILE_SERVER, package_link.replace('/','\\'))
    message +="Regards,\nBuildfarm\n"
    return subject, message

def send_mail(subject, from_who, to_who, text):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_who
    msg['To'] = to_who + ',' + from_who
    part1 = MIMEText(text, 'plain')
    msg.attach(part1)
    s = smtplib.SMTP(SMTP_SERVER)
    s.sendmail(from_who, to_who, msg.as_string())
    s.quit()

def get_android_env(msg):
    top=None
    out=None
    for line in msg:
        if line.startswith('ANDROID_BUILD_TOP'):
            top = line.split('=')[1]
        if line.startswith('ANDROID_PRODUCT_OUT'):
            out = line.split('=')[1]
        if top != None and out != None:
            break
    return top, out

def publish_to_dir(android_top, dst_folder, publish_dir, msg):
    build_fail = False
    ret_msg = ''
    if publish_dir == None:
        return build_fail, ret_msg
    if publish_dir == 'android':
        publish_dir = None
    for line in msg:
        if line.startswith('Install:'):
            file_name = line.split('/')[4:]
            if publish_dir != None:
                file_name = publish_dir + '/' + file_name[-1] #put all files into publish dir folder
            else:
                file_name = reduce(lambda x, y: x + '/' + y, file_name) #keep android output layout
            #print(line.split(':')[1], dst_folder + '/' + file_name)
            ret = copy_file(android_top + '/' + line.split(':')[1].strip(), dst_folder + '/' + file_name)
            if ret != 0:
                build_fail = True
                ret_msg = git_name + ' publish ' + file_name + ' failure!'
    return build_fail, ret_msg


def publish_by_config(android_top, android_out, dst_folder, project_path):
    build_fail = False
    msg = 'No release.txt file'
    publish_file = android_top + '/' + project_path + '/release.txt'
    #publish_file = 'release.txt'
    if os.path.isfile(publish_file):
        with open(publish_file, 'r') as file:
            for line in file:
                tp = line.split(':')[0]
                src = line.split(':')[1].strip()
                dst = dst_folder + '/' + line.split(':')[2].strip()
                print tp, src, dst
                if tp == 'src':
                    src = android_top + '/' + project_path + '/' + src
                elif tp == 'out':
                    src = android_out + '/' + src
                else:
                    build_fail = True
                    msg = project_path + ' release config error: ' + line
                    break
                print('copy ', src, dst)
                if os.path.isfile(src):
                    try:
                        copy_file(src, dst)
                    except IOError:
                        build_fail = True
                        msg = project_path + ' publish copy' + src + ' Failure!'
                        break
                else:
                    build_fail = True
                    msg = project_path + ' publish failure ' + src + ' is not exist!'
                    break
    return build_fail, msg

def publish_git_log(android_top, path_name, dst_folder):
    build_fail = False
    msg = ''
    log_file = android_top + '/' + path_name + '/git.log'
    if os.path.isfile(log_file):
        try:
            copy_file(log_file, dst_folder + '/git.log')
        except IOError:
            build_fail = True
            msg = git_name + ' publish git log file failure!'
    return build_fail, msg

def get_project_source(git_name, branch_name, path_name):
    git_addr = GIT_BASE + git_name
    clone_cmd = 'git clone -b ' + branch_name + ' ' 
    clone_cmd += git_addr + ' ' + path_name
    print(clone_cmd)
    ret, msg = runCMD(clone_cmd)
    #print(ret, msg)
    msg = '\n'.join(msg)
    log_cmd = 'cd ' + path_name + ' && '
    log_cmd += 'git log -n 10 > git.log'
    runCMD(log_cmd)

    return ret, msg

def build_project(target_product, android_variant, android_root, path_name, build_mode):
    build_fail = False
    msg = ''
    ret = 0
    if build_mode == 'android':
        build_cmd = 'cd ' + android_root + ' && '
        build_cmd += 'source build/envsetup.sh && '
        build_cmd += 'lunch ' + target_product + '-' + android_variant + ' && '
        build_cmd += 'env && '
        build_cmd += 'cd ' + path_name + ' && '
        build_cmd += 'mm -B'
        print build_cmd
        ret, msg = runCMDNeedShellBuiltin(build_cmd)
    elif build_mode == 'make': 
        pass
    elif build_mode == 'user':
        pass
    else:
        build_fail = True
        msg = 'build mode ' + build_mode  + ' is not support'

    if ret != 0:
        build_fail = True
        msg = '\n'.join(msg)

    return build_fail, msg

def get_last_build_product():
    target_product = None
    android_root = None
    build_type = None

    if os.path.isfile(BUILD_STDIO):
        with open(BUILD_STDIO, 'r') as file:
            for line in file:
                if line.startswith('TARGET_PRODUCT='):
                    target_product = line.split('=')[1]
                if line.startswith('ANDROID_SOURCE_DIR'):
                    android_root = line.split(':')[1]
                    android_root.strip()
                if line.startswith('Build type:'):
                    build_type = line.split(':')[1]
                    build_type.strip()
    if target_product != None:
        target_product = target_product.split('\n')[0]
    if android_root != None:
        android_root = android_root.split('\n')[0]
    if build_type != None:
        build_type = build_type.split('\n')[0]
    print '--- Get last android root: %s, product: %s from stdio.log' % (android_root, target_product)
    return android_root, target_product, build_type

def run(target_product, build_branch, build_nr, android_variant):
    #read all config file
    cf = ConfigParser.ConfigParser()
    cf.read(CONFIG_FILE)
    android_root, _product, build_type = get_last_build_product()
    if android_root == None or build_type == None:
        print 'Not found android source code or build type, stop binary release build'
        return

    if target_product == None:
        target_product = _product

    print target_product
    #find out the need build section in board
    projects = []
    secs = cf.sections()
    for s in secs:
        product_list = []
        if cf.has_option(s, 'target_product'):
            product = cf.get(s, 'target_product')
            product_list = product.split(',')
        else:
            product_list.append(target_product)
        branch = cf.get(s, 'build_branch')
        branch_list = branch.split(',')
        for p in product_list:
            for b in branch_list:
                if target_product == p and build_branch == b:
                    projects.append(s)
    print 'Build projects: '  + ','.join(projects)

    #do the build, copy the binary and send mail one by one
    for project in projects:
        #get all project
        if cf.has_option(project, 'name'):
            project_name = cf.get(project, 'name')
        mail_owner = cf.get(project, 'owner')
        print '--- ' + project
        branch = ''
        if cf.has_option(project, 'src_branch'):
            branch = cf.get(project, 'src_branch')

        build_fail = False
        msg = ''
        dst_folder = ''
        clean_list = []
        for i in range(1, MAX_PROJECT_NUM):
            sgname = 'src_git_%d' % i
            spname = 'src_local_path_%d' % i
            sbname = 'src_branch_%d' % i
            bpname = 'bin_local_path_%d' % i
            bmname = 'build_mode_%d' % i
            branch_name = branch
            git_name = ''
            path_name = ''
            bin_path_name = ''
            publish_dir = None
            build_mode = 'android'
            if cf.has_option(project, sgname):
                git_name = cf.get(project, sgname)
                path_name = cf.get(project, spname)
                bin_path_name = cf.get(project, bpname)
                if cf.has_option(project, sbname):
                    branch_name = cf.get(project, sbname)
                if cf.has_option(project, bmname):
                    build_mode = cf.get(project, bmname)
            else:
                #not found more git
                break
            clean_list.append(android_root + '/' + path_name)
        
            if cf.has_option(project, 'publish_dir'):
                publish_dir = cf.get(project, 'publish_dir') 

            #clean the binary project in code tree
            print '--- clean the binary project'
            print('rm -rf ' + bin_path_name)
            ret, msg = runCMD('rm -rf ' + android_root + '/' + bin_path_name)
            print(ret, msg)
            if ret != 0:
                build_fail = True
                msg = '\n'.join(msg)
                break

            print '\n--- git project source code'
            ret, msg = get_project_source(git_name, branch_name, android_root + '/' + path_name)
            if ret != 0:
                build_fail = True
                break

            print '\n--- start build '
            build_fail, msg = build_project(target_product, android_variant, android_root, path_name, build_mode)
            if build_fail:
                break

            android_top, android_out = get_android_env(msg) 
            print '--- android top: ' + android_top
            print '--- android out: ' + android_out

            #publish the build binary
            print '\n--- publish the build binary'
            ret = 0
            file_name = ''
            module = git_name.split('/')[-1]
            dst_folder = get_publish_folder(PUBLISH_DEST, project, module, build_branch, target_product)
            build_fail, msg = publish_to_dir(android_top, dst_folder, publish_dir, msg)
            if build_fail:
                break
            build_fail, msg =  publish_by_config(android_top, android_out, dst_folder, path_name)
            if build_fail:
                break
            publish_git_log(android_top, path_name, dst_folder)

        #send mail to admin and owner
        if build_fail:
            result = 'failed'
            clean_list.append(dst_folder)
        else:
            result = 'success'
        print '--- build ' + result
        print '--- notification sendmail '
        mail_subject, mail_text = return_mail_text(project_name, target_product, build_branch, build_type, build_nr, result, package_link=dst_folder, failurelog=msg)
        send_mail(mail_subject, ADMIN_MAIL, mail_owner, mail_text) 

        #clean the previous project build
        print '--- do clean'
        for folder in clean_list:
            print('rm -rf ' + folder)
            ret, msg = runCMD('rm -rf ' + folder)
        print '--- binary build end'

#User help
def usage():
    print "\tbin_release.py"
    print "\t      [-p] android product"
    print "\t      [-b] build branch"
    print "\t      [-m] android build mode: eng, user, userdebug"
    print "\t      [-n] build number from buildbot"
    print "\t      [-h] help"

def main(argv):
    build_branch = ''
    target_product = None
    build_nr = ''
    android_variant = 'userdebug'
    try:
        opts, args = getopt.getopt(argv,"p:b:n:m:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-p"):
            target_product = arg
        elif opt in ("-b"):
            build_branch = arg
        elif opt in ("-m"):
            android_variant = arg
        elif opt in ("-n"):
            build_nr = arg
    if not build_branch or not build_nr:
        usage()
        sys.exit(2)

    if android_variant == 'None':
        android_variant = 'userdebug'
    #From distribution build, it build branch will like pxa1936-lp5.1/3148
    build_branch = build_branch.split('/')[0]
    #From odvb , the product is product:device
    if target_product != None:
        target_product = target_product.split(':')[0]
    run(target_product, build_branch, build_nr, android_variant)

if __name__ == '__main__':
    main(sys.argv[1:])
