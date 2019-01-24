#!/usr/bin/env python

import sys
import os
import re
import tarfile

import internetarchive as ia

DESCRIPTION = """{pkgdesc}

This item contains old versions of the <a href="https://www.archlinux.org/packages/{pkgname}">Arch Linux package for {pkgname}</a>.
Website of the upstream project: <a href="{url}">{url}</a>
License: {license}
See the <a href="https://wiki.archlinux.org/index.php/Arch_Linux_Archive">Arch Linux Archive documentation</a> for details.
"""

SYMLINK_YEAR_REGEXP = re.compile(r'.*/repos/([0-9]{4})/')

def clean_name(name):
    """Remove chars that are not allowed in an Internet Archive identifier: @.+
    Only alphanumerics, - and _ and allowed."""
    res = name.replace('@', '_')
    res = res.replace('+', '_')
    res = res.replace('.', '_')
    return res

def extract_pkginfo(package):
    """Given a package (.tar.xz filename), extract and parse its .PKGINFO file as a dict"""
    with tarfile.open(package, mode='r|*', encoding='utf-8') as tar:
        # Manual seeking to find .PKGINFO without having to uncompress the whole package
        while True:
            f = tar.next()
            if f.name == '.PKGINFO':
                break
        pkginfo = tar.extractfile(f).readlines()
        # Parse .PKGINFO
        res = dict()
        for line in pkginfo:
            m = re.match(r'([^=]*) = (.*)', line.decode('utf8'))
            if m:
                # TODO: support multi-valued attributes
                key, value = m[1], m[2].strip()
                res[key] = value
        return res

def upload_pkg(identifier, pkgname, metadata, directory, years):
    """Upload all versions for package given by [directory], provided they date back
    from one of the [years]"""
    files = []
    for f in os.scandir(directory):
        if not f.is_symlink():
            continue
        path = os.readlink(f)
        match = re.match(SYMLINK_YEAR_REGEXP, path)
        if not match:
            continue
        year = match[1]
        if year not in years:
            continue
        files.append(f.path)
    if not files:
        return
    # Get last package, to extract a description
    last_pkg = sorted(filter(lambda x: not x.endswith('.sig'), files))[-1]
    pkginfo = extract_pkginfo(last_pkg)
    pkgdesc = pkginfo['pkgdesc'] if 'pkgdesc' in pkginfo else ''
    metadata['description'] = DESCRIPTION.format(pkgname=pkgname, pkgdesc=pkgdesc, url=pkginfo['url'], license=pkginfo['license'])
    metadata['rights'] = 'License: ' + pkginfo['license']
    #print(pkgname, len(files))
    #print(metadata)
    try:
        res = ia.upload(identifier, files=files, metadata=metadata)
        if not all([x.status_code == 200 for x in res]):
            ok = len([x for x in res if x.status_code == 200])
            nok = len([x for x in res if x.status_code != 200])
            codes = set([x.status_code for x in res])
            print("{}: only {}/{} files uploaded, status codes: {}".format(identifier, ok, ok+nok, codes), file=sys.stderr)
            print(directory)
    except Exception as e:
        print("{}: exception raised".format(identifier), file=sys.stderr)
        print(e, file=sys.stderr)
        print(directory)


def main(pkg_dir, years):
    """Upload all versions of a single package, from the given years"""
    pkgname = os.path.basename(pkg_dir)
    identifier = clean_name('archlinux_pkg_' + pkgname)
    metadata = {
        #'collection': ['test_collection', 'open_source_software'],
        #'collection': ['open_source_software'],
        'collection': ['archlinuxarchive'],
        'mediatype': 'software',
        'publisher': 'Arch Linux',
        'creator': 'Arch Linux',
        'subject': ['archlinux', 'archlinux package'],
    }
    metadata['title'] = pkgname + " package archive from Arch Linux"
    metadata['subject'].append(pkgname)
    upload_pkg(identifier, pkgname, metadata, pkg_dir, years)

if __name__ == '__main__':
    main(sys.argv[1], ['2013', '2014', '2015', '2016'])
