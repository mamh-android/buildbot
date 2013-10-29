#!/usr/bin/python
# v1.0
#    Cherry pick patches from git server by gerrit patchsetID
#    patchsetID should be a list, such as ["001","002","003","004","005"]
#    current it only support gerrit 2.4.2 database structure
#    Author: yfshi@marvell.com

import subprocess
import getopt
import pickle
import re
import sys
import os
import csv

#Gerrit admin user
m_user = "buildfarm"

#Code remote server
m_remote_server = "shgit.marvell.com"

# Internal variable
LAST_GERRIT_CSV = "last_gerrit_review.csv"

#Return different value from gerrit database of one patchsetID(revision)
def get_from_gerritid(revision, mark):
    global m_user
    global m_remote_server
    if mark in ("revision", "uploader_account_id", "draft", "patch_set_id"):
        table="patch_sets"
        args="ssh -p 29418 " + m_user + "@" + m_remote_server + " gerrit gsql -c \"select\ " + mark + "\ from\ " + table + "\ where\ revision\=\\\'" + revision + "\\\'\" | head -3 | tail -1"
    elif mark in ("change_key", "created_on", "last_updated_on", "sort_key", "owner_account_id", "dest_project_name", "dest_branch_name", "open", "status", "nbr_patch_sets", "current_patch_set_id", "subject", "topic", "last_sha1_merge_tested", "mergeable", "row_version", "change_id"):
        table="patch_sets"
        tmp_mark=mark
        mark="change_id"
        args="ssh -p 29418 " + m_user + "@" + m_remote_server + " gerrit gsql -c \"select\ " + mark + "\ from\ " + table + "\ where\ revision\=\\\'" + revision + "\\\'\" | head -3 | tail -1"
        change_id=os.popen(args).read()
        change_id=change_id.strip()
        table="changes"
        mark=tmp_mark
        args="ssh -p 29418 " + m_user + "@" + m_remote_server + " gerrit gsql -c \"select\ " + mark + "\ from\ " + table + "\ where\ change_id\=\\\'" + change_id + "\\\'\" | head -3 | tail -1"
    else:
        print "mark = " + mark + " is invalid"
        sys.exit(2)
    r_text=os.popen(args).read()
    r_text=r_text.strip()
    return r_text

#Define gerrit patch object array class
class Gerrit_patch:
    def __init__(self, change_key, created_on, last_updated_on, sort_key, owner_account_id, dest_project_name, dest_branch_name, gerrit_open, status, nbr_patch_sets, current_patch_set_id, subject, topic, last_sha1_merge_tested, mergeable, row_version, change_id, revision, uploader_account_id, draft, patch_set_id):
        self.change_key = change_key
        self.created_on = created_on
        self.last_updated_on = last_updated_on
        self.sort_key = sort_key
        self.owner_account_id = owner_account_id
        self.dest_project_name = dest_project_name
        self.dest_branch_name = dest_branch_name
        self.gerrit_open = gerrit_open
        self.status = status
        self.nbr_patch_sets = nbr_patch_sets
        self.current_patch_set_id = current_patch_set_id
        self.subject = subject
        self.topic = topic
        self.last_sha1_merge_tested = last_sha1_merge_tested
        self.mergeable = mergeable
        self.row_version = row_version
        self.revision = revision
        self.uploader_account_id = uploader_account_id
        self.draft = draft
        self.change_id = change_id
        self.patch_set_id = patch_set_id
    def __repr__(self):
        return repr((self.change_key, self.created_on, self.last_updated_on, self.sort_key, self.owner_account_id, self.dest_project_name, self.dest_branch_name, self.gerrit_open, self.status, self.nbr_patch_sets, self.current_patch_set_id, self.subject, self.topic, self.last_sha1_merge_tested, self.mergeable, self.row_version, self.change_id, self.revision, self.uploader_account_id, self.draft, self.patch_set_id))

#Return a gerrit_patch_object from revision_list, which include all the value of the gerrit table changes and patch_sets
def setup_gerrit_patch_object(revision_list):
    print "Start generating the gerrit patch object from gerrit database"
    gerrit_patch_object = [[]] * len(revision_list)
    for i in range(len(revision_list)):
        print "generating the gerrit patch object %d" %i
        r_dest_project_name = get_from_gerritid(revision_list[i], "dest_project_name")
        m = re.search(r'manifest',r_dest_project_name)
#if dest project name is for manifest set created_on is 0, the pacth will be move to top of the list when sorted by created on
        if m:
            gerrit_patch_object[i] = Gerrit_patch(get_from_gerritid(revision_list[i], "change_key"), "0", get_from_gerritid(revision_list[i], "last_updated_on"), get_from_gerritid(revision_list[i], "sort_key"), get_from_gerritid(revision_list[i], "owner_account_id"), get_from_gerritid(revision_list[i], "dest_project_name"), get_from_gerritid(revision_list[i], "dest_branch_name"), get_from_gerritid(revision_list[i], "open"), get_from_gerritid(revision_list[i], "status"), get_from_gerritid(revision_list[i], "nbr_patch_sets"), get_from_gerritid(revision_list[i], "current_patch_set_id"), get_from_gerritid(revision_list[i], "subject"), get_from_gerritid(revision_list[i], "topic"), get_from_gerritid(revision_list[i], "last_sha1_merge_tested"), get_from_gerritid(revision_list[i], "mergeable"), get_from_gerritid(revision_list[i], "row_version"), get_from_gerritid(revision_list[i], "change_id"), get_from_gerritid(revision_list[i], "revision"), get_from_gerritid(revision_list[i], "uploader_account_id"), get_from_gerritid(revision_list[i], "draft"), get_from_gerritid(revision_list[i], "patch_set_id"))
        else:
            gerrit_patch_object[i] = Gerrit_patch(get_from_gerritid(revision_list[i], "change_key"), get_from_gerritid(revision_list[i], "created_on"), get_from_gerritid(revision_list[i], "last_updated_on"), get_from_gerritid(revision_list[i], "sort_key"), get_from_gerritid(revision_list[i], "owner_account_id"), get_from_gerritid(revision_list[i], "dest_project_name"), get_from_gerritid(revision_list[i], "dest_branch_name"), get_from_gerritid(revision_list[i], "open"), get_from_gerritid(revision_list[i], "status"), get_from_gerritid(revision_list[i], "nbr_patch_sets"), get_from_gerritid(revision_list[i], "current_patch_set_id"), get_from_gerritid(revision_list[i], "subject"), get_from_gerritid(revision_list[i], "topic"), get_from_gerritid(revision_list[i], "last_sha1_merge_tested"), get_from_gerritid(revision_list[i], "mergeable"), get_from_gerritid(revision_list[i], "row_version"), get_from_gerritid(revision_list[i], "change_id"), get_from_gerritid(revision_list[i], "revision"), get_from_gerritid(revision_list[i], "uploader_account_id"), get_from_gerritid(revision_list[i], "draft"), get_from_gerritid(revision_list[i], "patch_set_id"))
    print "generating the gerrit patch is done, %d patch has been generated" %len(revision_list)
    return gerrit_patch_object

#sort and return gerrit_patch_object by mark (created_on)
def sort_gerrit_patch_object_by_created_on(gerrit_patch_object):
    gerrit_patch_object = sorted(gerrit_patch_object, key=lambda patch: patch.created_on)
    return gerrit_patch_object

#generate cd path from project name of manifest.xml
def generate_path(r_dest_project_name):
    manifest_xml_path = ""
    manifest_xml_name = ""
    manifest_file = "/home/buildfarm/aabs/odvb_work/manifest.xml"
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

#Generate and return the args[i] from gerrit_patch_object for git cherry pick
def args_from_gerrit_patch_object(gerrit_patch_object):
#    if (gerrit_patch_object == ""): sys.exit()
    args = [[]] * len(gerrit_patch_object)
    for i in range(len(gerrit_patch_object)):
        r_change_id = gerrit_patch_object[i].change_id
        r_patch_set_id = gerrit_patch_object[i].patch_set_id
        r_dest_project_name = gerrit_patch_object[i].dest_project_name
        r_dest_branch_name = gerrit_patch_object[i].dest_branch_name
        r_patch_folder = ""
        if len(r_change_id) < 2:
            r_patch_folder = r_change_id.zfill(2)
        elif len(r_change_id) > 1:
            r_patch_folder = r_change_id[-2:]
        else:
            print "change_id = " + r_change_id + " is invalid"
            sys.exit(2)
        if r_dest_project_name[:25] == "android/platform/manifest":
            cd_dest_project_name = ".repo/manifests"
            cd_args = "cd " + cd_dest_project_name + ";"
            gitcp_args = "git fetch ssh://" + m_user + "@" + m_remote_server + ":29418/" + r_dest_project_name + " refs/changes/" + r_patch_folder + "/" + r_change_id + "/" + r_patch_set_id + " && git cherry-pick FETCH_HEAD;cd -;ln -sf manifests/default.xml .repo/manifest.xml;repo sync;"
        else:
            cd_dest_project_name = generate_path(r_dest_project_name)
            cd_args = "cd " + cd_dest_project_name + ";"
            gitcp_args = "git fetch ssh://" + m_user + "@" + m_remote_server + ":29418/" + r_dest_project_name + " refs/changes/" + r_patch_folder + "/" + r_change_id + "/" + r_patch_set_id + " && git cherry-pick FETCH_HEAD;"
        args[i] = cd_args + gitcp_args
    return args

#Generate and return the args[i] from gerrit_patch_object for git show
def args_gitshow_from_gerrit_patch_object(gerrit_patch_object):
#    if (gerrit_patch_object == ""): sys.exit()
    args = [[]] * len(gerrit_patch_object)
    for i in range(len(gerrit_patch_object)):
        r_change_id = gerrit_patch_object[i].change_id
        r_patch_set_id = gerrit_patch_object[i].patch_set_id
        r_dest_project_name = gerrit_patch_object[i].dest_project_name
        r_dest_branch_name = gerrit_patch_object[i].dest_branch_name
        r_patch_folder = ""
        if len(r_change_id) < 2:
            r_patch_folder = r_change_id.zfill(2)
        elif len(r_change_id) > 1:
            r_patch_folder = r_change_id[-2:]
        else:
            print "change_id = " + r_change_id + " is invalid"
            sys.exit(2)
        gitcp_args = "git fetch ssh://" + m_user + "@" + m_remote_server + ":29418/" + r_dest_project_name + " refs/changes/" + r_patch_folder + "/" + r_change_id + "/" + r_patch_set_id + " && git format-patch -1 --stdout FETCH_HEAD;"
        args[i] = gitcp_args
    return args

#Return revision from changID and patchset
def return_revision(change_id, patch_set_id):
    global m_user
    global m_remote_server
    table="patch_sets"
    args = "ssh -p 29418 " + m_user + "@" + m_remote_server + " gerrit gsql -c \"select\ revision\ from\ " + table + "\ WHERE\ change_id=\\\'" + change_id +  "\\\'\ AND\ patch_set_id=\\\'" + patch_set_id + "\\\'\" | head -3 | tail -1"
    r_text=os.popen(args).read()
    r_text=r_text.strip()
    return r_text

#return gerrit patch list via csv
def return_gerrit_changes(gerrit_patch_csv):
    a = []
    in_txt = csv.reader(open(gerrit_patch_csv, "rb"), delimiter = ',')
    for row in in_txt:
        rev_list = return_revision(row[14].strip(), row[10].strip())
        a.append(rev_list)
    a.pop(0)
    if (os.path.exists(LAST_GERRIT_CSV)):
        ignore_list = []
        in_txt = csv.reader(open(LAST_GERRIT_CSV, "rb"), delimiter = ',')
        for row in in_txt:
            rev_list = return_revision(row[14].strip(), row[10].strip())
            ignore_list.append(rev_list)
        ignore_list.pop(0)
    else:
        ignore_list = []
    #ignore_list = ['803bafa44521262584fad12de9ad8e5ed697fee2', '69d218cb25a60ee9495e492277fe8b31b4c88878', 'c17afaff4741d08dda389b81b97f4423aec3da97', '40e7f4d41f4039b400375f15119928b9f33cff91', '3c98b9a6b0665259fec8c0c4871495a1a69bebec', '03f1623c5ec97ebaf5f68c2415343701d763ecce', '845fb555b0ef88266497975a5210c935e9f6c501', 'd940ef7c92a1ad94b7735c065972f70d42a55db8', '208e961efefaae564049537ebc448e826414209b', '25a7338dfb1a29d66a59d2aaa0a7172b2adca800', 'ac365c27f34f1c66f9545d564cc131dd90dc1cf9', '0aa28d8e4a4966da0eada4053d6cb45e3485105f']
    print "The last ignore list is:"
    print ignore_list
    for x in ignore_list:
        a.remove(x)
    return a

#Run args[i] by shell
def run_args(args):
    for i in range(len(args)):
        print args[i]
        subprocess.check_call(args[i], shell=True)

#User help
def usage():
    print "\tgerrit_pick_patch [-m] <gerrit patchsetID for manifest>"
    print "\t      [-p] <gerrit patchset list except patches for manifest> Eks: 001,002,003 the list is splited by ,"
    print "\t      [-t] <gerrit patch tab.csv file> "
    print "\t      [--showonly] only show the patches from listed patchsetID"
    print "\t      [-h] help"

def main(argv):
    gerrit_patch_manifest = ""
    gerrit_patch_list = ""
    gerrit_patch_csv = ""
    showonly = ""
    gerrit_patch_manifest_object = ""
    gerrit_patch_list_object = ""
    gerrit_patch_csv_object = ""
    args_gerrit_patch_manifest_object = ""
    args_gerrit_patch_list_object = ""
    try:
        opts, args = getopt.getopt(argv, "m:p:t:h", ["showonly","username","remote"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-m"):
            gerrit_patch_manifest = arg.split(',')
        elif opt in ("-p"):
            gerrit_patch_list = arg.split(',')
        elif opt in ("-t"):
            gerrit_patch_csv = arg
        elif opt in ("--showonly"):
            showonly = 1

    if (gerrit_patch_manifest == "") and (gerrit_patch_list == "") and (gerrit_patch_csv == ""):
        usage()
        sys.exit(2)
    if (gerrit_patch_manifest != ""):
        gerrit_patch_manifest_object = setup_gerrit_patch_object(gerrit_patch_manifest)
        gerrit_patch_manifest_object = sort_gerrit_patch_object_by_created_on(gerrit_patch_manifest_object)
    if (gerrit_patch_list != ""):
        gerrit_patch_list_object = setup_gerrit_patch_object(gerrit_patch_list)
        gerrit_patch_list_object = sort_gerrit_patch_object_by_created_on(gerrit_patch_list_object)
    if (gerrit_patch_csv != ""):
        gerrit_patch_list = return_gerrit_changes(gerrit_patch_csv)
        gerrit_patch_csv_object = setup_gerrit_patch_object(gerrit_patch_list)
        gerrit_patch_csv_object = sort_gerrit_patch_object_by_created_on(gerrit_patch_list_object)
        print gerrit_patch_csv_object
    if (showonly == 1):
        args_gerrit_patch_manifest_object = args_gitshow_from_gerrit_patch_object(gerrit_patch_manifest_object)
        args_gerrit_patch_list_object = args_gitshow_from_gerrit_patch_object(gerrit_patch_list_object)
        args_gerrit_patch_csv_object = args_gitshow_from_gerrit_patch_object(gerrit_patch_csv_object)
    else:
        args_gerrit_patch_manifest_object = args_from_gerrit_patch_object(gerrit_patch_manifest_object)
        args_gerrit_patch_list_object = args_from_gerrit_patch_object(gerrit_patch_list_object)
        args_gerrit_patch_csv_object = args_from_gerrit_patch_object(gerrit_patch_csv_object)
    run_args(args_gerrit_patch_manifest_object)
    run_args(args_gerrit_patch_list_object)
    run_args(args_gerrit_patch_csv_object)

if __name__ == "__main__":
    main(sys.argv[1:])
