"""
Summary: This container allows you to create your own HPEPRINT solution, using your own e-mail server. Printer must support FTP print (disabled on HP by default)
Maintainer : s@mck.la
Description: This docker container will:
1. Check an IMAP mailbox every 'SCHEDULE' seconds for unread/unseen e-mails in the \Inbox
2. Check if the file extension is in 'ALLOWED_FILE_TYPES' and mark the e-mail as read/seen. 
3 .If the file extension is in the 'ALLOWED_FILE_TYPES', download the attachment.
4. Upload the file via FTP to the 'PRINTER_IP', to print.

"""

import imaplib
import email
import ftplib
import time
import datetime
import re
import os
from email.header import decode_header
from email.message import EmailMessage

outputdir="downloadedFiles"
runTask = 1
if 'PRINTER_IP' in os.environ:
    printerIP = os.environ['PRINTER_IP']
if 'ALLOWED_FILE_TYPES' in os.environ:
    allowedFileTypes = (os.environ['ALLOWED_FILE_TYPES']).split(" ")
else:
    allowedFileTypes = ["pdf"]
if 'IMAP_SERVER_IP' in os.environ:  
    IMAPserver = os.environ['IMAP_SERVER_IP']
if 'IMAP_USERNAME' in os.environ:  
    IMAPuser = os.environ['IMAP_USERNAME']
if 'IMAP_PASSWORD' in os.environ:  
    IMAPpassword = os.environ['IMAP_PASSWORD']
if 'ALLOWED_SENDERS' in os.environ:  
    allowedSenders = list(os.environ['ALLOWED_SENDERS'].split(' '))
else:
    allowedSenders = []
if 'PRINT_ACTIVE' in os.environ:  # Allows you to run the container in test mode, i.e. do everything but actually print the file.
    printActive = os.environ['PRINT_ACTIVE']
else:
    printActive = True

if 'SCHEDULE' in os.environ:  
    recheckEveryXSeconds = int(os.environ['SCHEDULE'])
else:
    recheckEveryXSeconds = 60

def get_valid_filename(msg: EmailMessage):
    filename = msg.get_filename()
    #if decode_header(filename)[0][1] is not None:
    #    filename = decode_header(filename)[0][0].decode(decode_header(filename)[0][1])
    return filename

def ftp_to_printer(filename,printerIP:str=printerIP,user:str='anonymous',password:str='user@home.com'):
    global runTask
    try:
        session = ftplib.FTP(printerIP,user,password)
    except:
        print("error - could not connect to FTP server",printerIP)
        runTask = 0
    else:
        print(datetime.datetime.now(),)
        file = open(filename,'rb')                  # file to send
        session.storbinary('STOR ' + filename, file)     # send the file
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
    fromEmailAddress = re.search(r'<([A-z]|[0-9]|[_+-]){0,255}@([A-z]|[0-9]|[_+-]){0,255}\.([A-z]|[-]){0,10}>',str({mail["from"]}))
    fromEmailAddress = fromEmailAddress.group().replace('<','').replace('>','')
    #print("From Address:",fromEmailAddress)
    fromEmailAddress = fromEmailAddress.split('@')
    fromDomainName = fromEmailAddress[1]
    fromEmailAddress = '@'.join(fromEmailAddress)
    #print("from domain",fromDomainName,"from email",fromEmailAddress)
    #print("E-mail is from",{mail["from"]})
    if len(allowedSenders) != 0 and (fromDomainName in allowedSenders or fromEmailAddress in allowedSenders):
        print(datetime.datetime.now(),"sender is authorized [",fromEmailAddress,"|",fromDomainName,"]")
        for part in mail.walk():
            if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                filename, encoding = decode_header(part.get_filename())[0]

                if(encoding is not None):
                    filename = filename.decode(encoding)

                outputfilepath = outputdir + '/' + filename    
                fileextension = filename.split('.')
                fileextension.reverse()

                if fileextension[0] in allowedFileTypes:
                    open(outputfilepath , 'wb').write(part.get_payload(decode=True))
                    print(datetime.datetime.now(),"Attempting to print",filename)
                    print(filename,part.get_content_maintype(),part.get('Content-Disposition'),fileextension[0])
                    print(datetime.datetime.now(),fileextension[0],"is an allowed filetype")
                    print(datetime.datetime.now(),"Printing",fileextension[0]," attachment from e-mail:",fromEmailAddress,", stored at:",outputfilepath,f",to printer IP: {printerIP}")
                    if printActive == True:
                        ftp_to_printer(outputfilepath)
                    else:
                        print(datetime.datetime.now(),"This is where I would normally print",outputfilepath,", Currently: ACTIVE_PRINT!=True")
            #else:
            #    print(datetime.datetime.now(),filename,"is not an allowed filetype")
    else:
        print(datetime.datetime.now(),"sender is NOT authorized [",fromEmailAddress,"|",fromDomainName,"] : No further action will be taken.")
# Download all the attachment files for all emails in the inbox.
def downloadAllAttachmentsInInbox(server:str=IMAPserver, user:str=IMAPuser, password:str=IMAPpassword, outputdir:str=outputdir):
    m = connect(server, user, password)
    resp, items = m.search(None, "UnSeen")
    print(f"{datetime.datetime.now()} Checking e-mail account",IMAPuser)
    print(datetime.datetime.now(),"ALLOWED_FILE_TYPES:",','.join(allowedFileTypes))
    print(datetime.datetime.now(),"ALLOWED_SENDERS:",','.join(allowedSenders))
    
    items = items[0].split()
    print(datetime.datetime.now(),"Found",len(items),"e-mails")

    for emailid in items:
        m.store(emailid, '+FLAGS', '(\\Seen)')  ## Mark the e-mail as read so it won't be printed again
        downloaAttachmentsInEmail(m, emailid, outputdir)
    m.logout
while runTask == 1:
    downloadAllAttachmentsInInbox()
    print(f"{datetime.datetime.now()} Waiting {recheckEveryXSeconds} seconds")
    time.sleep(recheckEveryXSeconds)



