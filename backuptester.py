import configparser
import json
import glob
import os
import datetime
import dateparser
import smtplib
import ssl
import string
import requests


def sendSMS(plan_id, api_token, number_from, number_to, message):

    headers = {
        'Authorization': 'Bearer {0}'.format(plan_id),
        'Content-Type': 'application/json',
    }

    data = '\n  {{\n   "from": "{0}",\n   "to": [ "{1}" ],\n  "body": "{2}"\n  }}'.format(number_from, number_to, message)
    response = requests.post('https://sms.api.sinch.com/xms/v1/{0}/batches'.format(api_token), headers=headers, data=data)

def DoCheck(dir, rls, r):
    now = datetime.datetime.now()

    ok = False
    errors = []

    rules = json.loads(rls)
    if not isinstance(rules["file"], list):
        flist = [rules["file"]]
    else:
        flist = rules["file"]

    for f in flist:

        files = glob.glob(os.path.join(dir, f))

        if not files:        	
            r.write("{0}\n".format(json.dumps({"file": os.path.join(dir, f), "ok": False, "rule": rules["time"], "size": str(0), "date": "",})))
            errors.append({"file": os.path.join(dir, f), "ok": False, "rule": rules["time"], "size": str(0), "date": "",})
        else:
            for file in files:
                ok = False
                if now - datetime.datetime.fromtimestamp(os.path.getmtime(file)) < now - dateparser.parse(rules["time"]):
                    ok = True
                    if rules["rule"] == "some":
                        break

                if rules["rule"] == "all":
                    if ok == False:
                        errors.append({"file": file, "ok": ok, "rule": rules["time"], 
                            "size": str(os.stat(file).st_size), "date": str(datetime.datetime.fromtimestamp(os.path.getmtime(file))),})

                    r.write("{0}\n".format(json.dumps({"file": file, "ok": ok, "rule": rules["time"], 
                        "size": str(os.stat(file).st_size), "date": str(datetime.datetime.fromtimestamp(os.path.getmtime(file))),})))



            if rules["rule"] == "some":
                r.write("{0}\n".format(json.dumps({"file": os.path.join(dir, f),"ok": ok,"rule": rules["time"],})))
                if ok == False:
                	errors.append({"file": os.path.join(dir, f),"ok": ok,"rule": rules["time"],})

    return errors

def start():
    config = configparser.ConfigParser()
    config.read("backuptester.ini")

    directories = []

    errors = []

    for directory in config["dirs"]:
        if len(config["dirs"][directory].splitlines()) > 1:
            directories.append((directory, config["dirs"][directory].splitlines()))
        else:
            directories.append((directory, config["dirs"][directory]))

    f = open(config["global"]["statfile"], "w")

    for directory, values in directories:
        if isinstance(values, list):
            for value in values:
                e = DoCheck(directory, value, f)
                if e:
                	errors.append(e)
        else:
            e = DoCheck(directory, values, f)
            if e:
            	errors.append(e)


    if errors:
        # send email

        _DEFAULT_CIPHERS = ('ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:!eNULL:!MD5')
        smtp_server = smtplib.SMTP(config['global']['smtp'], port=str(config['global']['smtp_port']))

        # only TLSv1 or higher
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3

        context.set_ciphers(_DEFAULT_CIPHERS)
        context.set_default_verify_paths()
        context.verify_mode = ssl.CERT_REQUIRED

        if smtp_server.starttls()[0] != 220:
            return False # cancel if connection is not encrypted
        smtp_server.login(config['global']['smtp_login'], config['global']['smtp_password'])


        BODY = string.join((
            "From: %s" % config['global']['from'],
            "To: %s" % config['global']['to'],
            "Subject: %s" % "backup errors" ,
            "",
            str(errors)
            ), "\r\n")            

        smtp_server.sendmail(config['global']['from'],config['global']['to'], BODY)

        # send sms

        sendSMS(config['sms']['plan_id'], 
            config['sms']['api_token'], 
            config['sms']['number_from'], 
            config['sms']['number_to'], 'error in backup')

    f.close()


if __name__ == "__main__":
    start()

