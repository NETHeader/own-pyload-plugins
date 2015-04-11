# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class SexuriaCom(Crypter):
    __name__    = "SexuriaCom"
    __type__    = "crypter"
    __version__ = "0.06"
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
                self.logDebug("Package info found, name [%s] and folder [%s]" % (name, folder))
            pwd = re.search(self.PATTERN_PASSWORD, html).group('pwd')
            if pwd and pwd != "Kein Passwort":
                password = pwd.strip()
                self.logDebug("Password info [%s] found" % password)
            # Process link (dl_link)
            html = self.load(url)
            links = re.findall(self.PATTERN_REDIRECT_LINKS, html)
            if len(links) == 0:
                self.LogError("Plugin broken for link %s" % link)
            else:
                for link in links:
                    link = link.replace("http://sexuria.com/", "http://www.sexuria.com/")
                    finallink = self.load(link, just_header = True)['location']
                    if (finallink == None) or ("sexuria.com/" in finallink):
                        self.LogError("Plugin broken for link %s" % link)
                    else:
                        linklist.append(finallink)

        # Inform the user if no link could have been extracted
        if linklist == []:
            self.fail("Could not extract any links (out of date?)")

        # Debug log
        self.logDebug("Result: %d supported links" % len(linklist))
        for i, link in enumerate(linklist):
            self.logDebug("Supported link %d, %s" % (i+1, link))

        # Done, return to caller
        return name, linklist, folder, password
