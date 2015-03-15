# -*- coding: utf-8 -*-

import gntp.notifier

from time import time
from module.plugins.Hook import Hook

class NotifyGrowl(Hook):
    __name__    = "NotifyGrowl"
    __type__    = "hook"
    __version__ = "0.02"

    __config__ = [("hostname"       , "str" , "Hostname", "localhost"),
                  ("password"       , "str" , "Password", ""),
                  ("notifycaptcha"  , "bool", "Notify captcha request", True),
                  ("notifypackage"  , "bool", "Notify package finished", True),
                  ("notifyprocessed", "bool", "Notify processed packages status", True),
                  ("timeout"        , "int" , "Timeout between captchas in seconds" , 5),
                  ("force"          , "bool", "Send notifications even if client is connected", True)]

    __description__ = """Send notifications to Growl"""
    __license__     = "GPLv3"
    __authors__     = [("Jochen Oberreiter", "NETHead (AT) gmx.net")]
    
    event_list = ["allDownloadsProcessed"]

    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        self.info  = {}  #@TODO: Remove in 0.4.10
        self.growl = self.register()
        self.last_notify = 0


    def newCaptchaTask(self, task):
        if not self.getConfig("notifycaptcha"):
            return False
        
        if (time() - self.last_notify) < self.getConf("timeout"):
            return False

        self.notify("Captcha waiting", _("Captcha"), _("New request waiting user input"), 1)


    def packageFinished(self, pypack):
        if self.getConfig("notifypackage"):
            self.notify("Package finished", _("Package finished"), pypack.name)


    def allDownloadsProcessed(self):
        if not self.getConfig("notifyprocessed"):
            return False

        if any(True for pdata in self.core.api.getQueue() if pdata.linksdone < pdata.linkstotal):
            self.notify("Downloads finished", _("Package failed"), _("One or more packages was not completed successfully"))
        else:
            self.notify("Downloads finished", _("All packages finished"))


    def register(self):
        growl = gntp.notifier.GrowlNotifier(applicationName = "Pyload",
                                            notifications = ["Captcha waiting", "Package finished", "Downloads finished"],
                                            defaultNotifications = ["Captcha waiting", "Package finished", "Downloads finished"],
                                            hostname = self.getConfig("hostname"), # Defaults to localhost
                                            password = self.getConfig("password")  # Defaults to a blank password
                                            )
        if growl:
            growl.register()
            return growl
        else:
            self.logError("NotifyGrowl: Could not register pyload at host '%s'" % self.getConfig("hostname"), e)
            return None


    def notify(self, type, event, msg="", prio=-1):
        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        try:
            image = open('/usr/share/pyload/icons/logo.png', 'rb').read()
        except:
            image = None
            self.logInfo("NotifyGrowl: Pyload logo not found, skipping it")
            
        self.growl.notify(noteType = type,
                        title = event,
                        description = msg,
                        icon = image,
                        sticky = False,
                        priority = prio)
        
        self.last_notify = time()
