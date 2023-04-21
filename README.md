# email2printerFTP
Download attachments from e-mail via IMAP and send them to a printer via FTP


# Environment Variables
| VARIABLE  | Description |
| ------------- | ------------- |
| IMAP_SERVER_IP | The IP or hostname of the IMAP server  |
| IMAP_USERNAME | The username the authentication with your IMAP server  |
| IMAP_PASSWORD | The password the authentication with your IMAP server  |
| SCHEDULE | The time (in seconds) between checking the e-mail account `Default: 60`  |
| ALLOWED_FILE_TYPES | Space seperated filed extensions that will be sent to the printer `Default: pdf docx xlsx doc xls`  |


````
docker run -it -e PRINTER_IP='192.168.1.50' -e IMAP_SERVER_IP='192.0.2.1' -e IMAP_USERNAME='userpart@domain.com' -e IMAP_PASSWORD='yourIMAPpassword' -e SCHEDULE=90 -e ALLOWED_FILE_TYPES='docx pdf' smck83/email2printerftp
````
