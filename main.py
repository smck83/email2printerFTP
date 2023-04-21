"""
Summary: This container allows you to create your own HPEPRINT solution, using your own e-mail server. Printer must support FTP print (disabled on HP by default)
Maintainer : s@mck.la
Description: This docker container will:
1. Check an IMAP mailbox every 'SCHEDULE' seconds for unread/unseen e-mails in the \Inbox 
2. Download their attachments, and mark the e-mail as read/seen
3. Check if the file extension is in 'ALLOWED_FILE_TYPES' and if so, upload the file via FTP to the 'PRINTER_IP'



"""

import imaplib
import email
import ftplib
import time
import datetime
import re
import os

outputdir="downloadedFiles"
runTask = 1
if 'PRINTER_IP' in os.environ:
    printerIP = os.environ['PRINTER_IP']
if 'ALLOWED_FILE_TYPES' in os.environ:
    allowedFileTypes = (os.environ['ALLOWED_FILE_TYPES']).split(" ")
else:
    allowedFileTypes = ["pdf","docx","xlsx","doc","xls"]
if 'IMAP_SERVER_IP' in os.environ:  
    IMAPserver = os.environ['IMAP_SERVER_IP']
if 'IMAP_USERNAME' in os.environ:  
    IMAPuser = os.environ['IMAP_USERNAME']
if 'IMAP_PASSWORD' in os.environ:  
    IMAPpassword = os.environ['IMAP_PASSWORD']


if 'SCHEDULE' in os.environ:  
    recheckEveryXSeconds = int(os.environ['SCHEDULE'])
else:
    recheckEveryXSeconds = 60

def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

def ftp_to_printer(filename,printerIP:str=printerIP,user:str='anonymous',password:str='user@home.com'):
    global runTask
    try:
        session = ftplib.FTP(printerIP,user,password)
    except:
        print("error - could not connect to FTP server",printerIP)
        runTask = 0
    else:

        file = open(filename,'rb')                  # file to send
        session.storbinary('STOR print.txt', file)     # send the file
        file.close()                                    # close file and FTP
        session.quit()       

# Connect to an IMAP server
def connect(server, user, password):
    m = imaplib.IMAP4_SSL(server)
    m.login(user, password)
    m.select('Inbox')
    
    return m

# Download all attachment files for a given email
def downloaAttachmentsInEmail(m, emailid, outputdir):
    resp, data = m.fetch(emailid, "(BODY.PEEK[])")
    email_body = data[0][1]
    mail = email.message_from_bytes(email_body)
    if mail.get_content_maintype() != 'multipart':
        return
    print(mail.walk)
    for part in mail.walk():
        if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
            filename = get_valid_filename(part.get_filename())
            print("Attempting to print",filename)
            outputfilepath = outputdir + '/' + get_valid_filename(part.get_filename())
            open(outputfilepath, 'wb').write(part.get_payload(decode=True))
            fileextension = list(filename.split('.'))
            fileextension.reverse()
            if  fileextension[0] in allowedFileTypes:
                print(datetime.datetime.now(),fileextension[0],"is an allowed filetype")
                print(datetime.datetime.now(),"Printing",fileextension[0]," attachment from e-mail",outputfilepath,f"to printer IP: {printerIP}")
                ftp_to_printer(outputfilepath)
            else:
                print(datetime.datetime.now(),fileextension[0],"is not an allowed filetype")
    
# Download all the attachment files for all emails in the inbox.
def downloadAllAttachmentsInInbox(server:str=IMAPserver, user:str=IMAPuser, password:str=IMAPpassword, outputdir:str=outputdir):
    m = connect(server, user, password)
    resp, items = m.search(None, "UnSeen")
    print(f"{datetime.datetime.now()} Checking e-mail account",IMAPuser)
    
    items = items[0].split()
    print(len(items))

    for emailid in items:
        m.store(emailid, '+FLAGS', '(\\Seen)')  ## Mark the e-mail as read so it won't be printed again
        downloaAttachmentsInEmail(m, emailid, outputdir)

while runTask == 1:
    downloadAllAttachmentsInInbox()
    print(f"{datetime.datetime.now()} Waiting {recheckEveryXSeconds} seconds")
    time.sleep(recheckEveryXSeconds)



