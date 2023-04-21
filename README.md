# email2printerFTP
Download attachments from e-mail via IMAP and send them to a printer via FTP


````
docker run -it -e PRINTER_IP='192.168.1.50' -e IMAP_SERVER_IP='192.0.2.1' -e IMAP_USERNAME='userpart@domain.com' -e IMAP_PASSWORD='yourIMAPpassword' -e SCHEDULE=10 -e ALLOWED_FILE_TYPES='docx pdf' smck83/email2printerftp
````
