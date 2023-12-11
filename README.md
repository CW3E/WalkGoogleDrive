# WalkGoogleDrive
## Helper Script to scan a provided Google Drive and find all non-inherited permission.

### Steps to get running:
1. You will need to run this on a computer that has a web browser. You have to approve access to the Google API.
1. Follow the instructions on "Enable the API" and "Configure the OAuth consent screen" [here](https://developers.google.com/drive/api/quickstart/python). Once done download the JSON file and save it in this repository as 'credentials.json'
1. Install the Conda environment. `conda create -n walk_google_drive --file ./requirements.txt` should install everything but the file was created on a Mac, you will likely need to change it for linux. The necessary installs are:
    1. python => 3.11
    1. google-api-python-client
    1. google-auth-httplib2
    1. google-auth-oauthlib
1. Different ways to run the tools
    1. The original simple folder scanner (all folders in your drive) `python ./get_list_of_folders_in_drive.py <<GoogleDriveIDFromURL>>`
    2. The updated scanner all files and folders in your drive python `python ./get_list_of_folders_in_drive.v2.py <<GoogleDriveIDFromURL>> --search_files`
    3. Scoped to just a subfolder and all folders beneath it `python ./get_list_of_folders_in_drive.v2.py <<GoogleDriveIDFromURL>> --folder_id <<GoogleDriveFolderIDFromURL>>`
    4. Scoped to just a subfolder and all files and folders beneath it `python ./get_list_of_folders_in_drive.v2.py <<GoogleDriveIDFromURL>> --folder_id <<GoogleDriveFolderIDFromURL>> --search_files`
