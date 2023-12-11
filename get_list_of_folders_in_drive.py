#!/Users/pmulrooney/Desktop/Garbage/google_drive_user_scan/conda-env/bin/python -u
from __future__ import print_function

import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


def main(driveId, folderid):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    items = [0]

    nextPageToken=''

    folderIds = {driveId: ['__DriveRoot__',[]]}
    print('Folders:')
    while True:
        # Call the Drive v3 API
        results = service.files().list(
            q='mimeType="application/vnd.google-apps.folder"', corpora="drive",
            includeItemsFromAllDrives=True, includeTeamDriveItems=True, supportsAllDrives=True,
            supportsTeamDrives=True, driveId=driveId, pageToken=nextPageToken,
            pageSize=100, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        nextPageToken = results.get('nextPageToken', [])

        if not items:
            print('No folders found.')
            break

        print("Found %s folders"%(len(items)))
        for item in items:
            folderIds[item['id']] = [item['name'],[]]
            
        if not nextPageToken:
            print('No next page. Done collecting folders')
            break

    try:
        service = build('drive', 'v3', credentials=creds)

        for _key, _value in folderIds.items():
            # Call the Drive v3 API
            results = service.permissions().list(fileId=_key,
                pageSize=100, supportsAllDrives=True, supportsTeamDrives=True,
                fields="nextPageToken, permissions(emailAddress,permissionDetails(inherited),type)").execute()
            items = results.get('permissions', [])
            nextPageToken = results.get('nextPageToken', [])

            # 'permissionDetails': [{'inherited': True}]
            if items:
                _value[1] += [ x['emailAddress'] for x in items if x['permissionDetails'][0]['inherited'] == False and x['type'] != 'anyone' and x['type'] != 'domain' ]

            while nextPageToken:
                results = service.permissions().list(fileId=_key,
                    pageSize=100, supportsAllDrives=True, supportsTeamDrives=True,
                    pageToken=nextPageToken, fields="nextPageToken, permissions(emailAddress,permissionDetails(inherited),type)").execute()
                items = results.get('permissions', [])
                nextPageToken = results.get('nextPageToken', [])
            
                if items:
                    _value[1] += [ x['emailAddress'] for x in items if x['permissionDetails'][0]['inherited'] == False and x['type'] != 'anyone' ]

            if len(_value[1]) > 0:
                print("%s - https://drive.google.com/drive/u/0/folders/%s :"%(_value[0], _key))
                for _val in _value[1]:
                    print("  -- %s"%(_val))

    except: 
        print("")
        print("================== FAILED ON:")
        print(_key)
        print(_value[0])
        print(items)
   

if __name__ == '__main__':
    folder=sys.argv[2]
    main(sys.argv[1], folder)
