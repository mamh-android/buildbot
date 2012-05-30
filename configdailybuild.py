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


from buildbot.status.web.base import HtmlResource, ActionResource, path_to_root, map_branches, BuildLineMixin,getAndCheckProperties
from buildbot.status.web.builder import StatusResourceBuilder, StatusResourceAllBuilders, StatusResourceSelectedBuilders,path_to_builder,ForceBuildActionResource
import buildbot
from buildbot.master import BuildMaster
from buildbot.schedulers import timed
import twisted
from twisted.web import html
from twisted.web.util import Redirect
from twisted.python import log
from buildbot import util
from twisted.internet import defer
import sys,os,re
import urllib,time
import jinja2
import json


class ConfigAutobuild(HtmlResource, BuildLineMixin):
    pageTitle = "Configure Autobuild"
      
    def content(self, request, cxt):
        #time.sleep(5)
        status = self.getStatus(request)
        master = status.master
        self.scher = status.getSchedulers()
        cxt['schedulers'] = []
        for elemen in self.scher:
            cxt['schedulers'].append(elemen)
        status = self.getStatus(request)
        branch = request.args.get("update_branch",[""])[0]
        log.msg("request branch is", branch)
        if branch:
            cxt['branch'] = branch
        cxt['url_update'] = path_to_root(request)+"configbuild/update"
        cxt['url_delete'] = path_to_root(request)+"configbuild/remove"
        numbuilds = int(request.args.get("numbuilds", [50])[0])
        builders = request.args.get("builder", status.getBuilderNames())
        bs = cxt['builders'] = []
        builds = cxt['builds'] = []
        base_builders_url = path_to_root(request) + "builders/"
        for bn in builders:
            bld = { 'link': base_builders_url + urllib.quote(bn, safe=''),
                  'name': bn }
            bs.append(bld)
        sc = {}
        branch_names=[]
        json_scherdulers = []
        for s in self.scher:
            sc = ({'name':s.builderNames[0],            
                   'hour':s.hour,
                   'branch':s.branch,
                   'Graphic_Build':s.properties['Graphic_Build'],
                   'Test_Case_Build':s.properties['Test_Case_Build'],
                   'purpose':s.properties['purpose'],
                   'user_info':s.properties['useremail']})
            json_scherdulers.append(sc)
            branch_names.append(s.branch)
        cxt['branch_names'] = branch_names
        cxt['json_schedulers'] = json.dumps(json_scherdulers)
        #log.msg("json_schedulers=", cxt['json_schedulers']);
        cxt['dict_schedulers'] = json_scherdulers
        template = request.site.buildbot_service.templates.get_template("config_dailybuild.html")
        template.autoescape = True
        return template.render(**cxt)
    def test(self):
        log.msg("before sleep")
        time.sleep(5)
        log.msg("after sleep")
    def getChild(self, path, req):
        if path == "add":
            #self.test()
            #log.msg("after test")
            return addConfigure()
        if path == "remove":
            return removeConfigure()            
        return HtmlResource.getChild(self, path, req)

class addConfigure(ActionResource, BuildLineMixin):
    def __init__(self):
        ActionResource.__init__(self)

    @defer.deferredGenerator
    def performAction(self, request):
        hour = int(request.args.get("hour",[25])[0])
        status = self.getStatus(request)
        master = status.master
        configFile = os.path.join(master.basedir, master.configFileName)
        self.scher = status.getSchedulers()
        added = 'True'
        addorupdate="True"
        useremail = request.args.get("email", [None])[0]
        get_branch = request.args.get("get_branch",[None])[0]
        buildname = request.args.get("radiobutton", [None])[0]
        optional = request.args.get("checkbox", [])
        purpose = request.args.get("config_purpose", ["unknown"])[0]
        log.msg("optional is ",optional)
        properties = {}
        properties['purpose'] = str(purpose)
        properties['useremail'] = useremail
        if optional.count('Graphic_Build') == 1:
            properties['Graphic_Build'] = "True"
        else:
            properties['Graphic_Build'] = "False"
        if optional.count('Test_Case_Build') == 1:
            properties['Test_Case_Build'] = "True"
        else:
            properties['Test_Case_Build'] = "False"
        f = open(configFile , 'r')
        lines = f.readlines()
        os.remove(configFile)
        t = open(configFile, "a")
        #add new manifest branch
        if get_branch == "branch":
            branch = request.args.get("manifest_branch",[None])[0]
            if not branch:
                added = 'False'
            if buildname == "Develop":
                build_scheduler = timed.Nightly(name=branch , branch=branch, builderNames=['android_develop_build'], hour=hour, minute=00 ,properties=properties)
            else:
                build_scheduler = timed.Nightly(name=branch , branch=branch, builderNames=['android_release_build'], hour=hour, minute=00, properties=properties)        
            for e in self.scher:
                if e.name == build_scheduler.name:
                    added = 'False'
                    break
        # update manifest branch
        else:
            addorupdate="False"
            branch = get_branch
            if buildname == "Develop":
                build_scheduler = timed.Nightly(name=branch , branch=branch, builderNames=['android_develop_build'], hour=hour, minute=00, properties=properties)
            else:
                build_scheduler = timed.Nightly(name=branch , branch=branch, builderNames=['android_release_build'], hour=hour, minute=00, properties=properties)    
            for e in self.scher:
                if e.name == build_scheduler.name:
                    removed = e
                    self.scher.remove(e)
                    break
        if added == 'False':
            for l in lines:
                t.writelines(l)
        #write in master.cfg
        else:
            property=''
            if properties:
                p = ''
                for key in properties.keys():
                    p += '\"' +key + '\":' + '\"' + properties[key] + '\",'
                
                property = "properties ={" + p + "}"
                log.msg("property is", property)
            ho = str(hour)
            if buildname == "Develop":
                s = branch + '= timed.Nightly(name=\"' + branch + '\"' + ', branch=\"' + branch + '\"' + ', builderNames=["android_develop_build"], hour=' + ho + ', minute=00,' + property +')\n'
            else:
                s = branch + '= timed.Nightly(name=\"' + branch + '\"' + ', branch=\"' + branch + '\"' + ', builderNames=["android_release_build"], hour=' + ho + ', minute=00,' + property +')\n'
            string_1 = 'c["schedulers"].append(' + branch + ')\n'
            if addorupdate=="True":
                for l in lines:
                    t.writelines(l)
                t.writelines(s)
                t.writelines(string_1)
            else:
                for l in lines:
                    querytext1 = branch + '\"'
                    querytext2 = branch + '\)'
                    if(len(re.findall(querytext1, l))>=1):
                        t.writelines(s)
                    elif(len(re.findall(querytext2, l))>=1):
                        t.writelines(string_1)
                    else:
                        t.writelines(l)
            t.close()
            self.scher.append(build_scheduler)
        master.loadConfig_Schedulers(self.scher)
        time.sleep(0.2)
        yield path_to_root(request)+"configbuild"

class removeConfigure(ActionResource, BuildLineMixin):
    def __init__(self):
        ActionResource.__init__(self)

    @defer.deferredGenerator
    def performAction(self, request):
        branch = request.args.get("configurebranch",[None])[0]
        status = self.getStatus(request)
        master = status.master
        logfile = os.path.join(master.basedir, 'removelog.txt')
        logfile =open(logfile,'a')
        import time
        time = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))
        username = request.getCookie('username')
        s =time +" : " + username + ' delete branch ' + branch
        logfile.write(s)
        logfile.write('\n')
        logfile.close() 
        configFile = os.path.join(master.basedir, master.configFileName) 
        f = open(configFile , 'r')
        lines = f.readlines()
        os.remove(configFile)
        t = open(configFile, 'a')
        removed = None
        self.schedulers = status.getSchedulers()
        for s in self.schedulers:
            if s.branch == branch:
                removed = s
                break
        if removed:
            self.schedulers.remove(removed)
            master.loadConfig_Schedulers(self.schedulers)
            for line in lines:
                querytext1 = branch + '\"'
                querytext2 = branch + "\)"
                if(re.findall(querytext1,line)):
                    pass
                elif(re.findall(querytext2,line)):
                    pass
                else:
                    t.write(line)
            t.close()
        yield path_to_root(request)+"configbuild"
        
