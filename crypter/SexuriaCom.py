# -*- coding: utf-8 -*-

import re
from module.plugins.internal.Crypter import Crypter

class SexuriaCom(Crypter):
    __name__    = "SexuriaCom"
    __type__    = "crypter"
    __version__ = "0.10"
    __description__ = """Sexuria.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("NETHead", "NETHead.AT.gmx.DOT.net")]
    __pattern__ = r'http://(?:www\.)?sexuria\.com/(v1/)?(Pornos_Kostenlos_.+?_(\d+)\.html|dl_links_\d+_\d+\.html|id=\d+\&part=\d+\&link=\d+)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                  ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    # Constants
    PATTERN_SUPPORTED_MAIN     = re.compile(r'http://(www\.)?sexuria\.com/(v1/)?Pornos_Kostenlos_.+?_(\d+)\.html', flags=re.IGNORECASE)
    PATTERN_SUPPORTED_CRYPT    = re.compile(r'http://(www\.)?sexuria\.com/(v1/)?dl_links_\d+_(?P<id>\d+)\.html', flags=re.IGNORECASE)
    PATTERN_SUPPORTED_REDIRECT = re.compile(r'http://(www\.)?sexuria\.com/out\.php\?id=(?P<id>\d+)\&part=\d+\&link=\d+', flags=re.IGNORECASE)
    PATTERN_TITLE              = re.compile(r'<title> - (?P<title>.*) Sexuria - Kostenlose Pornos - Rapidshare XXX Porn</title>', flags=re.IGNORECASE)
    PATTERN_PASSWORD           = re.compile(r'<strong>Passwort: </strong></div></td>.*?bgcolor="#EFEFEF">(?P<pwd>.*?)</td>', flags=re.IGNORECASE | re.DOTALL)
    PATTERN_DL_LINK_PAGE       = re.compile(r'"(dl_links_\d+_\d+\.html)"', flags=re.IGNORECASE)
    PATTERN_REDIRECT_LINKS     = re.compile(r'value="(http://sexuria\.com/out\.php\?id=\d+\&part=\d+\&link=\d+)" readonly', flags=re.IGNORECASE)
    LIST_PWDIGNORE             = ["Kein Passwort", "-"]

    def decrypt(self, pyfile):
        # Init
        self.pyfile = pyfile
        self.package = pyfile.package()

        # Decrypt and add links
        package_name, self.links, folder_name, package_pwd = self.decryptLinks(self.pyfile.url)
        if package_pwd:
            self.pyfile.package().password = package_pwd
        self.packages = [(package_name, self.links, folder_name)]


    def decryptLinks(self, url):
        linklist = []
        name = self.package.name
        folder = self.package.folder
        password = None

        if re.match(self.PATTERN_SUPPORTED_MAIN, url):
            # Processing main page
            html = self.load(url)
            links = re.findall(self.PATTERN_DL_LINK_PAGE, html)
            for link in links:
                linklist.append("http://sexuria.com/v1/" + link)

        elif re.match(self.PATTERN_SUPPORTED_REDIRECT, url):
            # Processing direct redirect link (out.php), redirecting to main page
            id = re.search(self.PATTERN_SUPPORTED_REDIRECT, url).group('id')
            if id:
                linklist.append("http://sexuria.com/v1/Pornos_Kostenlos_liebe_" + id + ".html")

        elif re.match(self.PATTERN_SUPPORTED_CRYPT, url):
            # Extract info from main file
            id = re.search(self.PATTERN_SUPPORTED_CRYPT, url).group('id')
            html = self.load("http://sexuria.com/v1/Pornos_Kostenlos_info_" + id + ".html") #, decode=True
            title = re.search(self.PATTERN_TITLE, html).group('title').strip()
            if title:
                name = folder = title
                self.log_debug("Package info found, name [%s] and folder [%s]" % (name, folder))
            pwd = re.search(self.PATTERN_PASSWORD, html).group('pwd')
            if pwd and not (pwd in self.LIST_PWDIGNORE):
                password = pwd.strip()
                self.log_debug("Password info [%s] found" % password)

            # Process link (dl_link)
            html = self.load(url)
            links = re.findall(self.PATTERN_REDIRECT_LINKS, html)
            if not links:
                self.log_error(_("Broken for link: %s") % link)
            else:
                for link in links:
                    link = link.replace("http://sexuria.com/", "http://www.sexuria.com/")
                    finallink = self.load(link, just_header = True)['location']
                    if not finallink or ("sexuria.com/" in finallink):
                        self.log_error(_("Broken for link: %s") % link)
                    else:
                        linklist.append(finallink)

        # Log result
        if not linklist:
            self.fail(_("Unable to extract links (maybe plugin out of date?)"))
        else:
            self.log_debug("Result: %d supported links" % len(linklist))
            for i, link in enumerate(linklist):
                self.log_debug("Supported link %d: %s" % (i+1, link))

        # Done, return to caller
        return name, linklist, folder, password
