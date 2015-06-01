#!/usr/bin/python
# v1.0
#    current it only support gerrit 2.4.2 database structure

import subprocess
import getopt
import pickle
import re
import sys
import os
import csv
from datetime import datetime, timedelta

#Gerrit admin user
m_user = "buildfarm"

#Code remote server
m_remote_server = "shgit.marvell.com"

#return table from gerrit database by singel patch path, branch, and patch status.
def return_gerrit_changes(path, branch, gerrit_open):
    global m_user
    global m_remote_server
    #use regexp end must match
    path=path + '$'
    args = "ssh -p 29418 " + m_user + "@" + m_remote_server + " gerrit gsql -c \"select\ *\ from\ changes\ WHERE\ dest_branch_name=\\\'refs/heads/" + branch +  "\\\'\ AND\ open=\\\'" + gerrit_open + "\\\'\ AND\ dest_project_name\ REGEXP\ \\\'" + path + "\\\'\""
    a = []
    if gerrit_open == "X":
        f = open('tmptxt', 'w')
        f.write(os.popen(args).read())
        f.close()
        in_txt = csv.reader(open("tmptxt", "rb"), delimiter = '|')
        for row in in_txt:
            print row
            a.append(row)
        a.pop(1)
        a.pop(len(a)-1)
    else:
        f = open('tmptxt', 'w')
        f.write(os.popen(args).read())
        f.close()
        in_txt = csv.reader(open("tmptxt", "rb"), delimiter = '|')
        for row in in_txt:
            a.append(row)
        a.pop(0)
        a.pop(0)
        a.pop(len(a)-1)
    for i in range(len(a)):
        for j in range(len(a[i])):
            a[i][j]=a[i][j].strip()
    #print "******************* write in csv ****************"
    #print a
    #print "******************* write in csv ****************"
    return a

#setup gerrit patch change csv
def setup_gerrit_changes_csv(fout, d_path, d_branch):
    out_csv = csv.writer(open(fout, 'wb'))
    out_csv.writerows(return_gerrit_changes("X", "X", "X"))
    for name, c_path in d_path.items():
        branch = d_branch.get(name)
        print name
        print branch
        out_csv.writerows(return_gerrit_changes(c_path, branch, "Y"))

#return array via matching patch_set_approvals
def return_via_patch_approvals(in_array, category, value, change_open):
    global m_user
    global m_remote_server
    out_array = []
    out_array.extend(in_array)
    for rows in in_array:
        a = []
        args = "ssh -p 29418 " + m_user + "@" + m_remote_server + " gerrit gsql -c \"select\ *\ from\ patch_set_approvals\ WHERE\ VALUE=\\\'" + value +  "\\\'\ AND\ CHANGE_OPEN=\\\'" + change_open + "\\\'\ AND\ CATEGORY_ID=\\\'" + category + "\\\'\ AND\ CHANGE_ID=\\\'" + rows[13].strip() + "\\\'\ AND\ PATCH_SET_ID=\\\'" + rows[9].strip() +"\\\'\""
        f = open('tmptxt', 'w')
        f.write(os.popen(args).read())
        f.close()
        in_txt = csv.reader(open("tmptxt", "rb"), delimiter = '|')
        for row in in_txt:
            a.append(row)
        a.pop(0)
        a.pop(0)
        a.pop(len(a)-1)
        if not a:
            print "changeid with [" + rows[13].strip() + "] is empty patch_set_approvals"
            out_array.remove(rows)
    return out_array

#return array via unmatching patch_set_approvals
def return_umatch_patch_approvals(in_array, category, value, change_open):
    global m_user
    global m_remote_server
    out_array = []
    out_array.extend(in_array)
    for rows in in_array:
        a = []
        args = "ssh -p 29418 " + m_user + "@" + m_remote_server + " gerrit gsql -c \"select\ *\ from\ patch_set_approvals\ WHERE\ VALUE=\\\'" + value +  "\\\'\ AND\ CHANGE_OPEN=\\\'" + change_open + "\\\'\ AND\ CATEGORY_ID=\\\'" + category + "\\\'\ AND\ CHANGE_ID=\\\'" + rows[13].strip() + "\\\'\ AND\ PATCH_SET_ID=\\\'" + rows[9].strip() +"\\\'\""
        f = open('tmptxt', 'w')
        f.write(os.popen(args).read())
        f.close()
        in_txt = csv.reader(open("tmptxt", "rb"), delimiter = '|')
        for row in in_txt:
            a.append(row)
        a.pop(0)
        a.pop(0)
        a.pop(len(a)-1)
        if a:
            print "changeid with [" + rows[13].strip() + "] is " + category + "=" + value + ". Remove from the array"
            out_array.remove(rows)
    return out_array

#return array remove row via datetime. date=<1/2/3/4/5/x> over x days
def return_via_datetime(in_array, date):
    out_array = []
    out_array.extend(in_array)
    #return date N days ago
    print "****************remove " + str(date) + " days**********************"
    date_N_days_ago = datetime.now() - timedelta(days=date)
    for rows in in_array:
        if str(date_N_days_ago)>rows[2]:
            out_array.remove(rows)
    #print "************** return out_array *****************"
    #print out_array
    return out_array

#setup csv via unmatch "verfied +1", "reviewed -1/-2" "date great than 5 days" for rtvb
def setup_for_rtvb(fout, d_path, d_branch):
    print "Setup patches csv for rtvb"
    out_csv = csv.writer(open(fout, 'wb'))
    #out_csv.writerows(return_gerrit_changes("X", "X", "X"))
    tmp_array=[]
    for name, c_path in d_path.items():
        branch = d_branch.get(name)
        print name
        print branch
        #Create all list
        for row in return_gerrit_changes(c_path, branch, "Y"):
            tmp_array.append(row)
    #Remove date great then 10 days from list
    tmp_array = return_via_datetime(tmp_array, 10)
    #Remove CRVW -2 from list
    tmp_array = return_umatch_patch_approvals(tmp_array, "Code-Review", "-2", "Y")
    #Remove CRVW -1 from list
    tmp_array = return_umatch_patch_approvals(tmp_array, "Code-Review", "-1", "Y")
    #Remove VRIF +1 from list
    tmp_array = return_umatch_patch_approvals(tmp_array, "Verified", "1", "Y")
    #sorted by LAST_UPDATED_ON
    tmp_array.sort(key=lambda a: a[2])
    out_csv.writerows(tmp_array)

#setup gerrit patch change csv with patch_set_approvals
def setup_gerrit_changes_via_approvals(fout, d_path, d_branch, category, value):
    out_csv = csv.writer(open(fout, 'wb'))
    out_csv.writerows(return_gerrit_changes("X", "X", "X"))
    for name, c_path in d_path.items():
        branch = d_branch.get(name)
        print name
        print branch
        array_all = return_gerrit_changes(c_path, branch, "Y")
        out_csv.writerows(return_via_patch_approvals(array_all, category, value, "Y"))

#User help
def usage():
    print "\tcreate_csv [-o] <output file>"
    print "\t      [-b] {branch file from getname}"
    print "\t      [-p] {path file from getname}"
    print "\t      [--rtvb] create a csv for rtvb by specfied rule"
    print "\t      [--review=] R+-2/V+-2/S Sample --review=R+2/--review=S/--review=V-1"
    print "\t              R=Code Review V=Verified S=Submit"
    print "\t      [-h] help"

def main(argv):
    fout = ""
    branch_list = ""
    path_list = ""
    review_value = ""
    review_category = ""
    rtvb = ""
    try:
        opts, args = getopt.getopt(argv, "o:b:p:h", ["rtvb", "review="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-o"):
            fout = arg
            print fout
        elif opt in ("-b"):
            branch_list = arg
            print branch_list
        elif opt in ("-p"):
            path_list = arg
            print path_list
        elif opt in ("--rtvb"):
            rtvb = "ture"
        elif opt in ("--review"):
            print arg
            if arg[1:2] == "" and arg[:1] == "S":
                review_value = "1"
                review_category = "SUBM"
            elif arg[1:2] == "+" and (arg[2:] == "1" or arg[2:] == "2"):
                review_value = arg[2:]
                if arg[:1] == "R":
                    review_category = "Code-Review"
                elif arg[:1] == "V":
                    review_category = "Verified"
                else:
                    usage()
                    sys.exit(2)
            elif arg[1:2] == "-" and (arg[2:] == "1" or arg[2:] == "2"):
                review_value = arg[1:]
                if arg[:1] == "R":
                    review_category = "Code-Review"
                elif arg[:1] == "V":
                    review_category = "Verified"
                else:
                    usage()
                    sys.exit(2)
            else:
                usage()
                sys.exit(2)
            print review_category
            print review_value
    if fout == "" or branch_list == "" or path_list == "":
        usage()
        sys.exit(2)
    fp = open(path_list, "r")
    d_path = pickle.load(fp)
    fp.close()
    fp = open(branch_list, "r")
    d_branch = pickle.load(fp)
    fp.close()
    if rtvb == "ture":
        setup_for_rtvb(fout, d_path, d_branch)
    elif not review_category:
        setup_gerrit_changes_csv(fout, d_path, d_branch)
    else:
        setup_gerrit_changes_via_approvals(fout, d_path, d_branch, review_category, review_value)

if __name__ == "__main__":
    main(sys.argv[1:])
