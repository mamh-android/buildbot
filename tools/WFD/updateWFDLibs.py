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

#++++++++++++++++++++++++++++++++++++++++++++++++++++
# Global configurations for all platforms and branches
#--------
# (Begin)
#++++++++++++++++++++++++++++++++++++++++++++++++++++
platformWFDCodeDefs = [
{'eden-kk4.4' : {
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
             }
},
]# end of platformWFDCodeDefs

print "\nplatformWFDCodeDefs:\t", platformWFDCodeDefs

#mail
SMTP_SERVER = "10.68.76.51"
mailSubject = "Build notification of WFD from autobuild server"
fromWho = "autobuild@marvell.com"
toWho = ["lbi@marvell.com", "yfshi@marvell.com"]

#++++++++++++++++++++++++++++++++++++++++++++++++++++
# (End)
#--------
# Global configurations for all platforms and branches
#++++++++++++++++++++++++++++++++++++++++++++++++++++


optParser = OptionParser()
usage = "Usage: %prog [options]"
optParser.add_option("-m", "--mode", dest="mode", help="Autobuild, Developer, Integrator" )
optParser.add_option("-s", "--smtp", dest="smtp", help="smtp server" )
options, args = optParser.parse_args( args=sys.argv[1:] )
options.mode = "Developer" # hardcoded as developer
if options.mode != "Autobuild" and options.mode != "Developer" and options.mode != "Integrator":
    optParser.print_help()
    exit(1)

if options.smtp is not None and len(options.smtp)>0:
    SMTP_SERVER = options.smtp

def mode():
    global options
    if options.mode=="Autobuild":
        return "A"
    elif options.mode=="Developer":
        return "D"
    elif options.mode=="Integrator":
        return "I"
    else:
        return "U"

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

def probeAndroidPath():
    AndroidFoders = ["bionic", "frameworks", "hardware", "libcore", "dalvik"]
    pwdOut = os.path.dirname(os.path.abspath(__file__))
    pwd = pwdOut
    androidRoot = None
    while len(pwd) > 0:
        rc, lines = runCMD( "ls {0}".format(pwd) )
        commonItems = [val for val in AndroidFoders if val in lines]
        if len(AndroidFoders) == len(commonItems):
            androidRoot = pwd
            break;
        #strip tailing sub-drc
        lastSlashIdx = pwd.rfind("/")
        if lastSlashIdx <= 0:
            break;
        pwd = pwd[:lastSlashIdx]
    return (androidRoot, pwdOut)

### probe android dir
androidRoot, pwd = probeAndroidPath()
print "\nandroid:", androidRoot
print "    pwd:", pwd
if androidRoot is None:
    print "You are not running this script under valid Android source code!\n"
    exit(1)

### probe current platform android codebase branch name
rc,cmdOutput = runCMD( "git branch -a | grep -- '->'", workDir=androidRoot+"/.repo/manifests/")
if len(cmdOutput)==0:
    print "Can not identify android codebase branch name under its .repo/manifests folder!"
    exit(1)
pos = cmdOutput[0].rfind("/")
if pos < 0:
    print "Can not identify android codebase branch name on ", cmdOutput[0]
    exit(1)
androidBranchName = cmdOutput[0][pos+1:]
print "\nandroid branch name:{0}".format(androidBranchName)

### get the config instance for androidBranchName in $platformWFDCodeDefs 
configInstance = None
for config in platformWFDCodeDefs:
    if config[androidBranchName] is not None:
        configInstance = config[androidBranchName]
        break;
if configInstance is None:
    print "Can not find configuration for branch :", androidBranchName
print "\nconfiguration for {0} is:\t".format(androidBranchName), configInstance

'''#############################################################
1. Check if current released binaries MD5 matching its libs
   If not matched, then warning by email?
'''

'''#############################################################
2. Backup old .repo/manifests/default.xml
   Modify it for fetching wfd source code project (wfd_core_src,wfd_platform_src,wfd_vpu_src)
'''
# make sure wfd_platform, wfd_vpu projects are included in it.
repoXMLLines = []
foundWfdPlatformBinPro = False
foundWfdVpuBinPro = False
wfdSourceCodeProjects = []
f = open( androidRoot+"/.repo/manifests/default.xml", "r")
for line in f:
    repoXMLLines.append( line )

    if line.find( configInstance['wfd_core_src']['local_dir'] ) > -1 or \
       line.find( configInstance['wfd_platform_src']['local_dir'] ) > -1 or \
       line.find( configInstance['wfd_vpu_src']['local_dir'] ) > -1:
        wfdSourceCodeProjects.append( line )

    if line.find("path=\"vendor/marvell/generic/wfd_platform\"") > -1:
        leadingChars = line.find("<")
        foundWfdPlatformBinPro = True
        #add its source code projects
        repoXMLLines.append( "{0}<project name=\"{1}\" path=\"{2}\" revision=\"{3}\" />\n".format(line[:leadingChars],
                                                                                                configInstance['wfd_core_src']['git_name'],
                                                                                                configInstance['wfd_core_src']['local_dir'],
                                                                                                configInstance['wfd_core_src']['revision']) )
        repoXMLLines.append( "{0}<project name=\"{1}\" path=\"{2}\" revision=\"{3}\" />\n".format(line[:leadingChars],
                                                                                                configInstance['wfd_platform_src']['git_name'],
                                                                                                configInstance['wfd_platform_src']['local_dir'],
                                                                                                configInstance['wfd_platform_src']['revision']) )
    if line.find("path=\"vendor/marvell/generic/wfd_vpu\"") > -1:
        foundWfdVpuBinPro = True
        repoXMLLines.append( "{0}<project name=\"{1}\" path=\"{2}\" revision=\"{3}\" />\n".format(line[:leadingChars],
                                                                                                configInstance['wfd_vpu_src']['git_name'],
                                                                                                configInstance['wfd_vpu_src']['local_dir'],
                                                                                                configInstance['wfd_vpu_src']['revision']) )
f.close()

gWFDSourceCodeProjectsFoundInRepo = False
if len(wfdSourceCodeProjects) > 0:
    print "\nInfo : already found WFD sourc code projects in codebase! they are:\n"
    gWFDSourceCodeProjectsFoundInRepo = True
    for line in wfdSourceCodeProjects:
        print "\t{0}".format( line )
    print "\n"
    if mode()=="A":
        print "*** In Autobuild mode, we just stopped here!"
        exit(1)

if foundWfdPlatformBinPro==False or foundWfdVpuBinPro==False:
    print "\nNo WFD binaries projects in this codebase!\n"
    exit(1)

if gWFDSourceCodeProjectsFoundInRepo == False:
    rc,cmdOutput = runCMD( "mv default.xml default.xml.original", workDir=androidRoot+"/.repo/manifests/")
    if rc != 0:
        print "Can not backup .repo/manifests/default.xml before modifying it!"
        exit(1)
    
    f = open(androidRoot+"/.repo/manifests/default.xml", "w")
    for line in repoXMLLines:
        f.write( line )
    f.close()
    print "\nDone with modifying ", androidRoot+"/.repo/manifests/default.xml", "\n"
    gWFDSourceCodeProjectsFoundInRepo = True


'''#############################################################
3. repo sync wfd source code to their folders
'''
def pullSourceCode( local_path, root_path ):
    rc,cmdOutput = runCMD( "repo sync {0}".format( local_path ), workDir=root_path)
    if rc==0:
        print "\nInfo : pull wfd source code project success for :{0}".format( local_path )
    else:
        print "\nInfo : pull wfd source code project fail for :{0}".format( local_path )

for project_name in configInstance.keys():
    if os.path.isdir( androidRoot+"/"+configInstance[project_name]['local_dir'] )==True:
        print "For safety reason, on those already existing project do not repo sync : ", configInstance[project_name]['local_dir']
        continue
    else:
        pullSourceCode( configInstance[project_name]['local_dir'], androidRoot )

'''#############################################################
4. Backup old wfd .so, and rebuild libxml2, wfd_core_src, wfd_platform_src, wfd_vpu_src
'''
gNewlyBuiltSo = {}

def extractAndroidBuildEnvVars():
    myVars = {'TARGET_PRODUCT':''}
    sysEnv = os.environ.copy()
    myVars['TARGET_PRODUCT'] = sysEnv['TARGET_PRODUCT']
    myVars['TARGET_BUILD_VARIANT'] = sysEnv['TARGET_BUILD_VARIANT']
    return myVars

def buildSrcProject( androidRootPath, srcProjectRelativePath ):
    global gNewlyBuiltSo
    buildVars = extractAndroidBuildEnvVars()
    if len(buildVars['TARGET_PRODUCT']) == 0:
        print "Cann't find envrion variables 'TARGET_PRODUCT'!\n\t You may not setup android build environ!"
        exit(1)

    shellName = "{0}/{1}/tmpBuild.sh".format( androidRootPath, srcProjectRelativePath)
    fTmpShell = open( shellName, "w" )
    if fTmpShell is None:
        print "Cann't create tmpBuild.sh to build under", srcProjectRelativePath
        exit(1)
    fTmpShell.write( "cd {0}\n".format(androidRootPath) )
    fTmpShell.write( ". build/envsetup.sh\n" )
    fTmpShell.write( "lunch {0}-{1}\n".format( buildVars['TARGET_PRODUCT'], buildVars['TARGET_BUILD_VARIANT'] ) )
    fTmpShell.write( "cd {0}\n".format( srcProjectRelativePath ) )
    fTmpShell.write( "mm -B | grep Install\n" )
    fTmpShell.close()

    os.chmod( shellName, 0777 )

    rc,cmdOutput = runCMDNeedShellBuiltin( shellName, workDir=androidRoot + "/" + srcProjectRelativePath)
    if rc==0:
        print "\nSuccessfully built wfd src project  :", srcProjectRelativePath
        for line in cmdOutput:
            if line.startswith("Install:")==True:
                tokens = line.split()
                #print "\t\t{0}".format( tokens[1] )
                soPath = tokens[1]
                posSlash = soPath.rfind("/")
                if posSlash < 0:
                    continue
                gNewlyBuiltSo[ soPath[posSlash+1:] ] = soPath

    else:
        print "Failed building wfd src project  :", srcProjectRelativePath

# build WFD src projects
buildSrcProject( androidRoot, "external/libxml2" )
buildSrcProject( androidRoot, configInstance['wfd_core_src']['local_dir'] )
buildSrcProject( androidRoot, configInstance['wfd_platform_src']['local_dir'] )
buildSrcProject( androidRoot, configInstance['wfd_vpu_src']['local_dir'] )
for k in gNewlyBuiltSo.keys():
    print k, ":", gNewlyBuiltSo[k]
        

'''#############################################################
5. Check if the newly built wfd .so MD5 values are different from
   those previously released.
   If changed, then submit a patch on wfd_vpu/wfd_platform.
'''
def md5( filePath ):
    rc,cmdOutput = runCMD( "md5sum {0}".format(filePath) )
    if rc != 0 or len(cmdOutput)!=1:
        print "\nError: cannot calc md5sum for", filePath
        exit(1)
    mdVal = cmdOutput[0].split()[0]
    return mdVal

def getComparedMD5Sum( wfdBinProjectPath, androidRootPath, newBuiltSo ):
    rc,cmdOutput = runCMD( "find . -iname '*.so'", workDir=androidRoot+"/" + wfdBinProjectPath)
    if rc != 0:
        print "\nFailed to find .so under", wfdBinProjectPath
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
md5Result = getComparedMD5Sum( binProjectPath, androidRoot, gNewlyBuiltSo )
md5Info[ binProjectPath ] = md5Result
#wfd_vpu
binProjectPath = "vendor/marvell/generic/wfd_vpu"
md5Result = getComparedMD5Sum( binProjectPath, androidRoot, gNewlyBuiltSo )
md5Info[ binProjectPath ] = md5Result

reportString = ""
def report(strVal):
    global reportString
#reportString = reportString + strVal + "\r\n"
    print strVal
    
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
    </table>
    </p>

    <p>{2}</p>
  </body>

</html>
'''.format( getHostName(), getDateTime(), generateHtmlTable( md5Info ) )

sendMail( SMTP_SERVER, mailSubject, fromWho, toWho, plainText, htmlText)


print "Done"
