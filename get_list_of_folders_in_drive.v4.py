#!/home/pmulrooney/google_drive_user_scan/conda-env-linux/bin/python -u
from __future__ import print_function

import os.path
import sys
import argparse
import re
import traceback
import time

from datetime import datetime

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

    folders = [ [args.drive_id, '__DriveRoot__', 'https://drive.google.com/drive/u/0/folders', []] ]
    _query="mimeType=\"application/vnd.google-apps.folder\""

    if args.folder_id is not None:
        folders = [ [args.folder_id, '__TopFolder__', 'https://drive.google.com/drive/u/0/folders', []] ]
        _query = "mimeType=\"application/vnd.google-apps.folder\" and \"%s\" in parents"%(args.folder_id)

    # Top level folder
    print('Get all Folders:')

    nextPageToken=None

    ## Get all the folders in this drive / top folder...
    index = 0
    count = 0
    while index < len(folders):
        try:
           print(f'Scanning folder: {index:04d}                                                        ', end='\r')
           if _query == "":
               _query = "mimeType=\"application/vnd.google-apps.folder\" and \"%s\" in parents"%(folders[index][0])

           results = service.files().list(
               q=_query, corpora="drive",
               includeItemsFromAllDrives=True, includeTeamDriveItems=True, supportsAllDrives=True, orderBy='name', 
               supportsTeamDrives=True, driveId=args.drive_id, pageToken=nextPageToken,
               pageSize=1000, fields="nextPageToken, files(id, name)").execute()

           items = results.get('files', [])
           for item in items:
               if not any(folder[0] == item['id'] for folder in folders):
                   folders.append([item['id'], item['name'], 'https://drive.google.com/drive/u/0/folders', []])

           nextPageToken = results.get('nextPageToken', '')

           if nextPageToken == '':
               _query=""
               index += 1
           count = 0
        except Exception as e:
           DT = datetime.now()
           print(f'================== Exception during folder scan, sleeping for 1 minute then trying again ({DT})', end='\r')
           print(f"An error occurred: {e}")
           traceback.print_exc()
           time.sleep(60)
           count+=1
           if count > 2:
                print("Failed more than 3 times, stop trying...")
                break

    print("")
    print("")

    files = []
    if args.search_files == True:
        print("Get all files:")
       
        count = 0
        FCount=len(folders)
        for _index, _folder in enumerate(folders):
            print(f'Getting files in _folder: {_index:04d} of {FCount:04d} ({_folder[0]})                                         ', end='\r')
            _query = "mimeType!=\"application/vnd.google-apps.folder\" and mimeType!=\"application/vnd.google-apps.shortcut\" and \"%s\" in parents"%(_folder[0])
            nextFilePageToken=None
        
            while nextFilePageToken != '':
                try:
                    results = service.files().list(
                                    q=_query, corpora="drive",
                                    includeItemsFromAllDrives=True, includeTeamDriveItems=True, supportsAllDrives=True,
                                    supportsTeamDrives=True, driveId=args.drive_id, pageToken=nextFilePageToken,
                                    pageSize=1000, fields="nextPageToken, files(id, name)").execute()
                    file_items = results.get('files', [])
                    files += [ [file_item['id'], file_item['name'], 'https://drive.google.com/file/d', []] for file_item in file_items ]

                    nextFilePageToken = results.get('nextPageToken', '')
                    count = 0
                except Exception as e:
                    DT = datetime.now()
                    print(f'================== Exception during folder scan, sleeping for 1 minute then trying again ({DT})', end='\r')
                    #print(f"An error occurred: {e}")
                    #traceback.print_exc()
                    time.sleep(60)
                    count+=1
                    if count > 2:
                        print("Failed more than 3 times, stop trying...")
                        break


    print("")
    print("")
    print("Get all permissions:")
    FFCount=len(folders)+len(files)

    Checked_indexes = []

    for _index, _folder in enumerate(folders + files):
        print(f'Getting files in folder: {_index:04d} of {FFCount:04d} ({_folder[0]})                                   ', end='\r')
        nextPageToken=None
        
        if _folder[0] in Checked_indexes:
            continue

        Checked_indexes.append(_folder[0])

        while nextPageToken != '':
           try:
               results = service.permissions().list(fileId=_folder[0],
                       pageSize=100, supportsAllDrives=True, supportsTeamDrives=True, pageToken=nextPageToken,
                       fields="nextPageToken, permissions(emailAddress,permissionDetails(inherited),type)").execute()
               items = results.get('permissions', [])
               nextPageToken = results.get('nextPageToken', '')

               if items:
                   _folder[3] += [ x['emailAddress'] for x in items if x['permissionDetails'][0]['inherited'] == False and x['type'] != 'anyone' and x['type'] != 'domain' ]
                   _folder[3] += [ 'Link' for x in items if x['permissionDetails'][0]['inherited'] == False and ( x['type'] == 'anyone' or x['type'] == 'domain') ]

               count = 0

           except Exception as e:
               DT = datetime.now()
               if "File not found" in str(e):
                   continue
               print("")
               print("================== Exception during permissions scan, sleeping for 1 minute then trying again ({DT})")
               print(f"An error occurred: {e}")
               traceback.print_exc()
               time.sleep(60)
               count+=1
               if count > 2:
                   print("Failed more than 3 times, stop trying...")
                   break


        if len(_folder[3]) > 0:
            print("")
            print("%s - %s/%s?sharingaction=manageaccess :"%(_folder[1], _folder[2], _folder[0] ))
            for _val in _folder[3]:
                print("  -- %s"%(_val))

    print("")
    print("")
    print("****** That's all folks *******")
    exit(0)


if __name__ == '__main__':









    args = parse_args()
    main(args)
