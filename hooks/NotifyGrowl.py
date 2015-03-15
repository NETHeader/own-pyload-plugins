# -*- coding: utf-8 -*-

import gntp.notifier

from time import time
from module.plugins.Hook import Hook

class NotifyGrowl(Hook):
    __name__    = "NotifyGrowl"
    __type__    = "hook"
    __version__ = "0.01"

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

        self.notify("Captcha", _("Captcha"), _("New request waiting user input"), 1)


    def packageFinished(self, pypack):
        if self.getConfig("notifypackage"):
            self.notify("Package", _("Package finished"), pypack.name)


    def allDownloadsProcessed(self):
        if not self.getConfig("notifyprocessed"):
            return False

        if any(True for pdata in self.core.api.getQueue() if pdata.linksdone < pdata.linkstotal):
            self.notify("Package", _("Package failed"), _("One or more packages was not completed successfully"))
        else:
            self.notify("Package", _("All packages finished"))


    def register(self):
        growl = gntp.notifier.GrowlNotifier(applicationName = "Pyload",
                                            notifications = ["Captcha", "Package"],
                                            defaultNotifications = ["Captcha"],
                                            hostname = self.getConfig("hostname"), # Defaults to localhost
                                            password = self.getConfig("password") # Defaults to a blank password
                                            )
        growl.register()
        return growl


    def notify(self, type, event, msg="", prio=-1):
        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        self.growl.notify(noteType = type,
                        title = event,
                        description = msg,
                        #icon = "http://example.com/icon.png",
                        sticky = False,
                        priority = prio)

        self.last_notify = time()
