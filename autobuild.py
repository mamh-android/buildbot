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
# Copyright marvell PIE team


from buildbot.status.web.base import HtmlResource, path_to_root, map_branches, BuildLineMixin,getAndCheckProperties
from buildbot.status.web.builder import StatusResourceBuilder, StatusResourceAllBuilders, StatusResourceSelectedBuilders,path_to_builder,ForceBuildActionResource
import buildbot
import twisted
from twisted.web import html
from twisted.web.util import Redirect
from twisted.python import log
from buildbot import util
from twisted.internet import defer
import sys
import urllib,time
import jinja2

class Autobuild(HtmlResource, BuildLineMixin):
    pageTitle = "About this Buildbot"

    def content(self, request, cxt):
        status = self.getStatus(request)
        branches = [b for b in request.args.get("branch", []) if b]
        numbuilds = int(request.args.get("numbuilds", [50])[0])
        builders = request.args.get("builder", status.getBuilderNames())
        g = status.generateFinishedBuilds(builders, map_branches(branches),
                                          numbuilds, max_search=numbuilds)
        bs = cxt['builders'] = []
        cxt['current'] = []
        cxt['pending'] = []
        builds = cxt['builds'] = []
        base_builders_url = path_to_root(request) + "builders/"
        for bn in builders:
            bld = { 'link': base_builders_url + urllib.quote(bn, safe=''),
                  'name': bn }
            bs.append(bld)
        for build in g:
            builds.append(self.get_line_values(request, build))
        cxt['num_builds'] = numbuilds
        cxt['status'] = status
        cxt['authz'] = self.getAuthz(request)
        for buildname in builders:
            build_status = self.getStatus(request).getBuilder(buildname)
            a = StatusResourceBuilder(build_status)
            b = build_status
            for x in b.getCurrentBuilds():
                cxt['current'].append(a.builder(x,request))
        template = request.site.buildbot_service.templates.get_template("daily_build.html")
        template.autoescape = True
        return template.render(**cxt)
    def getChild(self, path, req):
        s = self.getStatus(req)
        if path in s.getBuilderNames():
            builder_status = s.getBuilder(path)
            return StatusResourceBuilder(builder_status)
        if path == "_all":
            return StatusResourceAllBuilders(self.getStatus(req))
        if path == "_selected":
            return StatusResourceSelectedBuilders(self.getStatus(req))
        if path == "query":
            return StatusQuery()

        return HtmlResource.getChild(self, path, req)

class StatusQuery(HtmlResource, BuildLineMixin):
    @defer.deferredGenerator
    def content(self,request,cxt):
        status = self.getStatus(request)
        branches = [b for b in request.args.get("branch", []) if b]
        numbuilds = int(request.args.get("numbuilds", [50])[0])
        builders = request.args.get("builder", status.getBuilderNames())
        bs = cxt['builders'] = []
        cxt['current'] = []
        cxt['pending'] = []
        recent = cxt['recent'] = []
        builds = cxt['builds'] = []
        finished_before = int(request.args.get("finished_before", [util.now()])[0])
        #finished_after = int(request.args.get("finished_after",[util.now()])[0])
        got = 0
        last_time = None
        g = status.generateFinishedBuilds(builders, map_branches(branches),
                numbuilds, max_search=200,finished_before=finished_before)
        for build in g:
            if got ==0:
                first_time = build.getTimes()[1]
                log.msg("first_time is ",time.strftime(self.LINE_TIME_FORMAT,time.localtime(first_time)))
            got+=1
            if got == numbuilds:
                last_time = build.getTimes()[1]
                log.msg("last_time is ",time.strftime(self.LINE_TIME_FORMAT,time.localtime(last_time)))
            recent.append(self.get_line_values(request, build))
        if last_time:
            cxt['nextpage'] = path_to_root(request)+"autobuild?finished_before=" + str(int(last_time))
        #cxt['previouspage'] = path_to_root(request)+"autobuild?finished_before=" + str(int(first_time))
        base_builders_url = path_to_root(request) + "builders/"
        for bn in builders:
            bld = { 'link': base_builders_url + urllib.quote(bn, safe=''),
                  'name': bn }
            bs.append(bld)
        for build in g:
            builds.append(self.get_line_values(request, build))
        cxt['num_builds'] = numbuilds
        cxt['status'] = status
        cxt['authz'] = self.getAuthz(request)
        for buildname in builders:
            build_status = self.getStatus(request).getBuilder(buildname)
            a = StatusResourceBuilder(build_status)
            b = build_status
            cxt['builder_url'] = path_to_builder(request, b)
            for x in b.getCurrentBuilds():
                cxt['current'].append(a.builder(x,request))
                #cxt['current'].append({'name' :buildname})
            wfd = defer.waitForDeferred(b.getPendingBuildRequestStatuses())
            yield wfd
            statuses = wfd.getResult()
            for pb in statuses:
                changes = []

                wfd = defer.waitForDeferred(pb.getSourceStamp())
                yield wfd
                source = wfd.getResult()

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
                    'when': time.strftime("%b %d %H:%M:%S",
                                          time.localtime(submitTime)),
                    'delay': util.formatInterval(util.now() - submitTime),
                    'id': pb.brid,
                    'changes' : changes,
                    'num_changes' : len(changes),
                    'name' : buildname,
                    'branch' : source.branch
                    })
        template = request.site.buildbot_service.templates.get_template("daily_build.html")
        template.autoescape = True
        yield template.render(**cxt)
    def getChild(self, path, req):
        s = self.getStatus(req)
        if path in s.getBuilderNames():
            builder_status = s.getBuilder(path)
            return StatusResourceBuilder(builder_status)
        if path == "_all":
            return StatusResourceAllBuilders(self.getStatus(req))
        if path == "_selected":
            return StatusResourceSelectedBuilders(self.getStatus(req))
        if path == "query":
            branches = [b for b in req.args.get("branch", []) if b]
            return Redirect(path_to_root(req)+"autobuild?branch="+branches[0])
            #return StatusQuery()
        if path == "force":
            return self.force(req, True)

        return HtmlResource.getChild(self, path, req)

    def query(self, request):
        branches = [b for b in request.args.get("branch", []) if b]
        return Redirect(path_to_root(request)+"autobuild?branch="+branches[0])
    def force(self, req, auth_ok=False):
        buildname_1 =  req.args.get("selected", [""])[0]
        builder_status = self.getStatus(req).getBuilder(buildname_1)
        name = req.args.get("username", ["<unknown>"])[0]
        reason = req.args.get("comments", ["<no reason specified>"])[0]
        branch = req.args.get("branch", [""])[0]
        revision = req.args.get("revision", [""])[0]
        repository = req.args.get("repository", [""])[0]
        project = req.args.get("project", [""])[0]
        urgent = req.args.get("urgent",[""])[0]
        priority = 0
        if urgent:
            priority = 2

        if not auth_ok:
            req_args = dict(name=name, reason=reason, branch=branch,
                            revision=revision, repository=repository,
                            project=project)
            return ForceBuildActionResource(builder_status, req_args)

        master = self.getBuildmaster(req)
       

        # keep weird stuff out of the branch revision, and property strings.
        branch_validate = master.config.validation['branch']
        revision_validate = master.config.validation['revision']
        if not branch_validate.match(branch):
            log.msg("bad branch '%s'" % branch)
            return Redirect(path_to_builder(req, builder_status))
        if not revision_validate.match(revision):
            log.msg("bad revision '%s'" % revision)
            return Redirect(path_to_builder(req, builder_status))
        properties = getAndCheckProperties(req)
        if properties is None:
            return Redirect(path_to_builder(req, builder_status))
        if not branch:
            branch = None
        if not revision:
            revision = None

        d = master.db.sourcestamps.addSourceStamp(branch=branch,
                revision=revision, project=project, repository=repository)
        def make_buildset(ssid):
            r = ("The web-page 'force build' button was pressed by '%s': %s\n"
                 % (html.escape(name), html.escape(reason)))
            return master.addBuildset(
                    builderNames=[buildname_1],
                    ssid=ssid, reason=r, priority = priority, properties=properties.asDict())
        d.addCallback(make_buildset)
        d.addErrback(log.err, "(ignored) while trying to force build")
        # send the user back to the builder page
        #return Redirect(path_to_builder(req, builder_status))
        return Redirect(path_to_root(req)+"autobuild")
        



        
