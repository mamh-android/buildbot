#!/bin/bash

GERRIT_PATCH=
MANIFEST_XML=
MANIFEST_BRANCH=
DEST_DIR=
PLATFORM_ANDROID_VARIANT=
ABS_BUILD_DEVICES=
USEREMAIL=
BUILDTYPE=
build_maintainer="yfshi@marvell.com"
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
PACKAGE_LINK=$( awk -F"<result-dir>|</result-dir>" ' /<result-dir>/ { print $2 } ' $STD_LOG )
DEV_TEAM="APSE-SE2"

help() {
  if [ -n "$1" ]; then
    echo "Error: $1"
    echo
  fi
  echo "HELP!!!!"
  echo "-e [useremail] -t [build type]"
  echo "-e -t"
  exit 1
}

validate_parameters() {
  if [ $# -lt 1 ]; then
    help
  fi
  while [ $# -gt 0 ];
  do
    case "$1" in
      "-e")
        if [ -z "$2" ]; then
          help "Please give a valid useremail."
        fi
        USEREMAIL=$2
        ;;
      "-t")
        if [ -z "$2" ]; then
          help "Please give a valid build type."
        fi
        BUILDTYPE=$2
#        shift 1
#        continue
        ;;
    esac
    shift 1
  done
}

generate_error_notification_email() {
cat <<-EOF
From: $build_maintainer
To: $USEREMAIL
Subject: [$BUILDTYPE] is failed! please check

This is an automated email from the autobuild script. It was
generated because an error encountered while $BUILDTYPE.
Please check the build log below and fix the error.

Last part of build log is followed:
=========================== Build LOG =====================

$(tail -100 $STD_LOG 2>/dev/null)

===========================================================

Complete Time: $(date)
Build Host: $(hostname)

---
Team of $DEV_TEAM
EOF
}

generate_success_notification_email() {
cat <<-EOF
From: $build_maintainer
To: $USEREMAIL
Subject: [$BUILDTYPE] is done.

This is an automated email from the autobuild script. It was
generated because your triggered $BUILDTYPE is success.

You can get the package from:
$PACKAGE_LINK

Complete Time: $(date)
Build Host: $(hostname)

---
Team of $DEV_TEAM
EOF
}

send_error_notification() {
  echo "generating error notification email"
  generate_error_notification_email  | /usr/sbin/sendmail -t $build_maintainer
}

send_success_notification() {
  echo "generating success notification email"
  generate_success_notification_email | /usr/sbin/sendmail -t $build_maintainer
}

validate_parameters $*

result=`grep ">PASS<" $STD_LOG`
if [ -n "$result" ]; then
  send_success_notification
  exit 0
else
  send_error_notification
  exit 0
fi
