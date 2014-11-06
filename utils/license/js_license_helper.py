#!/usr/bin/python
import json
import urllib
import argparse
import textwrap

parser = argparse.ArgumentParser()
parser.add_argument("-L", "--list", help="prints list of js libraries",
                    action="store_true")
parser.add_argument("-l", "--license", help="prints license of specified package",
                    action="store", dest="license")
parser.add_argument("-c", "--copyright", help="prints copyright text of specified package",
                    action="store", dest="copyright")
parser.add_argument("-d", "--description", help="prints description of specified package",
                    action="store", dest="description")
args = parser.parse_args()

npm_packages = open('/tmp/fuel-web/nailgun/npm-shrinkwrap.json')
bower_packages = open('/tmp/fuel-web/nailgun/bower.json')

npm_data = json.load(npm_packages)
bower_data = json.load(bower_packages)
depslist = []
packages = []

def check_url(link):
    if link.getcode() != 404:
        lic = link.readlines()
        out = wrap(lic)
        return out

def wrap(text):
    out = []
    if isinstance(text, list):
        for line in text:
            if len(line) > 90:
                out.append(textwrap.fill(line, 80))
            else:
                out.append(line)
        return ''.join(out)
    else:
        if len(text) > 90:
            return textwrap.fill(text, 80)
        else:
            return text

def parse_npm(deps):
    for k, v in deps.items():
        if k == "dependencies":
            for kk in v.keys():
                if kk not in packages:
                    packages.append(kk)
                    depslist.append('%s/%s' % (kk, v[kk]['version']))
        if isinstance(v, dict):
            parse_npm(v)

def parse_bower(deps):
    for name in deps['dependencies'].keys():
        if name not in packages:
            packages.append(name)
            depslist.append('%s/%s' % (name, deps['dependencies'][name]))

def github_parseurl(url):
    if 'http://github.com' in url:
        parsed = url.replace('http://', 'https://')
        parsed = parsed.replace('/github.com', '/raw.githubusercontent.com')
        parsed = parsed.replace('/blob/', '/')
        parsed = parsed.replace('/raw/', '/')
        return parsed
    elif 'https://github.com' in url:
        parsed = url.replace('/github.com', '/raw.githubusercontent.com')
        parsed = parsed.replace('/blob/', '/')
        parsed = parsed.replace('/raw/', '/')
        return parsed   
    elif 'git://github.com' in url:
        parsed = url.replace('git://', 'https://')
        parsed = parsed.replace('.git', '')
        parsed = parsed.replace('/github.com', '/raw.githubusercontent.com')
        parsed = parsed.replace('.com:', '.com/')
        return parsed
    elif 'git@github.com' in url:
        parsed = url.replace('git@', 'https://')
        parsed = parsed.replace('.git', '')
        parsed = parsed.replace('/github.com', '/raw.githubusercontent.com')
        parsed = parsed.replace('.com:', '.com/')
        return parsed
    elif 'raw.github.com' in url:
        parsed = url.replace('http://', 'https://')
        parsed = parsed.replace('/raw.github.com', '/raw.githubusercontent.com')
        parsed = parsed.replace('/blob/', '/')
        parsed = parsed.replace('/raw/', '/')
        return parsed

def get_description(package):
    link = urllib.urlopen('%s%s' % ('https://registry.npmjs.org/', package))
    if link.getcode() == 404:
        link = urllib.urlopen('%s%s' % ('https://registry.npmjs.org/', package.split('/')[0]))
    data = json.load(link)
    if 'description' in data.keys():
        return wrap(data['description'])

def get_license(package):
    link = urllib.urlopen('%s%s' % ('https://registry.npmjs.org/', package))
    if link.getcode() == 404:
        link = urllib.urlopen('%s%s' % ('https://registry.npmjs.org/', package.split('/')[0]))
    data = json.load(link)
    if 'license' in data.keys():
        if isinstance(data['license'], dict):
            lic = data['license']['type']
            return lic
        else:
            lic = data['license']
            return lic
    if 'licenses' in data.keys():
        for license in data['licenses']:
            if isinstance(license, dict):
                if 'type' in license.keys():
                    lic = license['type']
                    return lic
    if 'versions' in data.keys():
        return get_license('%s/%s' % (package, data['versions'].keys()[0]))
    return 'Unknown'
        
def get_copyright(package):
    link = urllib.urlopen('%s%s' % ('https://registry.npmjs.org/', package))
    if link.getcode() == 404:
        link = urllib.urlopen('%s%s' % ('https://registry.npmjs.org/', package.split('/')[0]))
    data = json.load(link)
    if 'licenses' in data.keys():
        for license in data['licenses']:
            if isinstance(license, dict):
                if 'url' in license.keys():
                    if 'github' in license['url']:
                        licenselink = urllib.urlopen(github_parseurl(license['url']))
                        copyright = check_url(licenselink)
                        if copyright:
                            return copyright
    if 'license' in data.keys():
        if isinstance(data['license'], dict):
            if 'url' in data['license'].keys():
                if 'github' in data['license']['url']:
                    licenselink = urllib.urlopen(github_parseurl(data['license']['url']))
                    copyright = check_url(licenselink)
                    if copyright:
                        return copyright
    if 'repository' in data.keys():
        if 'url' in data['repository']:
            if '/github.com' in data['repository']['url']:
                link = data['repository']['url']
                link += '/master/LICENSE'
                licenselink = urllib.urlopen(github_parseurl(link))
                copyright = check_url(licenselink)
                if copyright:
                    return copyright
                link += '.txt'
                licenselink = urllib.urlopen(github_parseurl(link))
                copyright = check_url(licenselink)
                if copyright:
                    return copyright
    if 'versions' in data.keys():
        return get_copyright('%s/%s' % (package, data['versions'].keys()[0]))
    return ''

if args.list:
    parse_npm(npm_data)
    parse_bower(bower_data)
    for package in sorted(set(depslist)):
        print package

if args.license:
    print get_license(args.license)

if args.copyright:
    print get_copyright(args.copyright)

if args.description:
    print get_description(args.description)