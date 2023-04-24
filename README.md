# email2printerFTP
- This service connects to an IMAP e-mail server and looks for e-mail that are unread/unseen in the Inbox
- All attachments will be downloaded, and e-mails will be marked as read/seen.
- If attachment file extensions are in the `ALLOWED_FILE_TYPES` list, the service will upload the file to the `PRINTER_IP` FTP server.

# Inspiration
I have a HP MFP 283fdw printer that allows you to use HPEPRINT to send e-mail to `<custom-adress>@hpeprint.com` which requires the document to be uploaded to the cloud. This service allows me to e-mail my self hosted e-mail server and have the HP printer pickup the job. 

NOTE: By default, my HP printer had "FTP Printing" disabled by default, and I needed to turn this on via a tickbox in the the printers webUI(https) under Networking > Configuration > Advanced

# Environment Variables
| VARIABLE  | Description |
| ------------- | ------------- |
| PRINTER_IP | `(REQUIRED)`The IP address of the Printer's FTP server. Anonymous FTP authentication is used.  |
| IMAP_SERVER_IP | `(REQUIRED)`The IP or hostname of the IMAP server  |
| IMAP_USERNAME | `(REQUIRED)`The username the authentication with your IMAP server  |
| IMAP_PASSWORD | `(REQUIRED)`The password the authentication with your IMAP server  |
| ALLOWED_SENDERS | `(REQUIRED)` Space seperated e-mail addresses or domain names, `e.g. bgates@contoso.com gmail.com`  |
| SCHEDULE | `(OPTIONAL)` The time (in seconds) between checking the e-mail account `Default: 60`  |
| ALLOWED_FILE_TYPES | `(OPTIONAL)` Space seperated file extensions that will be sent to the printer `Default: pdf`  |

````
docker run -it -e PRINTER_IP='192.168.1.50' -e IMAP_SERVER_IP='192.0.2.1' -e IMAP_USERNAME='userpart@domain.com' -e IMAP_PASSWORD='yourIMAPpassword' -e SCHEDULE=90 -e ALLOWED_FILE_TYPES='docx pdf' smck83/email2printerftp
````
