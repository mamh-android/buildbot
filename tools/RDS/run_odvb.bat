@echo off
rem ***************************************
rem windows daily task scheduler
rem use forfile to release the disk space under \android\autobuild
rem Author: yfshi@marvell.com
rem ***************************************

set workingdir=C:\RDS\
set loglocation=%workingdir%etc\logs\releaseodvb.txt
set olderthan1w=7
set olderthan3m=90
set olderthan6m=180
set olderthan1y=365
set source=D:\autobuild\odvb
set email=yfshi@marvell.com
set blat=%workingdir%blat\full\blat.exe
set relayserver=localhost
set subject="Disk Release.bat Report"
set releaselist=%workingdir%etc\odvbkill.txt
set emptylist=%workingdir%etc\odvbempty.txt

rem if exist %loglocation% del %loglocation%
if exist %releaselist% del %releaselist%

echo %subject%>>%loglocation%
date /t >>%loglocation%
time /t >>%loglocation%

echo Deleting *.* files older than %olderthan1w% days. 
echo Deleting *.* files older than %olderthan1w% days.>>%loglocation%
echo This file may take an extremely long time to run while it looks unresponsive.
echo Check %loglocation% for progress.
echo Release List located at %releaselist%

rem cd %source%

rem ***add *.* files older than 7 days into the releaselist***

echo Creating List of files older than 7 days to be removed: 
echo Creating List of files older than 7 days to be removed:>>%loglocation%

FORFILES /p %source% /s /d -%olderthan1w% /m * /c "CMD /C Echo @path>>%releaselist%
rem FORFILES /p %source% /s /d -%olderthan1w% /m *.* /c "CMD /C Echo @path>>%loglocation%

echo Starting delete...
echo Starting delete...>>%loglocation%
date /t >> %loglocation%
time /t >> %loglocation%

rem *** Removing the files from the %releaselist% listed ***
for /f "tokens=*" %%a in (%releaselist%) do del %%a

rem *** delete all the empty directory ***
if exist %emptylist% del %emptylist%
dir /ad/b/s %source% | sort /r >> %emptylist%
for /f "tokens=*" %%i in (%emptylist%) do rd "%%i"

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
