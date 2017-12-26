# backup-mongodb
Used to back up mongodb to Google Drive in an encrypted 7z file

#Introduction 
* pip3 install httplib2
* pip3 install --upgrade google-api-python-client 
* apt-get install 7zip-full

##Required:
line 30: DB Name
line 35: zip password
line 31/32: DB Username/Password

Enable Google Drive API:
Use this wizard [https://console.developers.google.com/start/api?id=drive] to create or select a project in the Google Developers Console and automatically turn on the API. Click Continue, then Go to credentials.
On the Add credentials to your project page, click the Cancel button.
At the top of the page, select the OAuth consent screen tab. Select an Email address, enter a Product name if not already set, and click the Save button.
Select the Credentials tab, click the Create credentials button and select OAuth client ID.
Select the application type Other, enter the name "mongo-backup", and click the Create button.
Click OK to dismiss the resulting dialog.
Click the file_download (Download JSON) button to the right of the client ID.
Move this file to your directory and rename it client_secret.json.

When you run the script for the first time it will give you a url to authorize the script to access your gdrive.

##Options:
line 28: Folder name in GDrive
