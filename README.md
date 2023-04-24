# email2printerFTP
- This service connects to an IMAP e-mail server and looks for e-mail that are unread/unseen in the Inbox
- The sender address (domain and e-mail address) is checked against `ALLOWED_SENDERS`
- All attachments with file extensions in `ALLOWED_FILE_TYPES` will be downloaded, and e-mails will be marked as read/seen.
- If `ACTIVE_PRINT` is not set to `False` the service will upload the file to the `PRINTER_IP` FTP server, to print.

# Inspiration
I have an HP MFP 283fdw printer that allows you to use HPEPRINT to send e-mail to `<custom-adress>@hpeprint.com` to print files easily and remotely, however this requires my document to be uploaded to the HPE cloud. This service allows me to e-mail my self hosted e-mail server and have the HP printer pickup the job over the FTP protocol. 

NOTE: My HP printer had "FTP Printing" disabled by default, and I needed to turn this on via a tickbox in the the printers webUI(https) under Networking > Configuration > Advanced

# Environment Variables
| VARIABLE  | Description |
| ------------- | ------------- |
| PRINTER_IP | `(REQUIRED)`The IP address of the Printer's FTP server. NOTE: Anonymous FTP authentication is used. |
| IMAP_SERVER_IP | `(REQUIRED)`The IP or hostname of the IMAP server  |
| IMAP_USERNAME | `(REQUIRED)`The username the authentication with your IMAP server  |
| IMAP_PASSWORD | `(REQUIRED)`The password the authentication with your IMAP server  |
| ALLOWED_SENDERS | `(REQUIRED)` Space seperated e-mail addresses or domain names, `e.g. bgates@contoso.com gmail.com`  |
| SCHEDULE | `(OPTIONAL)` The time (in seconds) between checking the e-mail account `Default: 60`  |
| ALLOWED_FILE_TYPES | `(OPTIONAL)` Space seperated file extensions that will be sent to the printer `Default: pdf`  |
| ACTIVE_PRINT | `(OPTIONAL)` This can be set to 'False' for testing IMAP, i.e. the file WILL NOT BE sent to the printer `Default: True`  |

````
docker run -it -e PRINTER_IP='192.168.1.50' -e IMAP_SERVER_IP='192.0.2.1' -e IMAP_USERNAME='userpart@domain.com' -e IMAP_PASSWORD='yourIMAPpassword' -e SCHEDULE=90 -e ALLOWED_FILE_TYPES='docx pdf' smck83/email2printerftp
````
