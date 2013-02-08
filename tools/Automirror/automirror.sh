#!/bin/bash
. ~/buildbot_script/buildbot/core/check_update.sh
cd /mnt/mirror && . ~/buildbot_script/buildbot/tools/Automirror/auto_mirror.sh
