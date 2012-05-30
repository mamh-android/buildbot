from twisted.web import html
from twisted.web.util import Redirect
import urllib, time, csv
from twisted.python import log
from twisted.internet import defer
from buildbot import interfaces
from buildbot.status.web.base import HtmlResource, BuildLineMixin, \
    path_to_build, path_to_slave, path_to_builder, path_to_change, \
    path_to_root, getAndCheckProperties, ICurrentBox, build_get_class, \
    map_branches, path_to_authfail, path_to_query, ActionResource, DownLoadResource

from buildbot.status.web.build import BuildsResource, StatusResourceBuild
from buildbot import util


class BranchStatus(HtmlResource):
    def __init__(self):
        HtmlResource.__init__(self)

    def content(self, req, cxt):
        status = self.getStatus(req)
        master = status.master
        self.schedulers = status.getSchedulers()
        branches = []
        for i in self.schedulers:
            branches.append(i.branch)
        cxt['branch_names'] = branches
        template = req.site.buildbot_service.templates.get_template("branchquery.html")
        return template.render(**cxt)       

    def getChild(self, path, req):
        if (path == "submitreason"):
            return setReason(path)
        elif (path == "export"):
            return exportData(req)
        else:
            return branchQuery(path)

class exportData(DownLoadResource, BuildLineMixin):
    def __init__(self, req):
        DownLoadResource.__init__(self)
        self.branchname = req.args.get("branchname", [""])[0]
        self.req = req;
    def getData(self): 
        buildernames = self.getStatus(self.req).getBuilderNames()
        numbuilds = 20000
        recent = []
        out = ""
        for builderName in buildernames:
            b = self.getStatus(self.req).getBuilder(builderName)
            for build in b.generateFinishedBuilds(num_builds=int(numbuilds)):
                if build.source.branch == self.branchname:
                    recent.append(self.get_line_values(self.req, build, False))
        out = out + "Time" + "," + "BranchName" + "," + "Result" + ','+ "Reason" + ',' + "builder" + ',' + "Build" + ',' + "Info" + ',' + "Android Build Info" + ',' + "Failure Reason" + ',' + "Owner" + ',' + "Submit Time"
        for build in recent:
            out = out + '\n' + build['time'] + ',' + build['branch'] + ',' + build['results'] + ',' + build['reason'].replace(',', '.').replace('\n', '').strip('\n') + ',' + build['builder_name'] + ',' + str(build['buildnum']) + ',' + build['text']
            if build['text1'].find('http') >= 0:
                out = out + ',' + build['text2']
            else:
                out = out + ',' + build['text1']
            if build['reason1'] != "":
                out = out  + ',' + ''.join((build['reason1'].replace(',', '.').replace('\n', '')).split()) + ',' + build['editperson'] + ',' + build['edittime']
        return out

class branchQuery(HtmlResource, BuildLineMixin):
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
    	self.master = self.getBuildmaster(req)
    	master = status.master
    	self.schedulers = status.getSchedulers()
    	branches = []
    	for i in self.schedulers:
    	    branches.append(i.branch)
    	cxt['branch_names'] = branches
    	#req.setHeader('Cache-Control', 'no-cache')
    	cxt['branchname'] = self.branchname
    	cxt['pending'] = []
    	cxt['current'] = []
    	recent = cxt['recent'] = []
    	sl = cxt['slaves'] = []
    	numbuilds = int(req.args.get('numbuilds', ['20000'])[0])
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
                #add by zlinghu begin:
                wfd = defer.waitForDeferred(self.master.db.buildsets.getBuildset(pb.bsid))
                yield wfd
                bs = wfd.getResult()
                #add by zlinghu end
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
                        'reason':bs['reason'],
                        'delay':util.formatInterval(util.now() - submitTime),
                        'id':pb.brid,
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
            


class setReason(ActionResource):
    def __init__(self, path):
        ActionResource.__init__(self)
        log.msg("init in setReason!");

    @defer.deferredGenerator
    def performAction(self, req):
        buildername = req.args.get("buildername", [""])[0]
        buildid = req.args.get("buildid", [""])[0]
        branch = req.args.get("branch", [""])[0]
        failurereason = req.args.get("failurereason", [""])[0]
        person = req.getCookie("dispname")
        b = self.getStatus(req).getBuilder(buildername)
        build = b.getBuild(int(buildid))
        build.setFailureReason(failurereason)
        build.setEditTime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        build.setEditPerson(person)
        build.saveYourself();
        yield "../branchquery/"+ branch
