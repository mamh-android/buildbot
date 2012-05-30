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

class DailyBuild(HtmlResource):
    pageTitle = "DailyBuild"

    def content(self, request, cxt):
        template = request.site.buildbot_service.templates.get_template("dailybuild.html")
        template.autoescape = True
        return template.render(**cxt)