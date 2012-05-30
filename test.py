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


from buildbot.schedulers.timed import Nightly
from twisted.web import html
from twisted.web.util import Redirect
import urllib, time
from twisted.python import log
from twisted.internet import defer
from buildbot import interfaces
from buildbot.status.web.base import HtmlResource, BuildLineMixin, \
    path_to_build, path_to_slave, path_to_builder, path_to_change, \
    path_to_root, path_to_trigger, path_to_query, getAndCheckProperties, ICurrentBox, build_get_class, \
    map_branches, path_to_authfail, ActionResource

from buildbot.status.web.build import BuildsResource, StatusResourceBuild
from buildbot import util


class Test(HtmlResource, BuildLineMixin):
    def builder(self, build, req):
        b = {}
       	#add by zlinghu begin:20111118
       	b["buildername"]
        b['reason'] = build.getReason()
		#add by zlinghu end
        b['num'] = build.getNumber()
        b['link'] = path_to_build(req, build)
        b['branch'] = build.source.branch
       # log.msg("builderbranch=%s" % build.source.branch)

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

        return b

    @defer.deferredGenerator
    def content(self, req, cxt):
        log.msg("testrequest",req)
        #branch = req.args.get("branch",[])[0]
        buildername = req.args.get("buildername",[])[0]
        self.status = self.getStatus(req)
        #username = req.args.get("username", "Dev build")
        #buildername = req.args.get("selected", [""])
        #log.msg("testbranch", branch)
        self.builder_status = self.status.getBuilder(buildername)
        b = self.builder_status
        bbranch = cxt['bbranch'] = []
        log.msg("bbranchs1=%s" % cxt['bbranch'])
        cxt['name'] = b.getName()
        self.name = b.getName()
        req.setHeader('Cache-Control', 'no-cache')
        slaves = b.getSlaves()
        connected_slaves = [s for s in slaves if s.isConnected()]

        cxt['current'] = [self.builder(x, req) for x in b.getCurrentBuilds()]
        for cu in cxt['current']:
        	log.msg("cu.branch=%s" % (cu['branch']))
        	if not cu['branch'] in bbranch:
        		bbranch.append(cu['branch'])
        log.msg("bbranchs2=%s" % cxt['bbranch'])

        cxt['pending'] = []
        wfd = defer.waitForDeferred(
            b.getPendingBuildRequestStatuses())
        yield wfd
        log.msg("test1")
        statuses = wfd.getResult()
        for pb in statuses:
            changes = []

            wfd = defer.waitForDeferred(
                    pb.getSourceStamp())
            yield wfd
            source = wfd.getResult()

            wfd = defer.waitForDeferred(
                    pb.getSubmitTime())
            yield wfd
            submitTime = wfd.getResult()

            if source.changes:
                for c in source.changes:
                    changes.append({ 'url' : path_to_change(req, c),
                                     'who' : c.who,
                                     'revision' : c.revision,
                                     'repo' : c.repository })

            cxt['pending'].append({
                'when': time.strftime("%b %d %H:%M:%S",
                                      time.localtime(submitTime)),
                'name': b.getName(),
                'delay': util.formatInterval(util.now() - submitTime),
                'id': pb.brid,
                #add by zinghu begin:20111109
				#'buildername': "zlinghu",
                #add by zlinghu end
                'changes' : changes,
                'num_changes' : len(changes),
                'branch': source.branch,
                })
            if not source.branch in bbranch:
            	bbranch.append(source.branch)
        numbuilds = int(req.args.get('numbuilds', ['5'])[0])
        recent = cxt['recent'] = []
        for build in b.generateFinishedBuilds(num_builds=int(numbuilds)):
            recent.append(self.get_line_values(req, build, False))

        sl = cxt['slaves'] = []
        connected_slaves = 0
        for slave in slaves:
            s = {}
            sl.append(s)
            s['link'] = path_to_slave(req, slave)
            s['name'] = slave.getName()
            c = s['connected'] = slave.isConnected()
            if c:
                s['admin'] = unicode(slave.getAdmin() or '', 'utf-8')
                connected_slaves += 1
        cxt['connected_slaves'] = connected_slaves

        cxt['authz'] = self.getAuthz(req)
        cxt['builder_url'] = path_to_builder(req, b)
        #self.ccxt = cxt.copy()
       	log.msg("testbranch %s" % cxt['bbranch'])
       	

        template = req.site.buildbot_service.templates.get_template("builder.html")
        yield template.render(**cxt)
        #yield Redirect(path_to_root(req)+ "query")
		
        #template = request.site.buildbot_service.templates.get_template("about.html")
        #template.autoescape = True
        #return template.render(**cxt)
