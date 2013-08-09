# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members
from buildbot.status.buildrequest import BuildRequestStatus
from buildbot.status.web.test import Test
from buildbot.schedulers.timed import Nightly
from twisted.web import html
from twisted.web.util import Redirect
import urllib, time
from twisted.python import log
from twisted.internet import defer
#from buildbot.status.web.builder import ForceBuildActionResource
from buildbot import interfaces
from buildbot.status.web.base import HtmlResource, BuildLineMixin, \
    path_to_build, path_to_slave, path_to_builder, path_to_change, \
    path_to_root, path_to_trigger, path_to_query, getAndCheckProperties, ICurrentBox, build_get_class, \
    map_branches, path_to_authfail, ActionResource

from buildbot.status.web.build import BuildsResource, StatusResourceBuild
from buildbot import util
from buildbot.process.properties import Properties

class TriggerBuild(HtmlResource, BuildLineMixin):
    pageTitle = "Trigger build"
    addSlash = True
    def __init__(self):
        HtmlResource.__init__(self)

    @defer.deferredGenerator
    def content(self, request, cxt):
        cxt['url'] = path_to_root(request) + "trigger/force"
        status = self.getStatus(request)
        master = status.master
        self.schedulers = status.getSchedulers()
        branches = []
        for i in self.schedulers:
            branches.append(i.branch)
        cxt['branch_names'] = branches
        s = self.getStatus(request);
        cxt['devslavenum'] = len(s.getBuilder('android_develop_build').getSlaves())
        cxt['relslavenum'] = len(s.getBuilder('android_release_build').getSlaves())

        template = request.site.buildbot_service.templates.get_template("trigger.html")
        template.autoescape = True
        yield template.render(**cxt)
    
    def getChild(self, path, req):
    	buildername = req.args.get('selected', [""])[0]
        builder_status = self.getStatus(req).getBuilder(buildername)
        if path == "force":
            return Force(builder_status)

        return HtmlResource.getChild(self, path, req)
        

class Force(ActionResource):
    def __init__(self, builder_status):
        ActionResource.__init__(self)
        self.builder_status = builder_status
        self.action = "forceBuild"

    def builder(self, build, req):
        b={}
        b['buildername'] = build.getBuilderName()
        b['reason'] = build.getReason()
        b['num'] = build.getNumber()
        b['link'] = path_to_build(req, build)
        b['branch'] = build.source.branch

        when = build.getETA()
        if when is not None:
            b['when'] = util.formatInterval(when)
            b['when_time'] = time.strftime("%H:%M:%S",
                                      time.localtime(time.time() + when))

        step = build.getCurrentStep()
        # TODO: is this necessarily the case?
        if not step:
            b['current_step'] = "[waiting for Lock]"
        else:
            if step.isWaitingForLocks():
                b['current_step'] = "%s [waiting for Lock]" % step.getName()
            else:
                b['current_step'] = step.getName()

        b['stop_url'] = path_to_build(req, build) + '/stop'
        b['start_time'] = build.getTimes()[0]
        b['properties'] = build.getProperties()

        return b

        
    @defer.deferredGenerator
    def performAction(self, req):
        name = req.args.get("email", ["<unknown>"])[0]
        reason = req.args.get("reason", ["<no reason specified>"])[0]
        revision = req.args.get("revision", [""])[0]
        repository = req.args.get("repository", [""])[0]
        project = req.args.get("project", [""])[0]
        selectname = self.builder_status.getName()
        samebranch = []
        buildernames = self.getStatus(req).getBuilderNames()
        self.status = self.getStatus(req)
        master = self.getBuildmaster(req)
        limitionforeachuser = 5
        buildcountforuser = 0
        cxt = {}

        """
        we set a limition builds for each user, they can build servel(here is 5) at 
        most(the sum of pending buids and running builds). Else, an alert will be shown in
        the query page.

        FIXME: if one user build 5 or more builds at once, first, the build will be added to the buildsets
        one by one, the user will be checked and we will judge whether the user has builded too much builds.
        but the action of adding build the buildsets is asynchronous, so when the next build is checked, the former
        may have not been added to the buildsets,.
        """
        if (selectname != "android_develop_build" and selectname != "android_release_build"):
            for buildername in buildernames:
                b = self.status.getBuilder(buildername)
                cxt['current'] = [self.builder(x, req) for x in b.getCurrentBuilds()]
                #we
                for cu in cxt['current']:
                    if (cu['properties'].getProperty("email", []) == name):
                        buildcountforuser = buildcountforuser + 1
                        if (buildcountforuser == limitionforeachuser):
                            req.addCookie('overlimition', buildcountforuser, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+0.5*3600)))    
                            yield (path_to_query(req))
                            return 
                wfd = defer.waitForDeferred(
                    b.getPendingBuildRequestStatuses())
                yield wfd
                statuses = wfd.getResult()
                for pb in statuses:               
                    wfd = defer.waitForDeferred(master.db.buildsets.getBuildsetProperties(pb.bsid))
                    yield wfd
                    bsp = wfd.getResult()
                #try: the bsp may do not have the email key,
                    try:
                        if (bsp["email"][0] == name):
                            buildcountforuser = buildcountforuser + 1
                            if (buildcountforuser == limitionforeachuser):
                                req.addCookie('overlimition', buildcountforuser, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+0.5*3600)))    
                                yield (path_to_query(req))
                                return
                    except:
                        pass
            properties = getAndCheckProperties(req)
            #add email propertie, be used to check the same user can only trigger the limition number at most. 
            #properties['username'] = name
            properties.setProperty("useremail", name, "Force build from")
            properties.setProperty("Reason", reason, "Force build from")
            wfd = defer.waitForDeferred(master.db.sourcestamps.addSourceStamp(branch = selectname + " " + time.asctime(), revision = revision, project = project, repository = repository))
            yield wfd
            ssid = wfd.getResult()
            r = ("'%s' trigger, reason: %s\n"
                 % (html.escape(name), html.escape(reason)))
            wfd = defer.waitForDeferred(master.addBuildset(
                    builderNames=[self.builder_status.getName()],
                    ssid=ssid, reason=r, properties=properties.asDict(), priority=0))
            yield wfd
            yield(path_to_query(req))
            return 

        builder_name = selectname
        if (selectname == "android_develop_build"):
            inputlen = req.args.get("len",[""])[0]
        else:
            inputlen = req.args.get("rellen",[""])[0]
        log.msg("inputlen is " + inputlen)
        inputlen = int(inputlen) + 1
        i = 0
        branches = []
        urgents = []

        #get the branch and urgent pair
        if (selectname == "android_develop_build"):
            while (i < inputlen):
                if (req.args.get("branch"+str(i), [""])[0] != ""):
                    branches.append((req.args.get("branch"+str(i), [""])[0]).strip())
                    if (req.args.get("urgent"+str(i), [""])[0] == "urgent"):
                        urgents.append("urgent")
                    else:
                        urgents.append("")
                i = i + 1
        else:
            while (i < inputlen):
                if (req.args.get("branch2"+str(i), [""])[0] != ""):
                    branches.append((req.args.get("branch2"+str(i), [""])[0]).strip())
                    if (req.args.get("urgent2"+str(i), [""])[0] == "urgent"):
                        urgents.append("urgent")
                    else:
                        urgents.append("")
                i = i + 1

        #add by zlinghu begin:20120210: get the slave status
        useableslaves = []
        idleslaves = []
        samebranch = []
        i = 0
        #builder_name = req.args.get('selected', [""])[0]
        s = self.getStatus(req)
        used_by_builder = {}
        for bname in s.getBuilderNames():
            b = s.getBuilder(bname)
            for bs in b.getSlaves():
                slavename = bs.getName()
                if slavename not in used_by_builder:
                    used_by_builder[slavename] = []
                used_by_builder[slavename].append(bname)

        """for bs in s.getSlaveNames():
            if name in used_by_builder[bs]:
                useableslaves.append(bs)
                bslave = s.getSlave(bs)
                sslave_status = s.botmaster.slaves[bs].slave_status
                runningbuilds = len(sslave_status.getRunningBuilds())
                if bslave.isConnected() and runningbuilds == 0:
                    idleslaves.append(bs)
                    """
        useableslaves_status = s.getBuilder(builder_name).getSlaves()
        for u in useableslaves_status:
            useableslaves.append(u.getName())
        while(i < len(branches)):
            for buildername in buildernames:
                b = self.status.getBuilder(buildername)
                cxt['current'] = [self.builder(x, req) for x in b.getCurrentBuilds()]
                for cu in cxt['current']:
                    if (cu['properties'].getProperty("email", []) == name):
                        buildcountforuser = buildcountforuser + 1
                        if (buildcountforuser == limitionforeachuser):
                            req.addCookie('overlimition', "5", path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+0.5*3600)))    
                            yield (path_to_query(req))
                            return 
                wfd = defer.waitForDeferred(
                    b.getPendingBuildRequestStatuses())
                yield wfd
                statuses = wfd.getResult()
                for pb in statuses:               
                    wfd = defer.waitForDeferred(master.db.buildsets.getBuildsetProperties(pb.bsid))
                    yield wfd
                    bsp = wfd.getResult()
                    #try: the bsp may do not have the email key,
                    try:
                        if (bsp["email"][0] == name):
                            buildcountforuser = buildcountforuser + 1
                            if (buildcountforuser == limitionforeachuser):
                                req.addCookie('overlimition', "5", path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+0.5*3600)))    
                                yield (path_to_query(req))
                                return
                    except:
                        pass
            branch = branches[i].strip()
            if(branch == ''):
                break
            urgent = urgents[i]
            if urgent == "urgent":
                priority = 2
            else:
                priority = 0
            i = i + 1

            for bs in useableslaves:
                #bs = us.getName() 
                bslave = s.getSlave(bs)
                sslave_status = s.botmaster.slaves[bs].slave_status
                runningbuilds = len(sslave_status.getRunningBuilds())
                if bslave.isConnected() and runningbuilds == 0:
                    idleslaves.append(bs)        
            log.msg("useableslaves,%s : idleslaves,%s\n"%(useableslaves, idleslaves))
            #add by zlinghu end
            
            cxt = {}
            bbranch = cxt['bbranch'] = []
            for buildername in buildernames:
                b = self.status.getBuilder(buildername)
                cxt['current'] = [self.builder(x, req) for x in b.getCurrentBuilds()]
                for cu in cxt['current']:
        	        if not cu['branch'] in bbranch:
        		        bbranch.append(cu['branch'])
                wfd = defer.waitForDeferred(
                    b.getPendingBuildRequestStatuses())
                yield wfd
                statuses = wfd.getResult()
                for pb in statuses:
                    wfd = defer.waitForDeferred(
                            pb.getSourceStamp())
                    yield wfd
                    source = wfd.getResult()
                    wfd = defer.waitForDeferred(
                            pb.getSubmitTime())
                    yield wfd
                    submitTime = wfd.getResult()
                    if not source.branch in bbranch:
            	        bbranch.append(source.branch)
            if not branch in cxt['bbranch']:
                master = self.getBuildmaster(req)
            #branch_validate = master.config.validation['branch']
            #revision_validate = master.config.validation['revision']
            #if not branch_validate.match(branch):
            #    log.msg("bad branch '%s'" % branch)
            #    yield Redirect(path_to_query(req))
            #if not revision_validate.match(revision):
            #    log.msg("bad revision '%s'" % revision)
            #    yield Redirect(path_to_query(req))
                properties = getAndCheckProperties(req)
            #   properties['username'] = name
                properties.setProperty("useremail", name, "Force build from")
            #if properties is None:
            #    yield Redirect(path_to_query(req))
                if not branch:
                    branch = None
		
            #if not revision:
            #    revision = None
                wfd = defer.waitForDeferred(master.db.sourcestamps.addSourceStamp(branch=branch,
           	            revision=revision, project=project, repository=repository))
                yield wfd
                ssid = wfd.getResult()
                r = ("'%s' trigger, reason: %s\n"
                     % (html.escape(name), html.escape(reason)))
                wfd = defer.waitForDeferred(master.addBuildset(
                        builderNames=[self.builder_status.getName()],
                        ssid=ssid, reason=r, properties=properties.asDict(), priority=priority))
                yield wfd
                wfd.getResult()

                bb = self.status.getBuilder(selectname)
            #judege the selected name , if the builder is release build , it can stop one of all
            #the build which are not urgent ,
            #else if it can not stop the release build
                bNames = buildernames

            #if force an urgent build ,we stop the current build which is not urgent and the submit time is 
            #the latest build
                if len(idleslaves) or priority != 2:
                    pass
            
                elif (priority == 2) and not len(idleslaves):
                #if selectname != 'Release build':
                 #   bNames.remove('Release build')
                    self.master = self.getBuildmaster(req)
                    ccxt = {}
                    ccxt['current'] = []
                    ccxt['nourgent'] = []
                    for bName in bNames: 
                        b = self.status.getBuilder(bName)
                        ccxt['current'].extend([self.builder(x, req) for x in b.getCurrentBuilds() if x.getSlavename() in useableslaves])
                    ccxt['nourgent'] = []
                    from buildbot.process import buildrequest
                    stopbuild = {}
                    for cx in ccxt['current']:
                        brid = {}
                        xx = {}
                        wfd = defer.waitForDeferred(
                                self.master.db.builds.getBuildRequestId(cx['num']))
                        yield wfd
                        brid = wfd.getResult()
                        bbrid = {}
                        for br in brid:
                            if (((br['start_time'] - cx['start_time']) < 1) & ((br['start_time'] - cx['start_time']) >-1)):
                                bbrid = br
                        if bbrid:
                            wfd = defer.waitForDeferred(
            	                    self.master.db.buildrequests.ggetBuildRequest(bbrid['brid']))
                            yield wfd
                            brd = wfd.getResult()
                            if brd['priority'] < 2:
                                xx['time'] = brd['submitted_at']
                                xx['build'] = cx
                                ccxt['nourgent'].append(xx)
                        if len(ccxt['nourgent']):
                            ccxt['nourgent'].sort()
                            nourgent = ccxt['nourgent']
                            stopnourgent = nourgent[-1]
                            stopbuild = stopnourgent['build']

                #stopbuild_status = self.status.getBuilder(bname)
                #stop the spicified build(stopbuild)
                    if stopbuild:
                        c = interfaces.IControl(self.getBuildmaster(req))
                        bldrc = c.getBuilder(stopbuild['buildername'])
                        if bldrc:
                            bldc = bldrc.getBuild(stopbuild['num'])
                            if bldc:
                                bldc.stopBuild("stopped by urgent build, it will be submit again!")           
                                stopbuildername = stopbuild['buildername']
                                builder_s = self.status.getBuilder(stopbuildername)
                                build_s = builder_s.getBuild(stopbuild['num'])
                                properties = Properties()
                            # Don't include runtime-set properties in a rebuild request
                                properties.updateFromPropertiesNoRuntime(build_s.getProperties())
                                properties_dict = dict((k,(v,s)) for (k,v,s) in properties.asList())
                                ss = build_s.getSourceStamp(absolute=True)
                                d = ss.getSourceStampId(master)
                                def add_buildset(ssid):
                                    return master.addBuildset(
                                                builderNames=[stopbuildername],
                                                ssid=ssid, reason=build_s.getReason()+"stoped by urgent", properties=properties_dict, priority=1)
                                d.addCallback(add_buildset)

#                yield(path_to_query(req))
            else:
               # req.addCookie('samebranch', branch, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+0.5*3600)))    
                samebranch.append(branch);
                #yield(path_to_trigger(req))
        #samebranch = []
        if (len(samebranch)):
            req.addCookie('samebranch', samebranch, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+0.5*3600)))    
        yield (path_to_query(req))



