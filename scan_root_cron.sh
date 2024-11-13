#!/bin/bash

DDATE="$(date '+%Y.%m.%d')"

mkdir /home/pmulrooney/google_drive_user_scan/_output/${DDATE}

/home/pmulrooney/google_drive_user_scan/get_list_of_folders_in_drive.v3.py  --search_files  >> /home/pmulrooney/google_drive_user_scan/_output/${DDATE}/${DDATE}_root_with_files.txt 2>&1
