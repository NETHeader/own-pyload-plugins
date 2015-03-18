# -*- coding: utf-8 -*-

import gntp.notifier    # Growl Network Transport Protocol Implementation
import socket           # for IP address determination
import os               # for loading of the pyLoad logo 

from time import time
from module.plugins.Hook import Hook

class NotifyGNTP(Hook):
    __name__    = "NotifyGNTP"
    __type__    = "hook"
    __version__ = "0.01"
    __description__ = """Send notifications to Growl & Snarl (GNTP)"""
    __license__     = "GPLv3"
    __authors__     = [("NETHeader", "NETHead (AT) gmx.net")]

    __config__ = [("hostname"      , "str" , "Hostname", "127.0.0.1"),
                  ("password"       , "str" , "Password", ""),
                  ("port"           , "int" , "Port", 23053),
                  ("notifycaptcha"  , "bool", "Notify captcha request", True),
                  ("notifypackage"  , "bool", "Notify package finished", True),
                  ("notifyprocessed", "bool", "Notify processed packages status", True),
                  ("timeout"        , "int" , "Timeout between captchas in seconds" , 5),
                  ("displaysticky"  , "bool", "Display notifications sticky", False),
                  ("displaypriority", "int" , "Display priority, range -2(very low) to 2(emergency)" , -1),
                  ("force"          , "bool", "Send notifications even if client is connected", True)]
    
    event_list = ["allDownloadsProcessed"]
    LOGO_PATH = "/usr/share/pyload/icons/logo.png"

    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        self.info  = {}  #@TODO: Remove in 0.4.10
        self.last_notify = 0

        # Register at remote host
        self.growl = self.register()
        if not self.growl:
            self.fail("Could not register at host '%s:%d'" % (self.getConfig("hostname"), self.getConfig("port")))
        else:
            self.logInfo("Registered at host '%s:%d'" % (self.getConfig("hostname"), self.getConfig("port")))

        # Determine callback URI 
        if self.config['webinterface']['activated']:
            self.webip = socket.gethostbyname(socket.gethostname())
            self.webport = self.config['webinterface']['port']
            self.logInfo("Callback URI is 'http://%s:%d'" % (self.webip, self.webport))
            
        self.logInfo("path = %s" % os.path.dirname(os.path.abspath(__file__)))
        self.logInfo("path = %s" % os.getcwd())
        
    def newCaptchaTask(self, task):
        if not self.getConfig("notifycaptcha"):
            return False
        
        # Check timeout
        if (time() - self.last_notify) < self.getConf("timeout"):
            return False
        
        if self.config['webinterface']['activated']:
            self.notify("Captcha waiting", _("Captcha"), _("New request waiting user input"), "http://%s:%d" % (self.webip, self.webport))
        else:
            self.notify("Captcha waiting", _("Captcha"), _("New request waiting user input"))


    def packageFinished(self, pypack):
        if self.getConfig("notifypackage"):
            self.notify("Package finished", _("Package finished"), pypack.name)


    def allDownloadsProcessed(self):
        if not self.getConfig("notifyprocessed"):
            return False
        
        # Check queue on package status 
        if any(True for pdata in self.core.api.getQueue() if pdata.linksdone < pdata.linkstotal):
            self.notify("Downloads finished", _("Package failed"), _("One or more packages was not completed successfully"))
        else:
            self.notify("Downloads finished", _("All packages finished"))


    def loadLogo(self, uri):
        self.logDebug("logo=%s" % uri)        
        if uri.startswith("http"):
            image = uri
        else:
            try:
                image = open(uri, 'rb').read()
            except:
                image = None
                self.logInfo("Application logo not found, skipping it")
        return image


    def register(self):
        growl = gntp.notifier.GrowlNotifier(applicationName = "pyLoad",
                                            notifications = ["Captcha waiting", "Package finished", "Downloads finished"],
                                            defaultNotifications = ["Captcha waiting", "Package finished", "Downloads finished"],
                                            applicationIcon = self.loadLogo(self.LOGO_PATH),
                                            hostname = self.getConfig("hostname"),
                                            password = self.getConfig("password"),
                                            port = self.getConfig("port"))
        if growl:
            growl.register()
        return growl


    def notify(self, type, event, msg = "", uri = None):
        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        # Check priority
        prio = self.getConfig("displaypriority")
        if not (-2 <= prio <= 2):
            prio = -1
            self.logWarning("Priority out of range, check plugin config")

        # Send notification  
        self.growl.notify(noteType = type,
                        title = event,
                        description = msg,
                        callback = uri,
                        icon = self.loadLogo(self.LOGO_PATH),
                        sticky = self.getConfig("displaysticky"),
                        priority = prio)
        
        self.last_notify = time()