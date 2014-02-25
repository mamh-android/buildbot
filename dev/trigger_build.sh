#!/bin/bash

get_date()
{
  echo $(date "+%Y-%m-%d %H:%M:%S")
}

MSBuild Cosmo.sln /t:Rebuild
RET=$?
    if [ $RET -eq 0 ]; then
        echo "Cosmo_build: [$(get_date)] success, exit value $RET"
        echo "success"
        exit 0
    else
        echo "Cosmo_build: [$(get_date)] failure, exit value $RET"
        echo "failed"
        exit 1
    fi
