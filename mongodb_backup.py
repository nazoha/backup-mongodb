#!/usr/bin/env python3
from __future__ import print_function
from os.path import join
import httplib2
import os
import sys
from googleapiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client import file
from googleapiclient.http import MediaFileUpload
from datetime import date
import glob
import shutil


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = str(os.path.abspath(os.path.dirname(__file__))) + '/client_secret.json'
APPLICATION_NAME = 'mongo-backup'
JSON_DIR = str(os.path.abspath(os.path.dirname(__file__)))+'/mongobackuptmp'
FOLDER = 'mongodb_backup'
FILE_MIMETYPE = 'application/tar'
DB_NAME = 'DB NAME' 
DB_USER = 'DB USERNAME'
DB_PASS = 'DB PASSWORD'
EXTENSION = '.json'
BACKUP_EXTENSION = '.zip'
BACKUP_PASSWORD = 'somepassword'

def mongodb_backup(backup_db_dir):
	command = "mongodump -u "+DB_USER+" -p "+DB_PASS+" --db "+DB_NAME+" --out "+backup_db_dir
    
	print("Executing command: " + command)
    callreturn = os.system(command);
    if (callreturn == 0):
        print('Backup successful')
    else:
        print('Something went wrong, mongodump returned: ' + callreturn)

    command = "7z a -t7z -m0=lzma2 -mx=9 -ms=on -mhe=on -p" + BACKUP_PASSWORD + ' \"' + os.path.join(backup_db_dir, 'NSdb_'+date.today().isoformat()+BACKUP_EXTENSION) + "\" " + backup_db_dir 

    print("Executing command: " + command)
    callreturn = os.system(command);
    if (callreturn == 0):
        print('Backup successful')
    else:
        print('Something went wrong, 7zip returned: ' + callreturn)


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'drive-python-mongo-backup.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def create_folder(service):
    print("Creating folder: %s" % (FOLDER))
    folder_metadata = {
        'name': FOLDER,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder.get('id')

def get_folder(service):
    response = service.files().list(q="mimeType='application/vnd.google-apps.folder' and name="+"'"+FOLDER+"'", spaces='drive', fields='files(id)').execute()
    if not response.get('files',[]):
        return False
    folder = response.get('files', [])[0]
    return folder.get('id')

def upload_file(service, file_name, folder_id):
    media_body = MediaFileUpload(file_name, mimetype=FILE_MIMETYPE, resumable=True)
    body = {
        'name': os.path.split(file_name)[-1],
        'mimeType': FILE_MIMETYPE,
        'parents': [folder_id],
    }
    service.files().create(body=body, media_body=media_body).execute()

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    folder_id = get_folder(service)
    if not folder_id:
        folder_id = create_folder(service)

    mongodb_backup(JSON_DIR)
    file_path = os.path.join(JSON_DIR, '*' + BACKUP_EXTENSION)
    files = glob.glob(file_path)
    if not files:
        print("No files to upload.")
        sys.exit()

    for file_name in files:
        if os.path.split(file_name)[-1] == 'client_secret.json':
            continue
        print('upload: ' + file_name)
        upload_file(service, file_name, folder_id)

    shutil.rmtree(JSON_DIR)

if __name__ == "__main__":
    main()
