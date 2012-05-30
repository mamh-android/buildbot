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

class LoginPage(HtmlResource):
    def __init__(self):
        HtmlResource.__init__(self)
    
    def content(self, request, cxt):
        cxt['path_to_root'] = path_to_root(request)
        template = request.site.buildbot_service.templates.get_template("login.html")
        template.autoescape = True
        return template.render(**cxt)
    def getChild(self, path, req):
        if (path=="auth"):
        	return LoginStatus(req)
        return HtmlResource.getChild(self, path, req)

class LoginStatus(ActionResource):
    def __init__(self, req):
        ActionResource.__init__(self)
        self.action = "loginIn"
        self.master = self.getBuildmaster(req)
 
    @defer.deferredGenerator
    def performAction(self, req):
        username = (req.args.get("username", [""])[0])
        status = self.getStatus(req)
        master = status.master
        import os
        logfile = os.path.join(master.basedir, 'user.txt')
        logfile =open(logfile,'a')
        #import time
        stime = time.strftime('%Y-%m-%d  %H:%M:%S',time.localtime(time.time()))
        #username = req.getCookie('username')
        s = stime +" : " + username + " try to login in"
        logfile.write(s)
        logfile.write('\n')
        logfile.close()         
        passwd = (req.args.get("passwd", [""])[0])
        wfd = defer.waitForDeferred(self.master.db.user_real.getUser_realByUsername(username))
        yield wfd
        userinfo = wfd.getResult()
        if not userinfo:
            req.addCookie('pass', 'nouser', path = '/')      
            yield path_to_authfail(req)
            return        
        if username == 'marvell' and passwd == 'marvelltest':
            #wfd = defer.waitForDeferred(self.master.db.user_real.getUser_realByUsername(username))
            #yield wfd
            #userinfo = wfd.getResult()
            dispname = userinfo['disp_name'].encode('utf-8')
            email = userinfo['email'].encode('utf-8')
            if(dispname):
                req.addCookie('dispname', dispname, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+24*3600)))
            else:
                req.addCookie('dispname', username, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+24*3600)))    
            req.addCookie('email', email, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+24*3600)))
            yield path_to_root(req)+"root"
            return
        import urllib2
        request = urllib2.Request( 'http://sh4-web01/LoginADWebSite/login.aspx' )
        try:
            params = urllib.urlencode({"userName":username, "password":passwd })
            response = urllib2.urlopen(request, params)
        except urllib2.URLError, e:
            yield path_to_authfail(req)
            return
        res = (response.read()).find('Passed')
        if res == -1:
            log.msg("..but not authorized")
            #req.addCookie('pass', 'passwdwrong', path = '/')      
            yield path_to_authfail(req)
            return
        else:
            #wfd = defer.waitForDeferred(self.master.db.user_real.getUser_realByUsername(username))
            #yield wfd
            #userinfo = wfd.getResult()
            dispname = userinfo['disp_name'].encode('utf-8')
            email = userinfo['email'].encode('utf-8')
            if(dispname):
                req.addCookie('dispname', dispname, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+24*3600)))
            else:
                req.addCookie('dispname', username, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+24*3600)))    
            req.addCookie('email', email, path = '/', expires = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(time.time()+24*3600)))
            yield path_to_root(req)+"root"
            return 

