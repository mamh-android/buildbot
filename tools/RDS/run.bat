@echo off
rem ***************************************
rem windows daily task scheduler
rem use forfile to release the disk space under \android\autobuild
rem Author: yfshi@marvell.com
rem ***************************************

set workingdir=C:\RDS\
set loglocation=%workingdir%etc\logs\releaseautobuild.txt
set olderthan3m=90
set olderthan6m=180
set olderthan1y=365
set source=D:\autobuild\android
set email=yfshi@marvell.com
set blat=%workingdir%blat\full\blat.exe
set extension=tgz
set relayserver=localhost
set subject="Disk Release.bat Report"
set releaselist=%workingdir%etc\kill.txt
set final_releaselist=%workingdir%etc\newkill.txt
set nonlist=%workingdir%etc\nonlist.txt

rem if exist %loglocation% del %loglocation%
if exist %releaselist% del %releaselist%
if exist %final_releaselist% del %final_releaselist%

echo %subject%>>%loglocation%
date /t >>%loglocation%
time /t >>%loglocation%

echo Deleting files older than %olderthan3m% days with the file extension *.%extension%.
echo Deleting files older than %olderthan3m% days with the file extension *.%extension%.>>%loglocation%
echo Deleting *.* files older than %olderthan6m% days except manifest.xml and changlogs*. 
echo Deleting *.* files older than %olderthan6m% days except manifest.xml and changlogs*.>>%loglocation%
echo This file may take an extremely long time to run while it looks unresponsive.
echo Check %loglocation% for progress.
echo Release List located at %releaselist%

rem cd %source%

rem ***add *.tgz older than 90 days into the releaselist***

echo Creating List of files older than 90 days to be removed: 
echo Creating List of files older than 90 days to be removed:>>%loglocation%

FORFILES /p %source% /s /d -%olderthan3m% /m *.%extension% /c "CMD /C Echo @path>>%releaselist%
rem FORFILES /p %source% /s /d -%olderthan3m% /m *.%extension% /c "CMD /C Echo @path>>%loglocation%

echo Starting delete...
echo Starting delete...>>%loglocation%
date /t >> %loglocation%
time /t >> %loglocation%

rem *** Removing the files from the %releaselist% listed ***
for /f "tokens=*" %%a in (%releaselist%) do del %%a

if exist %releaselist% del %releaselist%
if exist %final_releaselist% del %final_releaselist%

rem ***add *.* files older than 180 days into the releaselist***

echo Creating List of files older than 180 days to be removed: 
echo Creating List of files older than 180 days to be removed:>>%loglocation%

FORFILES /p %source% /s /d -%olderthan6m% /m *.* /c "CMD /C Echo @path>>%releaselist%
rem FORFILES /p %source% /s /d -%olderthan6m% /m *.* /c "CMD /C Echo @path>>%loglocation%

rem ***remove the manifest and changelog from the releaselist***
echo remove the manifest and changelog from the releaselist
findstr /v /g:%nonlist% %releaselist% > %final_releaselist%

echo List of files in the %final_releaselist% to be removed:
echo List of files in the %final_releaselist% to be removed:>>%loglocation%

echo Starting delete...
echo Starting delete...>>%loglocation%
date /t >> %loglocation%
time /t >> %loglocation%

rem *** Removing the files from the %final_releaselist% listed ***
for /f "tokens=*" %%a in (%final_releaselist%) do del %%a

rem *** delete all the empty directory ***
if exist %releaselist% del %releaselist%
dir /ad/b/s %source% | sort /r >> %releaselist%
for /f "tokens=*" %%i in (%releaselist%) do rd "%%i"

echo Delete finished...>>%loglocation%
date /t >>%loglocation%
time /t >>%loglocation%

rem ***************************************
rem sent report
rem use blat sent the releaselog
rem Author: yfshi@marvell.com
rem ***************************************
rem echo Delete finished... Sending Report.
rem set server=%computername%
rem %blat% %loglocation% -t %email% -s "%server% %subject%" -server %relayserver% -f do-not-reply@%server%
rem echo Report sent!
