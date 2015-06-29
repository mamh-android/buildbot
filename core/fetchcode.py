#!/usr/bin/python
# v1.0
#   Fetch code from source server

import getopt
import re
import subprocess
import sys

# Return 0 for success. Return negative for failure.
def verify_prefix(manifest_path):
    for prefix in ["http://", "https://", "ssh://", "git://"]:
        pat = re.compile(prefix)
        result = pat.search(manifest_path)
        if result != None:
            return 0
    return -1

def repo_init(src_manifest_path, manifest_branch, manifest_xml, addition):
    if (verify_prefix(src_manifest_path) < 0):
        print "prefix in manifest path is invalid"
        sys.exit(2)

    if manifest_branch != "":
        arg = "repo init -u " + src_manifest_path + " -b " + manifest_branch + addition
    elif manifest_xml != "":
        arg = "cp -f " + manifest_xml + " .repo/manifests/"
        subprocess.check_call(arg, shell=True)
        arg = "repo init " + " -m " + manifest_xml + addition
    print "====",arg
    process = subprocess.Popen(arg, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Input Your name, Your email, Is it correct
    process.communicate("\n\ny\n")[0]
    subprocess.check_call("repo sync -q --jobs=8", shell=True)

def usage():
    print "fetchcode -u {manifest url} | [-b {manifest branch}] | [-m {manifest xml}]"
    print "          [--repo-url={url}] | [--reference={url}]"

def main(argv):
    print "====",argv
    print ""

    manifest_url = ""
    manifest_branch = ""
    manifest_xml = ""
    addition = ""
    try:
        opts, args = getopt.getopt(argv, "b:u:m:h", ["reference=", "repo-url="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in "-b":
            manifest_branch = arg
        elif opt in "-u":
            manifest_url = arg
        elif opt in "-m":
            manifest_xml = arg
        elif opt in ("--reference"):
            addition += " --reference=" + arg
        elif opt in ("--repo-url"):
            addition += " --repo-url=" + arg

    if manifest_url == "":
        usage()
        sys.exit(2)
    elif ((manifest_branch == "") and (manifest_xml == "")):
        usage()
        sys.exit(2)
    elif ((manifest_branch != "") and (manifest_xml != "")):
        usage()
        sys.exit(2)

    repo_init(manifest_url, manifest_branch, manifest_xml, addition)

if __name__ == "__main__":
    main(sys.argv[1:])
