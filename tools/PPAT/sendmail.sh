#!/bin/bash
USER="buildfarm"
PPAT_SERVER="10.38.32.212"
ssh $USER@$PPAT_SERVER /home/buildfarm/ppat/send_email_notification.sh $@
