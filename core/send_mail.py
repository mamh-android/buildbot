#!/usr/bin/python
# v1.0
#    sendmail script
#    Author: yfshi@marvell.com

import getopt
import sys
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Gerrit admin user
ADM_USER = "buildfarm"

#Gerrit server
GERRIT_SERVER = "privgit.marvell.com"

#project name
PROJECT_GROUP = "cosmo-admin"

#Mavell SMTP server
SMTP_SERVER="10.68.76.51"

def get_mail_list():
    global ADM_USER
    global GERRIT_SERVER
    global PROJECT_GROUP
    email_list = []
    args = "ssh -p 29418 " + ADM_USER + "@" + GERRIT_SERVER + " gerrit gsql -c \"select\ group_id\ from\ account_groups\ WHERE\ name=\\\'" + PROJECT_GROUP + "\\\'\""
    #group_id is the gr_id in the gerrit database where matching PROJECT_GROUP
    group_id = os.popen(args).read().split()[2]
    args = "ssh -p 29418 " + ADM_USER + "@" + GERRIT_SERVER + " gerrit gsql -c \"select\ account_id\ from\ account_group_members\ WHERE\ group_id=\\\'" + group_id + "\\\'\""
    #account_id is the account_id in the gerrit database where matching PROJECT_GROUP
    account_id = os.popen(args).read().split()
    account_id.pop()
    account_id.pop()
    account_id.pop()
    account_id.pop()
    account_id.pop(0)
    account_id.pop(0)
    for i in account_id:
        args = "ssh -p 29418 " + ADM_USER + "@" + GERRIT_SERVER + " gerrit gsql -c \"select\ preferred_email\ from\ accounts\ WHERE\ account_id=\\\'" + i + "\\\'\""
        email_list.append(os.popen(args).read().split()[2])
    return email_list

def send_html_mail(subject, from_who, to_who, build_result):
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_who
    msg['To'] = ", ".join(to_who)

    # Create the body of the message (a plain-text and an HTML version).
    text = "Hi!\nHow are you?\nIt's a test link:\n//sh-srv06/"
    if (build_result == "success"):
        text = "Hi!\nCosmo build success\nIt's a test link:\n//sh-srv06/"
    elif (build_result == "failure"):
        text = "Hi!\nCosmo build failed\n"
    elif (build_result == "nobuild"):
        text = "Hi!\nCosmo build nobuild\n"
    else:
        text = "Hi!\nHow are you?\nIt's a test link:\n//sh-srv06/"
    
    #html sample
    html = """\
    <html>
      <head></head>
      <body>
        <p>Hi!<br>
           How are you?<br>
           Here is the <a href="\\sh-srv06">link</a> you wanted.
        </p>
      </body>
    </html>
    """

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    #part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    #msg.attach(part2)

    # Send the message via local SMTP server.
    #s = smtplib.SMTP('localhost')
    global SMTP_SERVER
    s = smtplib.SMTP(SMTP_SERVER)
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.sendmail(from_who, to_who, msg.as_string())
    s.quit()

#User help
def usage():
    print "\tsend_mail.py "
    print "\t      [-r] result <success|failure|nobuild>"
    print "\t      [-d] image path"
    print "\t      [-h] help"

def main(argv):
    results = ""
    dir_path = ""
    get_mail_list()
    send_html_mail("It's just a test",ADM_USER,["yfshi@marvell.com"],"success")
    #send_html_mail("It's just a test", ADM_USER, get_mail_list(), "success")
    try:
        opts, args = getopt.getopt(argv,"r:d:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-r"):
            results = arg
        elif opt in ("-d"):
            dir_path = arg
    if (results == ""):
        usage()
        sys.exit(2)
    else:
        get_mail_list()

if __name__ == "__main__":
    main(sys.argv[1:])
