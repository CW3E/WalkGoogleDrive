#!/Users/pmulrooney/Desktop/Garbage/google_drive_user_scan/conda-env/bin/python -u
from __future__ import print_function

import os.path
import sys
import argparse
import re
import traceback
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def validate_drive_id(value):
    if not re.match(r'^[a-zA-Z0-9]{19}$', value):
        raise argparse.ArgumentTypeError(f"{value} is not a valid drive ID")
    return value

def parse_args():
    parser = argparse.ArgumentParser(description='Process some arguments.')
    
    parser.add_argument('drive_id', nargs='?', type=validate_drive_id, help='Drive ID (alphanumeric, 20 characters)', default="0AOrqHsfJvRW9Uk9PVA")
    parser.add_argument('--folder_id', type=str, help='Optional Folder ID')
    parser.add_argument('--search_files', action='store_true', help='Search files (default is to search folders)')

    args = parser.parse_args()

    print('------------------------------- Arguments')
    print(f'Drive ID: {args.drive_id}')
    if args.folder_id:
        print(f'Folder ID: {args.folder_id}')
    print(f'Search Files: {args.search_files}')
    print('-------------------------------')
    print('')
    return args

def main(args):
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

    folderIds = {args.drive_id: ['__DriveRoot__',"https://drive.google.com/drive/u/0/folders",[]]}
    print('Folders:')
    if args.folder_id is not None:
        parents=[args.folder_id]
        folderIds = {args.folder_id: ['__TopFolder__',"https://drive.google.com/drive/u/0/folders",[]]}
        while parents:
            count=0
            try:
                _query = "mimeType=\"application/vnd.google-apps.folder\" and \"%s\" in parents"%(parents.pop())
                nextPageToken=''
                while True:
                    results = service.files().list(
                        q=_query, corpora="drive",
                        includeItemsFromAllDrives=True, includeTeamDriveItems=True, supportsAllDrives=True,
                        supportsTeamDrives=True, driveId=args.drive_id, pageToken=nextPageToken,
                        pageSize=100, fields="nextPageToken, files(id, name)").execute()
                    items = results.get('files', [])
                    nextPageToken = results.get('nextPageToken', [])

                    if not items:
                        break

                    for item in items:
                        parents.append(item['id'])
                        folderIds[item['id']] = [item['name'],"https://drive.google.com/drive/u/0/folders",[]]
                        if args.search_files == True:
                            _query = "mimeType!=\"application/vnd.google-apps.folder\" and \"%s\" in parents"%(item['id'])
                            nextFilePageToken=''
                            while True:
                                results = service.files().list(
                                    q=_query, corpora="drive",
                                    includeItemsFromAllDrives=True, includeTeamDriveItems=True, supportsAllDrives=True,
                                    supportsTeamDrives=True, driveId=args.drive_id, pageToken=nextFilePageToken,
                                    pageSize=100, fields="nextPageToken, files(id, name)").execute()
                                file_items = results.get('files', [])
                                nextFilePageToken = results.get('nextPageToken', [])

                                if not file_items:
                                    break

                                for file_item in file_items:
                                    folderIds[file_item['id']] = [file_item['name'],"https://drive.google.com/file/d",[]]

                                if not nextFilePageToken:
                                    break

                        
                    if not nextPageToken:
                        break
            except Exception as e:
                print("================== Exception during folder scan, sleeping for 1 minute then trying again")
                time.sleep(60)
                count+=1
                if count > 2:
                    print("Failed more than 3 times, stop trying...")
                    break
                continue
            break

    else:
        while True:
            results = service.files().list(
                q="mimeType=\"application/vnd.google-apps.folder\"", corpora="drive",
                includeItemsFromAllDrives=True, includeTeamDriveItems=True, supportsAllDrives=True,
                supportsTeamDrives=True, driveId=args.drive_id, pageToken=nextPageToken,
                pageSize=100, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            nextPageToken = results.get('nextPageToken', [])

            if not items:
                print('No folders found.')
                break

            print("Found %s folders"%(len(items)))
            for item in items:
                count=0
                while True:
                    try:
                        folderIds[item['id']] = [item['name'],"https://drive.google.com/drive/u/0/folders",[]]
                        if args.search_files == True:
                            _query = "mimeType!=\"application/vnd.google-apps.folder\" and \"%s\" in parents"%(item['id'])
                            nextFilePageToken=''
                            while True:
                                results = service.files().list(
                                    q=_query, corpora="drive",
                                    includeItemsFromAllDrives=True, includeTeamDriveItems=True, supportsAllDrives=True,
                                    supportsTeamDrives=True, driveId=args.drive_id, pageToken=nextFilePageToken,
                                    pageSize=100, fields="nextPageToken, files(id, name)").execute()
                                file_items = results.get('files', [])
                                nextFilePageToken = results.get('nextPageToken', [])

                                if not file_items:
                                    break

                                for file_item in file_items:
                                    folderIds[file_item['id']] = [file_item['name'],"https://drive.google.com/file/d",[]]

                                if not nextFilePageToken:
                                    break
                    except:
                        count+=1
                        print("Something failed, sleeping for a minute*%s and retry..."%(count))
                        time.sleep(60*count)
                        continue
                    break                
                
            if not nextPageToken:
                break

    service = build('drive', 'v3', credentials=creds)

    for _key, _value in folderIds.items():
        count=0
        while True:
            # Call the Drive v3 API
            try:
                results = service.permissions().list(fileId=_key,
                    pageSize=100, supportsAllDrives=True, supportsTeamDrives=True,
                    fields="nextPageToken, permissions(emailAddress,permissionDetails(inherited),type)").execute()
                items = results.get('permissions', [])
                nextPageToken = results.get('nextPageToken', [])

                # 'permissionDetails': [{'inherited': True}]
                if items:
                    _value[2] += [ x['emailAddress'] for x in items if x['permissionDetails'][0]['inherited'] == False and x['type'] != 'anyone' and x['type'] != 'domain' ]

                while nextPageToken:
                    results = service.permissions().list(fileId=_key,
                        pageSize=100, supportsAllDrives=True, supportsTeamDrives=True,
                        pageToken=nextPageToken, fields="nextPageToken, permissions(emailAddress,permissionDetails(inherited),type)").execute()
                    items = results.get('permissions', [])
                    nextPageToken = results.get('nextPageToken', [])
                
                    if items:
                        _value[2] += [ x['emailAddress'] for x in items if x['permissionDetails'][0]['inherited'] == False and x['type'] != 'anyone' ]

                if len(_value[2]) > 0:
                    print("%s - %s/%s?sharingaction=manageaccess :"%(_value[0], _value[1], _key))
                    for _val in _value[2]:
                        print("  -- %s"%(_val))

            except Exception as e:
                print("================== Exception:")
                #print("")
                #print(f"An exception occurred: {type(e).__name__}: {e}") 
                #print("")
                #traceback.print_exc()
                #print("")
                print("================== FAILED ON:")
                print(_key)
                print(_value[0])
                #print(items)
                print("================== Sleeping for 5 minutes, then trying again")
                time.sleep(300)
                count+=1
                if count > 2:
                    print("Failed more than 3 times, stop trying...")
                    break
                continue
            break
   

if __name__ == '__main__':

    args = parse_args()
    main(args)
