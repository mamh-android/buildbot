#!/usr/bin/env python
from multiprocessing import Process, Queue, Pipe, Lock, Value, Array, Manager, Pool
import subprocess
import os
import signal
import sys
import time
from optparse import OptionParser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#  git push ssh://lbi@shgit.marvell.com:29418/android/shared/Buildbot/buildbot.git HEAD:refs/for/master

#++++++++++++++++++++++++++++++++++++++++++++++++++++
# Global configurations for all platforms and branches
#--------
# (Begin)
#++++++++++++++++++++++++++++++++++++++++++++++++++++
platformWFDCodeDefs = {
'eden-kk4.4' : {
                    'wfd_core_src' :   {
                              'git_name':'vendor/marvell/generic/wfd_core',     # git project name (stripped suffix ".git")
                              'revision':'mrvl-kk4.4',                          # revision
                             'local_dir':'vendor/marvell/generic/wfd_core_src', # local path
                    },
                    'wfd_platform_src':{
                              'git_name':'vendor/marvell/generic/marvell-wifidisplay',
                              'revision':'mrvl-kk4.4',
                             'local_dir':'vendor/marvell/generic/wfd_platform_src',
                    },
                    'wfd_vpu_src':     {
                              'git_name':'vendor/marvell/generic/wfdhantro',
                              'revision':'master',
                             'local_dir':'vendor/marvell/generic/wfd_vpu_src'
                    },
             },
'rls_eden_kk4.4_dev_z2' : 'eden-kk4.4', # same as 'eden-kk4.4'
'rls_pxa988_kk4.4_T7_beta2' : {
                    'wfd_core_src' :   {
                              'git_name':'vendor/marvell/generic/wfd_core',
                              'revision':'mrvl-kk4.4',
                             'local_dir':'vendor/marvell/generic/wfd_core_src',
                    },
                    'wfd_platform_src':{
                              'git_name':'vendor/marvell/generic/marvell-wifidisplay',
                              'revision':'mrvl-kk4.4',
                             'local_dir':'vendor/marvell/generic/wfd_platform_src',
                    },
                    'wfd_vpu_src':     {
                              'git_name':'vendor/marvell/generic/wfdcoda7542',
                              'revision':'mrvl-kk4.4',
                             'local_dir':'vendor/marvell/generic/wfd_vpu_src'
                    },
             },
}# end of platformWFDCodeDefs

# resolve reference
for branchName in platformWFDCodeDefs.keys():
    if isinstance( platformWFDCodeDefs[branchName], str ) and platformWFDCodeDefs[branchName] in platformWFDCodeDefs.keys():
        platformWFDCodeDefs[ branchName ] = platformWFDCodeDefs[ platformWFDCodeDefs[ branchName ] ]

### dictionary variable to save global variables
gVars = {}
gVars['smtp_server'] = "10.68.76.51" # default
gVars['mail_subject']= "Build notification of WFD from autobuild server"
gVars['mail_from_who'] = "autobuild@marvell.com"
gVars['mail_to_who'  ] = ["lbi@marvell.com","mamh@marvell.com"]
gVars['mail_to_who_autobuild'] = ["mamh@marvell.com"]

#++++++++++++++++++++++++++++++++++++++++++++++++++++
# (End)
#--------
# Global configurations for all platforms and branches
#++++++++++++++++++++++++++++++++++++++++++++++++++++


optParser = OptionParser()
usage = "Usage: %prog [options]"
optParser.add_option("-m", "--mode", dest="mode", help="Autobuild , Developer , Integrator" )
optParser.add_option("-a", "--android", dest="androidRootPath", help="Android codebase root path" )
optParser.add_option("-p", "--product", dest="product", help="Android build combo value" )
optParser.add_option("-s", "--smtp", dest="smtp", help="smtp server" )
optParser.add_option("-l", dest="listConfigurations", action="store_true", help="List all platform/branch configurations." )
options, args = optParser.parse_args( args=sys.argv[1:] )

gCmdLine = " ".join( sys.argv )
print "cmd-line:", gCmdLine

count = 0
if options.listConfigurations == True:
    print "\n"
    print "=========================================================="
    print "| List all platform/branch WFD source code configurations"
    print "=========================================================="
    allConfigs = platformWFDCodeDefs
    for branch in allConfigs.keys():
        count += 1
        print " -------------"
        print "| ({0}) {1} : ".format( count, branch )
        print " -------------"
        for pro in allConfigs[branch].keys():
            print "        " + pro + " : "
            for so in allConfigs[branch][pro].keys():
                print "                    " + so + "  :  " + allConfigs[branch][pro][so]
    print "\n\n"
    exit(0)


if options.mode != "Autobuild" and options.mode != "Developer" and options.mode != "Integrator":
    optParser.print_help()
    exit(0)

# save run mode value
gVars['run_mode'] = options.mode

# check if user request to specify SMTP server
if options.smtp is not None and len(options.smtp)>0:
    gVars['smtp_server'] = options.smtp

if gVars['run_mode']=="Autobuild":
    gVars['mail_to_who'].extend( gVars['mail_to_who_autobuild'] )
    if options.androidRootPath is None or len(options.androidRootPath)==0 or options.product is None or len(options.product)==0:
        print "In Autobuild mode, please input -a <android-root-path> and -p <product-variant>\n"
        optParser.print_help()
        exit(0)

# function : run shell command to get result
def runCMD( cmd , workDir=None):
    if workDir is None:
        p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=workDir)
    p.wait()
    printedLines = []
    for line in p.stdout.readlines():
        line = line.replace("\n","")
        printedLines.append( line )
    return (p.returncode, printedLines)

# function : run shell that may invoke shell builtin commmands
def runCMDNeedShellBuiltin( cmd , workDir=None):
    if workDir is None:
        p = subprocess.Popen( cmd, shell=True, executable="/bin/bash", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        p = subprocess.Popen( cmd, shell=True, executable="/bin/bash", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=workDir)
    p.wait()
    printedLines = []
    for line in p.stdout.readlines():
        line = line.replace("\n","")
        printedLines.append( line )
    return (p.returncode, printedLines)

# function : probe android codebase root path
def probeAndroidPath( startingPath ):
    AndroidFoders = ["bionic", "frameworks", "hardware", "libcore", "dalvik"]
    pwd = startingPath
    androidRoot = None
    while len(pwd) > 0:
        rc, lines = runCMD( "ls {0}".format(pwd) )
        commonItems = [val for val in AndroidFoders if val in lines]
        if len(AndroidFoders) == len(commonItems):
            androidRoot = pwd
            break;
        #strip tailing sub-dir
        lastSlashIdx = pwd.rfind("/")
        if lastSlashIdx <= 0:
            break;
        pwd = pwd[:lastSlashIdx]
    return androidRoot

### probe android dir
androidRoot = None
if gVars['run_mode']=="Autobuild":
    androidRoot = probeAndroidPath( options.androidRootPath )
else:
    androidRoot = probeAndroidPath( os.environ['PWD'] )
#    androidRoot = probeAndroidPath( os.path.dirname(os.path.abspath(__file__)) )

if androidRoot is None:
    print "Can not identify where is the android codebase!\n"
    exit(0)

# save android codebase root path
gVars['android_root_path'] = androidRoot
gVars['script_path'] = os.path.dirname(os.path.abspath(__file__))

gHistoryLog = []
def modeLog( msg ):
    global gVars
    global gHistoryLog
    s = "[mode : {0}] {1}".format( gVars['run_mode'], msg )
    print s
    gHistoryLog.append( s )

def printList( lis ):
    for line in lis:
        modeLog( line )

def getHostName():
    rc,cmdOutput = runCMD( "hostname" )
    if rc==0 and len(cmdOutput)==1:
        return cmdOutput[0]
    else:
        return "unknown"

def getDateTime():
    rc,cmdOutput = runCMD( "date +%T-%m/%d/%Y" )
    if rc==0 and len(cmdOutput)==1:
        return cmdOutput[0]
    else:
        return "unknown"

def sendMail( smtpServer, subject, fromWho, toWho, plainText, htmlText ):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = fromWho
    msg['To'] = ", ".join(toWho)
    part1 = MIMEText( plainText, 'plain' )
    part2 = MIMEText( htmlText, 'html' )
    msg.attach( part1 )
    msg.attach( part2 )
    error = None
    try:
        s = smtplib.SMTP( smtpServer )
        s.sendmail( fromWho, toWho, msg.as_string() )
        s.quit()
    except SMTPRecipientsRefused:
        error = "sendmail raised exception : SMTPRecipientsRefused"
    except SMTPHeloError:
        error = "sendmail raised exception : SMTPHeloError"
    except SMTPSenderRefused:
        error = "sendmail raised exception : SMTPSenderRefused"
    except SMTPDataError:
        error = "sendmail raised exception : SMTPDataError"

    return error

def sendReportMail( htmlContent ):
    global gVars

    plainText = ""
    htmlText = '''
    <html>

    <style type="text/css"
    </style>

    <head>
      <title> Checking WFD binaries </title>
    </head>

    <body>
    <p>
    <table>
      <tr>
        <td>build machine host name</td>
        <td> <font style="font-weight:bold;">{0}</font> </td>
      </tr>
      <tr>
        <td>build time</td>
        <td> <font style="font-weight:bold;">{1}</font> </td>
      </tr>
      <tr>
        <td>Build Mode</td>
        <td> <font style="font-weight:bold;">{2}</font> </td>
      </tr>
      <tr>
        <td>Build Command Line</td>
        <td> <font style="font-weight:bold;">{3}</font> </td>
      </tr>
    </table>
    </p>

    <p>{4}</p>
    </body>

    </html>
    '''.format( getHostName(), getDateTime(), gVars['run_mode'], gCmdLine, htmlContent )
    sendMail( gVars['smtp_server'], gVars['mail_subject'], gVars['mail_from_who'], gVars['mail_to_who'  ], plainText, htmlText)

def sendFailMail( lastMsg = None ):
    global gHistoryLog
    html="<table border=0>"
    html += '''<tr><th style="font-weight:bold; background-color:red">Failure logs</th></tr>'''
    for line in gHistoryLog:
        html += '''<tr><td>{0}</td></tr>'''.format( line )
    if lastMsg is not None:
        html += '''<tr><td style="background-color:red">{0}</td></tr>'''.format( line )
    html += "</table>"
    sendReportMail( html )

# function : get android platform android codebase branch name
def getAndroidPlatformBranchName( runMode, androidRootPath ):
    rc,cmdOutput = runCMD( "git branch -a | grep -- '->'", workDir=androidRootPath+"/.repo/manifests/")
    if len(cmdOutput)==0:
        modeLog( "Can not identify android codebase branch name under its .repo/manifests folder!" )
        exit(0)
    pos = cmdOutput[0].rfind("/")
    if pos < 0:
        modeLog("Can not identify android codebase branch name on %s" %(cmdOutput[0]) )
        exit(0)
    return cmdOutput[0][pos+1:]

# Get android release branch name
gVars['android_release_branch'] = getAndroidPlatformBranchName( gVars['run_mode'], gVars['android_root_path'] )


### get the config instance for androidBranchName in $platformWFDCodeDefs
configInstance = None
if gVars['android_release_branch'] in platformWFDCodeDefs.keys():
    configInstance = platformWFDCodeDefs[ gVars['android_release_branch'] ]
if configInstance is None:
    modeLog( "Can not find configuration for branch :" + gVars['android_release_branch'] )
    exit(0)

#print "\nconfiguration for {0} is:\t".format( gVars['android_release_branch'] ), configInstance

print "\nSetting of current platform/branch : ", gVars['android_release_branch']
print " -------------"
print "|", gVars['android_release_branch']
print " -------------"
for project in configInstance.keys():
    print "    "+project+" :"
    for so in configInstance[project].keys():
        print "                    %s : %s" % ( so, configInstance[project][so] )
print "\n"

# Get wfd src code projects info
gVars['wfd_projects_info'] = configInstance

################### Prepare source code #############################

def repoSyncSourceCode( local_path, root_path ):
    rc,cmdOutput = runCMD( "repo sync {0}".format( local_path ), workDir=root_path)
    if rc==0:
        modeLog( "Info : Succeeded pull wfd source code project for :{0}".format( local_path ) )
    else:
        modeLog( "Info : Failed pull wfd source code project for :{0}".format( local_path ) )
        modeLog( "[IN] local_path=%s, root_path=%s" %( local_path, root_path ) )
        for line in cmdOutput:
            modeLog( line )
        sendFailMail()
        exit(1)

def prepareWFDSourceCode_Developer( gV ):
    ### Backup old .repo/manifests/default.xml
    ### Modify it for fetching wfd source code project (wfd_core_src,wfd_platform_src,wfd_vpu_src)
    ###==============================================================

    # make sure wfd_platform, wfd_vpu projects are included in it.
    repoXMLLines = []
    foundWfdPlatformBinPro = False
    foundWfdVpuBinPro = False
    wfdSourceCodeProjects = []
    f = open( gV['android_root_path']+"/.repo/manifests/default.xml", "r")
    for line in f:
        repoXMLLines.append( line )
        if line.find(    gV['wfd_projects_info']['wfd_core_src']['local_dir'] ) > -1 \
           or line.find( gV['wfd_projects_info']['wfd_platform_src']['local_dir'] ) > -1 \
           or line.find( gV['wfd_projects_info']['wfd_vpu_src']['local_dir'] ) > -1:
            wfdSourceCodeProjects.append( line )
        if line.find("path=\"vendor/marvell/generic/wfd_platform\"") > -1:
            leadingChars = line.find("<")
            foundWfdPlatformBinPro = True
            #add its source code projects
            repoXMLLines.append( "{0}<project name=\"{1}\" path=\"{2}\" revision=\"{3}\" />\n".format(line[:leadingChars],
                                                                                                      gV['wfd_projects_info']['wfd_core_src']['git_name'],
                                                                                                      gV['wfd_projects_info']['wfd_core_src']['local_dir'],
                                                                                                      gV['wfd_projects_info']['wfd_core_src']['revision']) )
            repoXMLLines.append( "{0}<project name=\"{1}\" path=\"{2}\" revision=\"{3}\" />\n".format(line[:leadingChars],
                                                                                                      gV['wfd_projects_info']['wfd_platform_src']['git_name'],
                                                                                                      gV['wfd_projects_info']['wfd_platform_src']['local_dir'],
                                                                                                      gV['wfd_projects_info']['wfd_platform_src']['revision']) )
        if line.find("path=\"vendor/marvell/generic/wfd_vpu\"") > -1:
            foundWfdVpuBinPro = True
            repoXMLLines.append( "{0}<project name=\"{1}\" path=\"{2}\" revision=\"{3}\" />\n".format(line[:leadingChars],
                                                                                                      gV['wfd_projects_info']['wfd_vpu_src']['git_name'],
                                                                                                      gV['wfd_projects_info']['wfd_vpu_src']['local_dir'],
                                                                                                      gV['wfd_projects_info']['wfd_vpu_src']['revision']) )
    f.close()
    foundWFDSourceCodeProjectsInRepo = False
    if len(wfdSourceCodeProjects) > 0:
        modeLog( "\nInfo : already found WFD sourc code projects in codebase! they are:\n" )
        foundWFDSourceCodeProjectsInRepo = True
        for line in wfdSourceCodeProjects:
            modeLog( "\t{0}".format( line ) )
        modeLog( "\n" )

    if foundWfdPlatformBinPro==False or foundWfdVpuBinPro==False:
        modeLog( "\nNo WFD binaries projects in this codebase!\n" )
        return False

    if foundWFDSourceCodeProjectsInRepo== False:
        rc,cmdOutput = runCMD( "mv default.xml default.xml.original", workDir=gV['android_root_path']+"/.repo/manifests/")
        if rc != 0:
            modeLog("Can not backup .repo/manifests/default.xml before modifying it!" )
            return False

        f = open( gV['android_root_path']+"/.repo/manifests/default.xml", "w")
        for line in repoXMLLines:
            f.write( line )
        f.close()
        modeLog( "\nDone with modifying "+ gV['android_root_path'] +"/.repo/manifests/default.xml\n" )

    for project_name in gV['wfd_projects_info'].keys():
        if os.path.isdir( gV['android_root_path']+"/"+gV['wfd_projects_info'][project_name]['local_dir'] )==True:
            modeLog( "For safety reason, on those already existing project do not repo sync : " + gV['wfd_projects_info'][project_name]['local_dir'] )
            continue
        else:
            repoSyncSourceCode( gV['wfd_projects_info'][project_name]['local_dir'], gV['android_root_path'] )

    return True

def prepareWFDSourceCode_Autobuild( gV ):
    for project_name in gV['wfd_projects_info'].keys():
        if os.path.isdir( gV['android_root_path']+"/"+gV['wfd_projects_info'][project_name]['local_dir'] )==True:
            modeLog( "Error! The wfd source code project already exists under : " + gV['wfd_projects_info'][project_name]['local_dir'] )
            return False
        rc,cmdOutput = runCMD( "git clone -b {0} ssh://shgit.marvell.com/git/android/{1}.git {2}".format( gV['wfd_projects_info'][project_name]['revision'],
                                                                                                          gV['wfd_projects_info'][project_name]['git_name'],
                                                                                                          gV['wfd_projects_info'][project_name]['local_dir']),
                               workDir=gV['android_root_path'] )
        if rc==0:
            modeLog( "Succeeded git clone source code : " + gV['wfd_projects_info'][project_name]['local_dir'] )
        else:
            modeLog( "Failed to git clone source code : " + gV['wfd_projects_info'][project_name]['local_dir'] )
            for line in cmdOutput:
                modeLog( line )
            return False
    return True


isOK = False
if gVars['run_mode']=="Autobuild":
    isOK = prepareWFDSourceCode_Autobuild( gVars )
else:
    isOK = prepareWFDSourceCode_Developer( gVars )
if isOK==False:
    modeLog( "Failed to prepare WFD source code projects!\n" )
    sendFailMail()
    exit(1)

modeLog( "Completed wfd source code preparation! \n" )

''' ****************************************** '''

'''#############################################################
4. Backup old wfd .so, and rebuild libxml2, wfd_core_src, wfd_platform_src, wfd_vpu_src
'''
gNewlyBuiltSo = {}

def extractAndroidBuildEnvVars( gV ):
    gV['TARGET_PRODUCT'] = ''
    sysEnv = os.environ.copy()
    gV['TARGET_PRODUCT'] = sysEnv['TARGET_PRODUCT']
    gV['TARGET_BUILD_VARIANT'] = sysEnv['TARGET_BUILD_VARIANT']
    modeLog( " option of lunch is set as : {0}-{1}".format( gV['TARGET_PRODUCT'], gV['TARGET_BUILD_VARIANT']) )
    return True

def buildSrcProject( androidRootPath, srcProjectRelativePath, gV, ignoredErros=False ):
    global gNewlyBuiltSo
    if len(gV['TARGET_PRODUCT']) == 0:
        modeLog( "Cann't find envrion variables 'TARGET_PRODUCT'!\n\t You may not setup android build environ!" )
        return False

    shellName = "{0}/{1}/tmpBuild.sh".format( androidRootPath, srcProjectRelativePath)
    fTmpShell = open( shellName, "w" )
    if fTmpShell is None:
        modeLog( "Cann't create tmpBuild.sh to build under", srcProjectRelativePath )
        return False
    fTmpShell.write( "cd {0}\n".format(androidRootPath) )
    fTmpShell.write( ". build/envsetup.sh\n" )
    fTmpShell.write( "lunch {0}-{1}\n".format( gV['TARGET_PRODUCT'], gV['TARGET_BUILD_VARIANT'] ) )
    fTmpShell.write( "cd {0}\n".format( srcProjectRelativePath ) )
    fTmpShell.write( "mm -B | grep Install\n" )
    fTmpShell.close()

    os.chmod( shellName, 0777 )

    rc,cmdOutput = runCMDNeedShellBuiltin( shellName, workDir=androidRootPath + "/" + srcProjectRelativePath)
    if rc==0:
        modeLog( "Successfully built wfd src project  : " + srcProjectRelativePath )
        for line in cmdOutput:
            if line.startswith("Install:")==True:
                tokens = line.split()
                soPath = tokens[1]
                posSlash = soPath.rfind("/")
                if posSlash < 0:
                    continue
                gNewlyBuiltSo[ soPath[posSlash+1:] ] = soPath
        return True

    else:
        if ignoredErros==False:
            modeLog( "Failed building wfd src project  : " + srcProjectRelativePath )
            printList(  cmdOutput )
            return False
        else:
            return True
    return True

# build WFD src projects
if gVars['run_mode']=="Autobuild":
    sProductVariant = options.product;
    posSep = sProductVariant.find("-")
    gVars['TARGET_PRODUCT'] = sProductVariant[:posSep]
    gVars['TARGET_BUILD_VARIANT'] = sProductVariant[posSep+1:]
else:
    extractAndroidBuildEnvVars( gVars )


if buildSrcProject( gVars['android_root_path'], "vendor/marvell/external/live555", gVars, False ) == False:
    sendFailMail()
    exit(1)

if buildSrcProject( gVars['android_root_path'], "external/libxml2", gVars, True ) == False:
    sendFailMail()
    exit(1)

if buildSrcProject( gVars['android_root_path'], gVars['wfd_projects_info']['wfd_core_src']['local_dir'], gVars, False ) == False:
    sendFailMail()
    exit(1)

if buildSrcProject( gVars['android_root_path'], gVars['wfd_projects_info']['wfd_platform_src']['local_dir'], gVars, False ) == False:
    sendFailMail()
    exit(1)

if buildSrcProject( gVars['android_root_path'], gVars['wfd_projects_info']['wfd_vpu_src']['local_dir'], gVars, False ) == False:
    sendFailMail()
    exit(1)

for k in gNewlyBuiltSo.keys():
    modeLog( k + " : " + gNewlyBuiltSo[k] )
# Save the newly built share libraries info
gVars['newly_built_libs'] = gNewlyBuiltSo

'''#############################################################
5. Check if the newly built wfd .so MD5 values are different from
   those previously released.
   If changed, then submit a patch on wfd_vpu/wfd_platform.
'''
def md5( filePath ):
    rc,cmdOutput = runCMD( "md5sum {0}".format(filePath) )
    if rc != 0 or len(cmdOutput)!=1:
        modeLog( "Error: cannot calc md5sum for" + filePath )
        sendFailMail()
        exit(1)
    mdVal = cmdOutput[0].split()[0]
    return mdVal

def getComparedMD5Sum( wfdBinProjectPath, androidRootPath, newBuiltSo ):
    rc,cmdOutput = runCMD( "find . -iname '*.so'", workDir=androidRoot+"/" + wfdBinProjectPath)
    if rc != 0:
        modeLog( "Failed to find .so under" + wfdBinProjectPath )
        sendFailMail()
        exit(1)
    result = {}
    for line in cmdOutput:
        posSlash = line.rfind("/")
        soName = line[posSlash+1:]
        result[ soName ] = { 'old-md5':'', 'new-md5':'', 'md5-diff':False }
        oldMD5Sum = md5( androidRootPath + "/"  +wfdBinProjectPath + "/" + line )
        result[ soName ]['old-md5'] = oldMD5Sum
        if soName in newBuiltSo.keys():
            newMD5Sum = md5( androidRootPath + "/" + newBuiltSo[soName] )
            result[ soName ]['new-md5'] = newMD5Sum
        if result[ soName ]['old-md5'] != result[ soName ]['new-md5']:
            result[soName]['md5-diff'] = True
    return result

# md5 overall
md5Info = {}
#wfd_platform
binProjectPath = "vendor/marvell/generic/wfd_platform"
md5Result = getComparedMD5Sum( binProjectPath, gVars['android_root_path'], gVars['newly_built_libs'] )
md5Info[ binProjectPath ] = md5Result
#wfd_vpu
binProjectPath = "vendor/marvell/generic/wfd_vpu"
md5Result = getComparedMD5Sum( binProjectPath, gVars['android_root_path'], gVars['newly_built_libs'] )
md5Info[ binProjectPath ] = md5Result

# Save the calculated md5 info
gVars['projects_libs_info'] = md5Info

'''
****************************************************************
*********************** To report result ***********************
****************************************************************
'''

def report(strVal):
    modeLog( strVal )

report( "MD5 overall:" )
for p in md5Info.keys():
    report( "\t%s:" %(p) )
    projectMD5Info = md5Info[p]
    for soName in projectMD5Info.keys():
        report( "\t\t%s:" %(soName) )
        k = 'old-md5'
        report( "\t\t\t{0}\t:\t{1}".format( k, projectMD5Info[soName][k] ) )
        k = 'new-md5'
        report( "\t\t\t{0}\t:\t{1}".format( k, projectMD5Info[soName][k] ) )
        k = 'md5-diff'
        report( "\t\t\t{0}\t:\t{1}".format( k, projectMD5Info[soName][k] ) )

def generateHtmlTable( md5Info ):
    html="<table border=1>"
    heads = ['project', 'lib', 'old-md5', 'new-md5', 'diff']
    html += "<tr><th>" + "</th><th>".join(heads) + "</th></tr>"
    for p in md5Info.keys():
        projectMD5Info = md5Info[p]
        for soName in projectMD5Info.keys():
            k = 'md5-diff'
#if projectMD5Info[soName][k] == True:
#                html += "<tr style=\"background-color:red\">"
#            else:
            html += "<tr>"

            html += "<td>" + p + "</td>"
            html += "<td>" + soName + "</td>"
            k = 'old-md5'
            html += "<td>" + projectMD5Info[soName][k] + "</td>"
            k = 'new-md5'
            html += "<td>" + projectMD5Info[soName][k] + "</td>"
            k = 'md5-diff'
            if projectMD5Info[soName][k] == True:
                html += "<td style=\"background-color:red\">Different</td>"
            else:
                html += "<td style=\"background-color:green\">==</td>"
            html += "</tr>"
    html += "</table>"
    return html
# do send report mail
sendReportMail( generateHtmlTable( md5Info ) )


print "Done"
exit(0)
