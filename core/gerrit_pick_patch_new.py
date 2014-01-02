#!/usr/bin/python
# v1.1
#    Cherry pick patches from git server by gerrit patchsetID
#    patchsetID should be a list, such as ["001","002","003","004","005"]
#    Author: yfshi@marvell.com

import subprocess
import getopt
import pickle
import re
import sys
import os
import json
import shlex
import datetime
import subprocess

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

#Return different value from gerrit query
def return_gerrit_query_jsonstr(revisions):
    global m_user
    global m_remote_server
    jsonstr = [[]] * len(revisions)
    for i in range(len(revisions)):
        cmd = "ssh -p 29418 %s@%s gerrit query --patch-sets --format=JSON commit:%s" % (m_user, m_remote_server, revisions[i])
        (status, remote_output) = run_command_status(cmd)    
        jsonstr[i] = json.loads(remote_output.split('\n')[0])
#sorted by createdOn
    jsonstr = sorted(jsonstr, key=lambda patch: patch['patchSets'][0]['createdOn'])
    return jsonstr

#Generate and return the args[i] from list jsonstr for git cherry pick
def args_from_jsonstr_list(jsonstr_list):
#    if (gerrit_patch_object == ""): sys.exit()
#git fetch ssh://buildfarm@shgit.marvell.com:29418/android/platform/frameworks/opt/telephony refs/changes/71/82171/1 && git cherry-pick FETCH_HEAD
    args = [[]] * len(jsonstr_list)
    for i in range(len(jsonstr_list)):
        projectspec = jsonstr_list[i]['project']
        r_dest_project_name = projectspec
        refspec = jsonstr_list[i]['patchSets'][0]['ref']
        if r_dest_project_name[:25] == "android/platform/manifest":
            cd_dest_project_name = ".repo/manifests"
            cd_args = "cd " + cd_dest_project_name + ";"
            gitcp_args = "git fetch ssh://" + m_user + "@" + m_remote_server + ":29418/" + r_dest_project_name + " " + refspec + " && git cherry-pick FETCH_HEAD;cd -;ln -sf manifests/default.xml .repo/manifest.xml;repo sync;"
        else:
            cd_dest_project_name = generate_path(r_dest_project_name)
            cd_args = "cd " + cd_dest_project_name + ";"
            gitcp_args = "git fetch ssh://" + m_user + "@" + m_remote_server + ":29418/" + r_dest_project_name + " " + refspec + " && git cherry-pick FETCH_HEAD;"
        args[i] = cd_args + gitcp_args
    return args

#Generate and return the args[i] from gerrit_patch_object for git check out for rtvb
def args_from_gerrit_patch_object_rtvb(jsonstr_list):
    args = [[]] * len(jsonstr_list)
    for i in range(len(jsonstr_list)):
        projectspec = jsonstr_list[i]['project']
        r_dest_project_name = projectspec
        refspec = jsonstr_list[i]['patchSets'][0]['ref']
        if r_dest_project_name[:25] == "android/platform/manifest":
            cd_dest_project_name = ".repo/manifests"
            cd_args = "cd " + cd_dest_project_name + ";"
            gitcp_args = "git fetch ssh://" + m_user + "@" + m_remote_server + ":29418/" + r_dest_project_name + " " + refspec + " && git checkout FETCH_HEAD;cd -;ln -sf manifests/default.xml .repo/manifest.xml;repo sync;"
        else:
            cd_dest_project_name = generate_path_rtvb(r_dest_project_name)
            cd_args = "cd " + cd_dest_project_name + ";"
            gitcp_args = "git fetch ssh://" + m_user + "@" + m_remote_server + ":29418/" + r_dest_project_name + " " + refspec + " && git checkout FETCH_HEAD;"
        args[i] = cd_args + gitcp_args
    return args

#generate cd path from project name of manifest.xml
def generate_path(r_dest_project_name):
    manifest_xml_path = ""
    manifest_xml_name = ""
    #manifest_file = "/home/buildfarm/aabs/odvb_work/manifest.xml"
    manifest_file = "/home/yfshi/workspace/eden-jb43/.repo/manifest.xml"
    search = ""
    pat = '\spath=\"([a-zA-Z0-9-_/]*)\"\s'
    if r_dest_project_name[:25] == "android/platform/manifest":
        manifest_xml_path = ".repo/manifests"
    elif r_dest_project_name[:17] == "android/platform/":
        search = r_dest_project_name[17:]
    elif r_dest_project_name[:8] == "android/":
        search = r_dest_project_name[8:]
    elif r_dest_project_name[:10] == "ose/linux/":
        search = r_dest_project_name[10:]
    elif r_dest_project_name[:5] == "test/":
        search = r_dest_project_name[5:]
    elif r_dest_project_name[:4] == "pie/":
        search = r_dest_project_name[4:]
    else:
        print "dest_project_name have not been definted yet, please contact buildbot admin"
        sys.exit(2)
    try:
        fp_src = open(manifest_file, 'r')
    except IOError:
        print "failed to open manifest file with read mode"
        sys.exit(2)
    for line in fp_src.readlines():
        m = re.search(search,line)
        if m:
            a = re.search(pat,line)
            if a:
                manifest_xml_path = a.group(1)
                break
            else:
                manifest_xml_path = search
        else:
            manifest_xml_path = search
    return manifest_xml_path

#generate cd path from project name of manifest.xml for rtvb
def generate_path_rtvb(r_dest_project_name):
    manifest_xml_path = ""
    manifest_xml_name = ""
    #manifest_file = "/home/buildfarm/aabs/odvb_work/manifest.xml"
    manifest_file = "/home/buildfarm/aabs/rtvb_work/.repo/manifest.xml"
    search = ""
    pat = '\spath=\"([a-zA-Z0-9-_/]*)\"\s'
    if r_dest_project_name[:25] == "android/platform/manifest":
        manifest_xml_path = ".repo/manifests"
    elif r_dest_project_name[:17] == "android/platform/":
        search = r_dest_project_name[17:]
    elif r_dest_project_name[:8] == "android/":
        search = r_dest_project_name[8:]
    elif r_dest_project_name[:10] == "ose/linux/":
        search = r_dest_project_name[10:]
    elif r_dest_project_name[:5] == "test/":
        search = r_dest_project_name[5:]
    elif r_dest_project_name[:4] == "pie/":
        search = r_dest_project_name[4:]
    else:
        print "dest_project_name have not been definted yet, please contact buildbot admin"
        sys.exit(2)
    try:
        fp_src = open(manifest_file, 'r')
    except IOError:
        print "failed to open manifest file with read mode"
        sys.exit(2)
    for line in fp_src.readlines():
        m = re.search(search,line)
        if m:
            a = re.search(pat,line)
            if a:
                manifest_xml_path = a.group(1)
                break
            else:
                manifest_xml_path = search
        else:
            manifest_xml_path = search
    return manifest_xml_path

#return revisions of first from the patch file and update the file by remove the picked patch
def return_gerrit_revisions(gerrit_patch_file):
    infile = open(gerrit_patch_file,'r')
    json_list = []
    for jsonstr in infile.readlines():
        json_list.append(json.loads(jsonstr))
    infile.close()
#read first revision and remove it from list
    revisions = json_list[0]['currentPatchSet']['revision']
    json_list.pop(0)
    outfile = open(gerrit_patch_file, 'w')
    for json_str in json_list:
        json.dump(json_str, outfile)
        outfile.write('\n')
    outfile.close()
    return revisions

#Run args[i] by shell
def run_args(args):
    for i in range(len(args)):
        print args[i]
        subprocess.check_call(args[i], shell=True)

#User help
def usage():
    print "\tgerrit_pick_patch"
    print "\t      [-p] <gerrit patchset list except patches for manifest> Eks: 001,002,003 the list is splited by ,"
    print "\t      [-t] <gerrit patch json tab file> "
    print "\t          the function design for rtvb"
    print "\t          Check-out the patch instead cherry-pick, pick the first patch from tab file, and remove it from tab file"
    print "\t      [--showonly] only show the patches from listed patchsetID"
    print "\t      [-h] help"

def main(argv):
    gerrit_patch_list = ""
    gerrit_patch_tab = ""
    args_list = []
    try:
        opts, args = getopt.getopt(argv, "p:t:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-p"):
            gerrit_patch_list = arg.split(',')
        elif opt in ("-t"):
            gerrit_patch_tab = arg

    if (gerrit_patch_list == "") and (gerrit_patch_tab == ""):
        usage()
        sys.exit(2)

    if (gerrit_patch_list != ""):
        args_list = args_from_jsonstr_list(return_gerrit_query_jsonstr(gerrit_patch_list))
        print args_list
    elif (gerrit_patch_tab != ""):
        args_list = args_from_jsonstr_list_rtvb(return_gerrit_query_jsonstr(return_gerrit_revisions(gerrit_patch_tab)))
        print args_list

    run_args(args_list)

if __name__ == "__main__":
    main(sys.argv[1:])
