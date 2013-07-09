#!/bin/bash
USER="buildfarm"
PPAT_SERVER="10.38.32.98"
ssh $USER@$PPAT_SERVER /home/buildfarm/ppat/send_email_notification.sh $@
