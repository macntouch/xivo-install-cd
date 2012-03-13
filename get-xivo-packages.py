#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import with_statement
__version__ = "$Revision$ $Date$"
__author__    = "Guillaume Bour <gbour@proformatique.com>"
__license__ = """
        Copyright (C) 2010    Proformatique

        This program is free software; you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation; either version 2 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License along
        with this program; if not, write to the Free Software Foundation, Inc.,
        51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""

import sys, urllib2, httplib, os, os.path
from optparse import OptionParser

DAKBASE = 'http://mirror.xivo.fr/debian/dists/'
SUITES    = {
    'skaro': [
        'squeeze-xivo-skaro-rc/main/binary-i386/Packages',
        'squeeze-xivo-skaro-rc/non-free/binary-i386/Packages',
        'squeeze-xivo-skaro/main/binary-i386/Packages',
        'squeeze-xivo-skaro/non-free/binary-i386/Packages',
        'squeeze/main/binary-i386/Packages',
        'squeeze/contrib/binary-i386/Packages',
        'squeeze/non-free/binary-i386/Packages',
    ],

}

if __name__ == '__main__':
    usage    = "Usage: %prog [options] path/to/download"
    parser = OptionParser(usage=usage)
    parser.add_option('-l', '--list-packages'                 , dest='list'         , action='store_true',
        default=False, help="list available packages (do not download)")
    parser.add_option('-f', '--force'                 , dest='force'         , action='store_true',
        default=False, help="force re-download all packages")
    parser.add_option('-s', '--suite'     , dest='suite'    , action='store',
        type='string', default='gallifrey', help="XiVO suite. set SUITE to *list* to list all available suites")

    (options, args) = parser.parse_args()
    if options.suite in ['list', '*list*']:
        print "Available suites:"
        for suite in SUITES.keys():
            print " *", suite
        sys.exit(0)

    if not options.list and len(args) != 1:
        parser.print_help(); sys.exit(2)

    if options.suite not in SUITES:
        print "Unknown suite", options.suite; sys.exit(2)


    stats         = {'size': 0, 'installed-size': 0}
    packages = []

    # whitelist
    if options.suite == "skaro-dev":
        include = [
            'pf-fai-xivo-1.2-skaro-dev',
            'pf-fai-dev',
        ]
    elif options.suite == "skaro-rc":
        include = [
            'pf-fai-xivo-1.2-skaro',
            'pf-fai',
        ]
    elif options.suite == "skaro":
        include = [
            'pf-fai-xivo-1.2-skaro',
            'pf-fai',
        ]
    exclude = [
        'cracklib',
        'dahdi-linux-source',
        'libcrack2',
        'libctl',
        'libnet-ssh-ruby',
        'libruby',
        'meep', 'libmeep',
        'misdn-kernel-source',
        'mpb',
        'pf-sys-ssh',
        'pfbotnet', 'libpfbotnet',
        'python-cap',
        'python-crack',
        'sangoma-dbg',
        'sangoma-wanpipe-source',
        'squid',
        'swig',
        'tshark',
        'wireshark',
        'xivo-dev-ssh-pubkeys',
    ]
    skip=False
    
    for src in SUITES[options.suite]:
        f = urllib2.urlopen(DAKBASE + src)
        for line in f.readlines():
            if line.startswith('Package:'):
                skip = True
                pacnam = line.split(' ')[1][:-1]

                if not pacnam in include and \
                        (pacnam.endswith('-dev') or \
                        len(filter(lambda x: pacnam.startswith(x), exclude)) > 0):
                    continue
                
                skip = False

            if skip:
                continue

            if line.startswith('Installed-Size:'):
                stats['installed-size'] += int(line.split(' ')[1])
            elif line.startswith('Size:'):
                stats['size'] += int(line.split(' ')[1])
            elif line.startswith('Filename:'):
                if 'dalek' in line:
                    continue
            
                packages.append(line.split(' ')[1][:-1])

        f.close()
    
    
    packages.sort()
    if options.list:
        import pprint; pprint.pprint(packages)
        print stats
        sys.exit(0)


    # 2. downloading packages
    if not os.path.exists(args[0]):
        os.makedirs(args[0])
    
    conn = httplib.HTTPConnection('mirror.xivo.fr')
    for package in packages:
        debfile = package.rsplit('/', 1)[-1]
        print " . downloading", debfile, ':',

        if os.path.exists(args[0] + '/' + debfile):
            localsize = os.path.getsize(args[0] + '/' + debfile)
            
            conn.request("HEAD", '/debian/' + package)
            resp = conn.getresponse()
            try:
                netsize     = int(dict(resp.getheaders()).get('content-length'))
            except:
                netsize     = -1
            conn.close()
            
            if netsize == localsize:
                print 'skipping...'; continue
        
        print '...'
        conn.request("GET", '/debian/' + package)
        resp = conn.getresponse()
        
        with open(args[0] + '/' + debfile, 'wb') as f:
            while True:
                data = resp.read(8192)
                if len(data) == 0:
                    break
                    
                f.write(data)
            
        conn.close()

