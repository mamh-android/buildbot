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


from buildbot.status.web.base import HtmlResource
import buildbot
import twisted
import json
import sys
import jinja2
from twisted.web import html
from twisted.web.util import Redirect
import urllib, time
from twisted.python import log
from twisted.internet import defer
from buildbot import interfaces
from buildbot.status.web.base import HtmlResource, BuildLineMixin, \
    path_to_build, path_to_slave, path_to_builder, path_to_change, \
    path_to_root, getAndCheckProperties, ICurrentBox, build_get_class, \
    map_branches, path_to_authfail, path_to_query, ActionResource

from buildbot.status.web.build import BuildsResource, StatusResourceBuild
from buildbot import util

class QueryBuild(HtmlResource, BuildLineMixin):
    pageTitle = "Query Page"
    def builder(self, build, req):
        b = {}
        b['buildername'] = build.getBuilder().getName()
        b['reason'] = build.getReason()
        b['num'] = build.getNumber()
        b['link'] = path_to_build(req, build)
        b['branch'] = build.source.branch
        b['builder_url'] = ("../builders/" + build.getBuilder().getName())
        

        when = build.getStart()
        b['when_time'] = time.strftime("%b %d  %H:%M:%S",
                            time.localtime(when))
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

        return b

    @defer.deferredGenerator
    def content(self, req, cxt):
    	status = self.getStatus(req)
        self.master = self.getBuildmaster(req)
    	buildernames = self.getStatus(req).getBuilderNames()
    	req.setHeader('Cache-Control', 'no-cache')
    	cxt['name'] = na = []
    	cxt['pending'] = []
    	cxt['current'] = []
    	recent = cxt['recent'] = []
    	sl = cxt['slaves'] = []
    	numbuilds = int(req.args.get('numbuilds', ['50'])[0])

    	for builderName in buildernames:
    	    b = self.getStatus(req).getBuilder(builderName)
    	    na.append(b.getName())
    	    slaves = b.getSlaves()
    	    connected_slaves = [s for s in slaves if s.isConnected()]
    	    cxt['current'].extend([self.builder(x, req) for x in b.getCurrentBuilds()])
    	    #bs = status.getBuilder(builderName)
    	    wfd = defer.waitForDeferred(
    	        b.getPendingBuildRequestStatuses())
            yield wfd
            statuses = wfd.getResult()
            for pb in statuses:
                changes=[]
                wfd = defer.waitForDeferred(pb.getSourceStamp())
                yield wfd
                source = wfd.getResult()
                wfd = defer.waitForDeferred(self.master.db.buildsets.getBuildset(pb.bsid))
                yield wfd
                bs = wfd.getResult()
                wfd = defer.waitForDeferred(pb.getSubmitTime())
                yield wfd
                submitTime = wfd.getResult()
                
                if source.changes:
                    for c in source.changes:
                        changes.append({ 'url' : path_to_change(req, c),
                                         'who' : c.who,
                                         'revision' : c.revision,
                                         'repo' : c.repository })
                cxt['pending'].append({
                    'when':time.strftime("%b %d  %H:%M:%S",
                            time.localtime(submitTime)),
                    'name':b.getName(),
                    'delay':util.formatInterval(util.now() - submitTime),
                    'id':pb.brid,
                    'reason': bs['reason'],
                    'changes' : changes,
                    'num_changes' : len(changes),
                    'branch':source.branch,
                    'builder_url':  (path_to_root(req) + "query/" +
                            urllib.quote(b.getName(), safe='') + '/cancelbuild')
                })
        builders = req.args.get("builder", [])
        branches = [b for b in req.args.get("branch", []) if b]
        cxt['jsonrunning'] = json.dumps(cxt['current'])
        cxt['jsonpending'] = json.dumps(cxt['pending'])
        
        finished_before = int(req.args.get("finished_before", [util.now()])[0])
        finished_after = int(util.now())
        got = 0
        last_time = None
        g = status.generateFinishedBuilds(builders, map_branches(branches),
                                      numbuilds, max_search=2000,finished_before=finished_before)
        for build in g:
            recent.append(self.get_line_values(req, build, False))
            if got ==0:
                first_time = build.getTimes()[1] 
            got+=1
            if got ==numbuilds:
     	         last_time = build.getTimes()[1]
        if last_time:
            cxt['nextpage'] = path_to_root(req)+"query?finished_before=" + str(int(last_time))
        cxt['previous'] = path_to_root(req)+"query?finished_before=" + str(int(finished_after))
        cxt['connected_slaves'] = connected_slaves
        cxt['authz'] = self.getAuthz(req)
        sl1 = []
        for slave in sl:
            if slave not in sl1:
                sl1.append(slave)
        cxt['slaves'] = sl1	
        cxt['jsonfinished'] = json.dumps(cxt['recent'])
        template = req.site.buildbot_service.templates.get_template("query.html")
        yield template.render(**cxt)


    def getChild(self, path, req):
        s = self.getStatus(req)
        if path in s.getBuilderNames():
            builder_status = s.getBuilder(path)
            return StatusResourceBuilder(builder_status)
        return HtmlResource.getChild(path,req)


class StatusResourceBuilder(HtmlResource):
    def __init__(self, builder_status):
        HtmlResource.__init__(self)
        self.builder_status = builder_status
    def getChild(self, path, req):
        if path == "cancelbuild":
            return CancelBuild(self.builder_status)
        return HtmlResource.getChild(self, path, req)


class CancelBuild(ActionResource):

    def __init__(self, builder_status):
        ActionResource.__init__(self)
        self.builder_status = builder_status

    @defer.deferredGenerator
    def performAction(self, req):
        try:
            request_id = req.args.get("id", [None])[0]
            if request_id == "all":
                cancel_all = True
            else:
                cancel_all = False
                request_id = int(request_id)
        except:
            request_id = None

        authz = self.getAuthz(req)
        status = self.getStatus(req)
        master = status.master
        branch = req.args.get("branchname",[None])[0]
        import os
        logfile = os.path.join(master.basedir, 'cancelbuild.txt')
        logfile =open(logfile,'a')
        import time
        time = time.strftime('%Y-%m-%d  %H:%M:%S',time.localtime(time.time()))
        username = req.getCookie('username')
        s =time +" : " + username + ' cancel branch ' + branch
        logfile.write(s)
        logfile.write('\n')
        logfile.close() 
        if request_id:
            c = interfaces.IControl(self.getBuildmaster(req))
            builder_control = c.getBuilder(self.builder_status.getName())

            wfd = defer.waitForDeferred(
                    builder_control.getPendingBuildRequestControls())
            yield wfd
            brcontrols = wfd.getResult()

            for build_req in brcontrols:
                if cancel_all or (build_req.brid == request_id):
                    d = authz.actionAllowed('cancelPendingBuild',
                                            req, build_req)
                    wfd = defer.waitForDeferred(d)
                    yield wfd
                    res = wfd.getResult()
                    if res:
                        build_req.cancel()
                    else:
                        yield path_to_authfail(req)
                        return
                    if not cancel_all:
                        break

        yield path_to_query(req)



class BranchStatus(HtmlResource, BuildLineMixin):
    def __init__(self, path):
        HtmlResource.__init__(self)
        self.branchname = path

    def builder(self, build, req):
        b = {}
        b['buildername'] = build.getBuilder().getName()
        b['reason'] = build.getReason()
        b['num'] = build.getNumber()
        b['link'] = path_to_build(req, build)
        b['branch'] = build.source.branch

        when = build.getStart()
        b['when_time'] = time.strftime("%b %d  %H:%M:%S",
                            time.localtime(when))
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

        return b
        
    @defer.deferredGenerator
    def content(self, req, cxt):
        status = self.getStatus(req)
    	buildernames = self.getStatus(req).getBuilderNames()
    	req.setHeader('Cache-Control', 'no-cache')
    	cxt['branchname'] = self.branchname
    	cxt['pending'] = []
    	cxt['current'] = []
    	recent = cxt['recent'] = []
    	sl = cxt['slaves'] = []
    	numbuilds = int(req.args.get('numbuilds', ['200'])[0])
    	currentall = []

    	for builderName in buildernames:
    	    b = self.getStatus(req).getBuilder(builderName)
    	    slaves = b.getSlaves()
    	    connected_slaves = [s for s in slaves if s.isConnected()]
    	    currentall.extend([self.builder(x, req) for x in b.getCurrentBuilds()])
    	    wfd = defer.waitForDeferred(
    	        b.getPendingBuildRequestStatuses())
            yield wfd
            statuses = wfd.getResult()
            for pb in statuses:
                changes=[]
                wfd = defer.waitForDeferred(pb.getSourceStamp())
                yield wfd
                source = wfd.getResult()
                wfd = defer.waitForDeferred(self.master.db.buildsets.getBuildset(pb.bsid))
                yield wfd
                bs = wfd.getResult()
                wfd = defer.waitForDeferred(pb.getSubmitTime())
                yield wfd
                submitTime = wfd.getResult()
                
                if source.changes:
                    for c in source.changes:
                        changes.append({ 'url' : path_to_change(req, c),
                                         'who' : c.who,
                                         'revision' : c.revision,
                                         'repo' : c.repository })
                if source.branch == self.branchname:
                    cxt['pending'].append({
                        'when':time.strftime("%b %d  %H:%M:%S",
                                time.localtime(submitTime)),
                        'name':b.getName(),
                        'delay':util.formatInterval(util.now() - submitTime),
                        'id':pb.brid,
                        #'reason': bs['reason'],
                        'changes' : changes,
                        'num_changes' : len(changes),
                        'branch':source.branch,
                        'builder_url':  (path_to_root(req) + "query/" +
                                urllib.quote(b.getName(), safe='') + '/cancelbuild')
                    })
            for build in b.generateFinishedBuilds(num_builds=int(numbuilds)):
                if build.source.branch == self.branchname:
                    recent.append(self.get_line_values(req, build, False))
        for cu in currentall:
    	    if cu['branch'] == self.branchname:
    	        cxt['current'].append(cu)    
        cxt['connected_slaves'] = connected_slaves
       	cxt['authz'] = self.getAuthz(req)
       	sl1 = []
       	for slave in sl:
       		if slave not in sl1:
       			sl1.append(slave)
     	cxt['slaves'] = sl1	
        template = req.site.buildbot_service.templates.get_template("branchquery.html")
        yield template.render(**cxt)   



