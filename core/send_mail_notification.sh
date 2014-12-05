#!/bin/bash
GERRIT_PATCH=
MANIFEST_XML=
MANIFEST_BRANCH=
DEST_DIR=
PLATFORM_ANDROID_VARIANT=
ABS_BUILD_DEVICES=
USEREMAIL=
BUILDTYPE=
BRANCH_NAME=
TAG_NAME=
GITACCESS_FILE=
BUILD_NUMBER=
build_maintainer="yfshi@marvell.com"
buildbot_url="http://10.38.34.92:8010/builders/"
STD_LOG=/home/buildfarm/buildbot_script/stdio.log
PACKAGE_LINK=$( awk -F"<result-dir>|</result-dir>" ' /<result-dir>/ { print $2 } ' $STD_LOG )
DEV_TEAM="APSE-SE2"
PUBLISH_SERVER=/APSE_Release

help() {
  if [ -n "$1" ]; then
    echo "Error: $1"
    echo
  fi
  echo "HELP!!!!"
  echo "-e [useremail] -t [build type] -b [branch name] -a [tag name] -n [build number] -p [gerrit patch list] -m [manifest.xml]"
  echo "-e -t -b -a -n -p"
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
        ;;
      "-b")
        if [ -z "$2" ]; then
          help "Please give a valid branch name."
        fi
        BRANCH_NAME=$2
        ;;
      "-a")
        if [ -z "$2" ]; then
          help "Please give a valid tag name."
        fi
        TAG_NAME=$2
        ABS_DEVICE=${TAG_NAME%%_*}
        ABS_RLS=${TAG_NAME%.*}
        tmp=${TAG_NAME##*.}
        ABS_TAG=${tmp#*-}
        ;;
      "-n")
        if [ -z "$2" ]; then
          help "Please give a valid build number."
        fi
        BUILD_NUMDER=$2
        ;;
      "-p")
        if [ -z "$2" ]; then
          help "Please give a valid gerrit patch list."
        fi
        GERRIT_PATCH=$2
        ;;
      "-m")
        if [ -z "$2" ]; then
          help "Please give a valid manifest.xml."
        fi
        MANIFEST_XML=$2
        MANIFEST_NAME=$(basename $MANIFEST_XML)
        BUILD_DIR=$(dirname $MANIFEST_XML)
        ;;
    esac
    shift 1
  done
}

#Generate mail
generate_error_notification_email() {
cat <<-EOF
From: $build_maintainer
To: $USEREMAIL
Subject: [$BUILDTYPE] is failed! please check

This is an automated email from the autobuild script. It was
generated because an error encountered while $BUILDTYPE.

BuildBot Url: $buildbot_url$BUILDTYPE/builds/$BUILD_NUMDER

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

generate_odvb_success_notification_email() {
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

generate_uprb_success_notification_email() {
cat <<-EOF
From: $build_maintainer
To: $USEREMAIL,gqxu@marvell.com,
Subject: [$BUILDTYPE] is done.

This is an automated email from the autobuild script. It was
generated because your triggered $BUILDTYPE is success.

.gitaccess file is attached. Please forward this mail and upload the .gitaccessfile

Complete Time: $(date)
Build Host: $(hostname)

---
Team of $DEV_TEAM
EOF
uuencode $GITACCESS_FILE ${GITACCESS_FILE##/*/}
}

#Send mail
send_error_notification() {
  echo "generating error notification email"
  generate_error_notification_email  | /usr/sbin/sendmail -t $build_maintainer
  if [ $BUILDTYPE == "on_demand_virtual_build" ];then
    echo "update gerrit review"
    ./core/gerrit_review_update.py -p $GERRIT_PATCH -m $MANIFEST_XML -r "failure"
  fi
}

send_odvb_success_notification() {
  echo "generating odvb success notification email"
  generate_odvb_success_notification_email | /usr/sbin/sendmail -t $build_maintainer
  echo "update gerrit review"
  ./core/gerrit_review_update.py -p $GERRIT_PATCH -m $MANIFEST_XML -r "success" -d $PACKAGE_LINK
}

send_uprb_success_notification() {
  echo "generating uprb success notification email"
  GITACCESS_FILE=$(./core/create_gitaccess.py -b $BRANCH_NAME -t $TAG_NAME)
  echo "gitaccess file "$GITACCESS_FILE
  cp $GITACCESS_FILE $BUILD_DIR
  if [ ! -f ${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG}/$(basename $GITACCESS_FILE) ] && [ -d ${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG} ]; then
    cp $GITACCESS_FILE ${PUBLISH_SERVER}/${ABS_DEVICE}/$(basename $BUILD_DIR)-${ABS_TAG}
  fi
  generate_uprb_success_notification_email | /usr/sbin/sendmail -t $build_maintainer
}

validate_parameters $*

case "$BUILDTYPE" in
  "on_demand_virtual_build")
    result=`grep ">PASS<" $STD_LOG`
    if [ -n "$result" ]; then
      send_odvb_success_notification
      exit 0
    else
      send_error_notification
      exit 0
    fi
  ;;
  "upload_public_release_build")
    result=`grep "upload finished!" $STD_LOG`
    if [ -n "$result" ]; then
      send_uprb_success_notification
      exit 0
    else
      send_error_notification
      exit 0
    fi
  ;;
  *)
    echo "$BUILDTYPE is not valid"
    exit 1
  ;;
esac
