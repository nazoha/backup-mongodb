#!/usr/bin/env python3
from __future__ import print_function
from os.path import join
from bson.json_util import dumps
import pymongo
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
import tarfile


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = str(os.path.abspath(os.path.dirname(__file__))) + '/client_secret.json'
APPLICATION_NAME = 'mongo-backup'
JSON_DIR = str(os.path.abspath(os.path.dirname(__file__)))+'/data'
FOLDER = 'mongodb_backup'
FILE_MIMYTYPE = 'application/json'
DB_NAME = 'test'  # input databasename crowi's
EXTENSION = '.json'
BACKUP_EXTENSION = '.tar.gz'

def mongodb_backup(backup_db_dir):
    client = pymongo.MongoClient(host="130.211.153.118", port=27017)
    database = client[DB_NAME]
    # Please write username and password of mongodb if mongodb requires authentication.
    # authenticated = database.authenticate("username","passwd")
    # assert authenticated, "Could not authenticate to database!"
    collections = database.collection_names()
    for i, collection_name in enumerate(collections):
        col = getattr(database, collections[i])
        collection = col.find()
        jsonpath = collection_name + EXTENSION
        jsonpath = join(backup_db_dir, jsonpath)
        with open(jsonpath, 'w') as jsonfile:
            jsonfile.write(dumps(collection))
    tar = tarfile.open(os.path.join(backup_db_dir, 'daxiv_'+date.today().isoformat()+BACKUP_EXTENSION), 'w:gz')
    tar.add(backup_db_dir)
    tar.close()

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
    print("Create folder: %s" % (FOLDER))
    folder_metadata = {
        'name': FOLDER,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    print("File ID: %s" % folder.get('id'))
    return folder.get('id')

def get_folder(service):
    response = service.files().list(q="name="+"'"+FOLDER+"'", spaces='drive').execute()
    if not response:
        return False
    folder = response.get('files', [])[0]
    return folder.get('id')



def upload_file(service, file_name, folder_id):
    media_body = MediaFileUpload(file_name, mimetype=FILE_MIMYTYPE, resumable=True)
    body = {
        'name': os.path.split(file_name)[-1],
        'mimeType': FILE_MIMYTYPE,
        'parents': [folder_id],
    }
    service.files().create(body=body, media_body=media_body).execute()

def main():
    #mongodb_backup(JSON_DIR)
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    file_path = os.path.join(JSON_DIR, '*' + BACKUP_EXTENSION)
    files = glob.glob(file_path)
    if not files:
        print("No files to upload.")
        sys.exit()
    folder_id = get_folder(service)
    if not folder_id:
        folder_id = create_folder(service)
    for file_name in files:
        if os.path.split(file_name)[-1] == 'client_secret.json':
            continue
        print('upload: ' + file_name)
        upload_file(service, file_name, folder_id)
        os.remove(file_name)

if __name__ == "__main__":
    main()
