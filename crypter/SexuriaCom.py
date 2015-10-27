# -*- coding: utf-8 -*-

import re
from module.plugins.internal.Crypter import Crypter

class SexuriaCom(Crypter):
    __name__    = "SexuriaCom"
    __type__    = "crypter"
    __version__ = "0.17"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?sexuria\.com/(v1/)?(Pornos_Kostenlos_.+?_(\d+)\.html|dl_links_\d+_\d+\.html|id=\d+\&part=\d+\&link=\d+)'
    __config__  = [("use_subfolder",        "bool", "Save package to subfolder"          , True),
                  ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Sexuria.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("NETHead", "NETHead.AT.gmx.DOT.net")]

    #: Constants
    PATTERN_SUPPORTED_MAIN     = r'http://(www\.)?sexuria\.com/(v1/)?Pornos_Kostenlos_.+?_(\d+)\.html'
    PATTERN_SUPPORTED_CRYPT    = r'http://(www\.)?sexuria\.com/(v1/)?dl_links_\d+_(?P<ID>\d+)\.html'
    PATTERN_SUPPORTED_REDIRECT = r'http://(www\.)?sexuria\.com/out\.php\?id=(?P<ID>\d+)\&part=\d+\&link=\d+'
    PATTERN_TITLE              = r'<title> - (?P<TITLE>.*) Sexuria - Kostenlose Pornos - Rapidshare XXX Porn</title>'
    PATTERN_PASSWORD           = r'<strong>Passwort: </strong></div></td>.*?bgcolor="#EFEFEF">(?P<PWD>.*?)</td>'
    PATTERN_DL_LINK_PAGE       = r'"(dl_links_\d+_\d+\.html)"'
    PATTERN_REDIRECT_LINKS     = r'value="(http://sexuria\.com/out\.php\?id=\d+\&part=\d+\&link=\d+)" readonly'
    LIST_PWDIGNORE             = [u"Kein Passwort", u"-", u"kein"]

    def decrypt(self, pyfile):
        #: Init
        self.pyfile = pyfile
        self.package = pyfile.package()

        #: Decrypt and add links
        package_name, self.links, folder_name, package_pwd = self.decrypt_links(self.pyfile.url)
        if package_pwd:
            self.pyfile.package().password = package_pwd
        self.packages = [(package_name, self.links, folder_name)]


    def decrypt_links(self, url):
        linklist = []
        name     = self.package.name
        folder   = self.package.folder
        password = None

        if re.match(self.PATTERN_SUPPORTED_MAIN, url, re.I):
            #: Processing main page, redirecting to download links
            self.log_debug(u"Processing main link")
            html = self.load(url)
            links = re.findall(self.PATTERN_DL_LINK_PAGE, html, re.I)
            for link in links:
                linklist.append("http://sexuria.com/v1/" + link)

        elif re.match(self.PATTERN_SUPPORTED_REDIRECT, url, re.I):
            #: Processing direct redirect link (out.php), redirecting to main page
            self.log_debug(u"Processing redirect link")
            id = re.search(self.PATTERN_SUPPORTED_REDIRECT, url, re.I).group('ID')
            if id:
                linklist.append("http://sexuria.com/v1/Pornos_Kostenlos_liebe_%s.html" % id)

        elif re.match(self.PATTERN_SUPPORTED_CRYPT, url, re.I):
            #: Processing crypted download link
            self.log_debug(u"Processing crypt link")
            id = re.search(self.PATTERN_SUPPORTED_CRYPT, url, re.I).group('ID')
            #: Download main page and extract package data
            html = self.load("http://sexuria.com/v1/Pornos_Kostenlos_info_%s.html" % id, decode=False)
            if not isinstance(html, unicode):
                html_encoding = re.search(r'content="text/html; charset=(?P<ENC>.+?)"', html, re.I)
                if html_encoding:
                    self.log_debug(u"Found HTML source encoding: %s" % html_encoding.group('ENC'))
                    html = html.decode(encoding=html_encoding.group('ENC'), errors='ignore')
            #: Webpage title / Package name
            titledata = re.search(self.PATTERN_TITLE, html, re.I)
            if not titledata:
                self.log_warning(_(u"No title data found, maybe plugin outdated?"))
            else:
                title = titledata.group('TITLE').strip()
                if title:
                    name = folder = title
                    self.log_debug(u"Package data found: name [%s] and folder [%s]" % (name, folder))
            #: Password
            pwddata = re.search(self.PATTERN_PASSWORD, html, re.I | re.S)
            if not pwddata:
                self.log_warning(_(u"No password data found, maybe plugin outdated?"))
            else:
                pwd = pwddata.group('PWD').strip()
                if pwd and not (pwd in self.LIST_PWDIGNORE):
                    password = pwd
                    self.log_debug(u"Package data found: password [%s]" % password)

            #: Process crypted download link (dl_link)
            html = self.load(url)
            links = re.findall(self.PATTERN_REDIRECT_LINKS, html, re.I)
            if not links:
                self.log_error(_(u"Broken for link: %s") % link)
            else:
                for link in links:
                    link = link.replace("http://sexuria.com/", "http://www.sexuria.com/")
                    finallink = self.load(link, just_header=True)['location']
                    if not finallink or ("sexuria.com/" in finallink):
                        self.log_error(_(u"Broken for link: %s") % link)
                    else:
                        linklist.append(finallink)

        #: Log result
        if not linklist:
            self.fail(_(u"Unable to extract links (maybe plugin out of date?)"))
        else:
            for i, link in enumerate(linklist):
                self.log_debug(u"Supported link %d/%d: %s" % (i+1, len(linklist), link))

        #: All done, return to caller
        self.log_debug(u"type(name) = %s" % type(name))
        for link in linklist:
            self.log_debug(u"type(link) = %s" % type(link))
        self.log_debug(u"type(folder) = %s" % type(folder))
        self.log_debug(u"type(password) = %s" % type(password))
        return name, linklist, folder, password
