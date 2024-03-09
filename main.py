"""
Summary: This container allows you to create your own HPEPRINT solution, using your own e-mail server. Printer must support FTP print (disabled on HP by default)
Maintainer : s@mck.la
Description: This docker container will:
1. Check an IMAP mailbox every 'SCHEDULE' seconds for unread/unseen e-mails in the Inbox
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
import smtplib
import requests
from email.message import EmailMessage
from email.header import decode_header
from email.message import EmailMessage

outputdir="downloadedFiles"
runTask = 1
if 'PRINTER_IP' in os.environ:
    printerIP = os.environ['PRINTER_IP']
if 'ALLOWED_FILE_TYPES' in os.environ:
    allowedFileTypes = (os.environ['ALLOWED_FILE_TYPES']).lower().split(" ")
else:
    allowedFileTypes = ["pdf"]
if 'IMAP_SERVER_IP' in os.environ:  
    IMAPserver = os.environ['IMAP_SERVER_IP']
if 'IMAP_USERNAME' in os.environ:  
    IMAPuser = os.environ['IMAP_USERNAME']
if 'GOTENBERG_API' in os.environ:  
    GOTENBERGApi = os.environ['GOTENBERG_API']
if 'IMAP_PASSWORD' in os.environ:  
    IMAPpassword = os.environ['IMAP_PASSWORD']
if 'ALLOWED_SENDERS' in os.environ:  
    allowedSenders = list(os.environ['ALLOWED_SENDERS'].lower().split(' '))
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
if 'SMTP_SERVER' in os.environ:  
    SMTPserver = os.environ['SMTP_SERVER']
else:
    SMTPserver = IMAPserver
if 'SMTP_USERNAME' in os.environ:  
    SMTPuser = os.environ['SMTP_USERNAME']
else:
    SMTPuser = IMAPuser
if 'SMTP_PASSWORD' in os.environ:  
    SMTPpassword  = os.environ['SMTP_PASSWORD']
else:
    SMTPpassword = IMAPpassword
if 'SMTP_SENDER' in os.environ:  
    SMTPsender  = os.environ['SMTP_SENDER']
else:
    SMTPsender = f"Print Update <{IMAPuser}>"

gotenbergFileTypes = ["bib","doc","xml","docx","fodt","html","ltx","txt","odt","ott","pdb","psw","rtf","sdw","stw","sxw","uot","vor","wps","epub","png","bmp","emf","eps","fodg","gif","jpg","met","odd","otg","pbm","pct","pgm","ppm","ras","std","svg","svm","swf","sxd","sxw","tiff","xhtml","xpm","fodp","pages","potm","pot","pptx","pps","ppt","pwp","sda","sdd","sti","sxi","uop","wmf","csv","dbf","dif","fods","ods","ots","pxl","sdc","slk","stc","sxc","uos","xls","xlt","xlsx","tif","jpeg","odp","odg","dotx","xltx"]
def sendEmail(receivers,subject,emailbody):
    msg = EmailMessage()
    msg['Subject'] = f"Email2PrinterFtp - {subject}"
    msg['From'] = SMTPsender
    msg['To'] = [receivers]
    msg.set_content(emailbody)

    s = smtplib.SMTP(SMTPserver,25)
    try:
        s.connect(SMTPserver,587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(SMTPuser, SMTPpassword)
        s.send_message(msg)
        print(datetime.datetime.now(),"Trying to send e-mail response")
    except Exception as e:
        s.quit()
        print(datetime.datetime.now(),"Something went wrong:",e)
    else:
        print(datetime.datetime.now(),"Success! - E-mail response sent to ",receivers)
        s.quit()

def get_valid_filename(msg: EmailMessage):
    filename = msg.get_filename()
    #if decode_header(filename)[0][1] is not None:
    #    filename = decode_header(filename)[0][0].decode(decode_header(filename)[0][1])
    return filename

def ftp_to_printer(filename,printerIP:str=printerIP,user:str='anonymous',password:str='user@home.com'):
    global runTask
    try:
        session = ftplib.FTP(printerIP,user,password)
    except Exception as e:
        print("error - could not connect to FTP server",printerIP)
        printLog["fail"].append(f"\n\nWARNING: FTP TO PRINTER[{printerIP}] {e}")
        print(e)
        #runTask = 0
    else:
        print(datetime.datetime.now(),)
        printLog["success"].append(f"\n\nSUCCESS: FTP TO PRINTER[{printerIP}]")
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

def convertdocx2pdf(filename):

    url = GOTENBERGApi + "/forms/libreoffice/convert"
    

    payload = {}
    files = [
        ('files', (filename, open(filename, 'rb')))
    ]
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    # Check if the request was successful
    if response.status_code == 200:
        # Open a file in binary write mode
        newfilename = f"{filename}.pdf"
        with open(newfilename, 'wb') as f:
            # Write the content of the response to the file
            f.write(response.content)
        print(f"PDF file saved successfully! {newfilename}")
        return newfilename
    else:
        print("Error converting document")
        #printLog["fail"].append(f"{response.text}")


# Download all attachment files for a given email
def downloaAttachmentsInEmail(m, emailid, outputdir):
    printLog = {}
    printLog["fail"] = []
    printLog["success"] = []
    printLog["info"] = []    

    resp, data = m.fetch(emailid, "(BODY.PEEK[])")
    email_body = data[0][1]
    mail = email.message_from_bytes(email_body)
    
    if mail.get_content_maintype() != 'multipart':
        return
    fromEmailAddress = re.search(r'<([A-z]|[0-9]|[._+-]){0,255}@([A-z]|[0-9]|[_+-]){0,255}\.([A-z]|[-.]){0,10}>',str({mail["from"]}))

    # prior to 8th Feb - fromEmailAddress = re.search(r'<([A-z]|[0-9]|[_+-]){0,255}@([A-z]|[0-9]|[_+-]){0,255}\.([A-z]|[-]){0,10}>',str({mail["from"]}))
    fromEmailAddress = fromEmailAddress.group().replace('<','').replace('>','')
    #print("From Address:",fromEmailAddress)
    fromEmailAddress = fromEmailAddress.split('@')
    fromDomainName = fromEmailAddress[1]
    fromEmailAddress = '@'.join(fromEmailAddress)
    #print("from domain",fromDomainName,"from email",fromEmailAddress)
    #print("E-mail is from",{mail["from"]})
    if len(allowedSenders) != 0 and (fromDomainName.lower() in allowedSenders or fromEmailAddress.lower() in allowedSenders):
        print(datetime.datetime.now(),"sender is authorized [",fromEmailAddress,"|",fromDomainName,"]")
        for part in mail.walk():
            if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                filename, encoding = decode_header(part.get_filename())[0]
            
                if(encoding is not None):
                    filename = filename.decode(encoding)
                print("filename",filename)
                fileextension = filename.split('.')
                fileextension.reverse()
                filename = str(abs(hash(filename))) + '.' + fileextension[0].lower()
                #filename = filename[0:60].replace(" ","") + filename[-4:]
                print("filename",filename)
                outputfilepath = outputdir + '/' + filename    


                if fileextension[0].lower() in allowedFileTypes:
                    # logic to send docx file to gotenberg for conversation to pdf before sending to printer
                    open(outputfilepath , 'wb').write(part.get_payload(decode=True))
                    if fileextension[0].lower() in gotenbergFileTypes and isinstance(GOTENBERGApi,str):
                        outputfilepath = convertdocx2pdf(outputfilepath)
                    print(datetime.datetime.now(),"Attempting to print",filename)
                    print(filename,part.get_content_maintype(),part.get('Content-Disposition'),fileextension[0])
                    print(datetime.datetime.now(),fileextension[0],"is an allowed filetype")
                    print(datetime.datetime.now(),"Printing",fileextension[0]," attachment from e-mail:",fromEmailAddress,", stored at:",outputfilepath,f",to printer IP: {printerIP}")
                    print("printActive",printActive)
                    if printActive == True:
                        ftp_to_printer(outputfilepath)
                    else:
                        print(datetime.datetime.now(),"This is where I would normally print",outputfilepath,", Currently: ACTIVE_PRINT!=True")
                    printLog["success"].append(f'File \"{filename}\" was downloaded and sent to the printer via FTP.')
                    #sendEmail(fromEmailAddress,f'your file \"{filename}\" has been processed for printing',f'File \"{filename}\" was downloaded and sent to the printer via FTP.')
                else:
                    printLog["fail"].append(f'File \"{filename}\" is not supported, and was not processed.')
                    #sendEmail(fromEmailAddress,f'your file \"{filename}\" is not supported',f'Files with extension type:{fileextension[0]} are not allowed to be processed.')
            #else:
            #    print(datetime.datetime.now(),filename,"is not an allowed filetype")
        filesProcessed = len(printLog['fail'] + printLog['success'])
        sendEmail(fromEmailAddress,f'Your print job - {filesProcessed} files received','\r\n'.join(printLog["success"]) + '\r\n\r\n' + '\r\n'.join(printLog["fail"]))

    else:
        print(datetime.datetime.now(),"sender is NOT authorized [",fromEmailAddress,"|",fromDomainName,"] : No further action will be taken.")
        sendEmail(fromEmailAddress,f'Your e-mail address {fromEmailAddress} is not authorized',f'The e-mail sender {fromEmailAddress} is not authorized to send e-mails to this address.')
# Download all the attachment files for all emails in the inbox.
def downloadAllAttachmentsInInbox(server:str=IMAPserver, user:str=IMAPuser, password:str=IMAPpassword, outputdir:str=outputdir):
    m = connect(server, user, password)
    resp, items = m.search(None, "UnSeen")
    print(f"{datetime.datetime.now()} Checking e-mail account",IMAPuser)
    print(datetime.datetime.now(),"ALLOWED_FILE_TYPES:",','.join(allowedFileTypes))
    print(datetime.datetime.now(),"ALLOWED_SENDERS:",','.join(allowedSenders))
    print(datetime.datetime.now(),"Printing Active?",printActive)
    items = items[0].split()
    print(datetime.datetime.now(),"Found",len(items),"e-mails")

    for emailid in items:
        m.store(emailid, '+FLAGS', '(\\Seen)')  ## Mark the e-mail as read so it won't be printed again
        downloaAttachmentsInEmail(m, emailid, outputdir)
    m.logout
while runTask == 1:
    printLog = {}
    printLog["fail"] = []
    printLog["success"] = []
    printLog["info"] = []
    downloadAllAttachmentsInInbox()
    print(f"{datetime.datetime.now()} Waiting {recheckEveryXSeconds} seconds")
    time.sleep(recheckEveryXSeconds)



