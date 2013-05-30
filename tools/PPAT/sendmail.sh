#!/bin/bash
USER="buildfarm"
PPAT_SERVER="10.38.32.203"
ssh $USER@$PPAT_SERVER /home/buildfarm/ppat/send_email_notification.sh $@
