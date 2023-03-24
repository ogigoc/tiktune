from __future__ import print_function

import io
import glob

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/drive']
# SCOPES = []
SERVICE_ACCOUNT_FILE = 'service_account.json'

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)


def download_file(real_file_id):
    """Downloads a file
    Args:
        real_file_id: ID of the file to download
    Returns : IO object with location.

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    # creds, _ = google.auth.default()

    try:
        # create drive api client

        file_id = real_file_id

        # pylint: disable=maybe-no-member
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print(F'Download {int(status.progress() * 100)}.')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return file.getvalue()

def get_all_files(gdrive_dir):
    files = []
    page_token = None
    while True:
        # pylint: disable=maybe-no-member
        response = service.files().list(q=f"'{gdrive_dir}' in parents",
                                        spaces='drive',
                                        fields='nextPageToken, '
                                        'files(id, name)',
                                        pageToken=None).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    return files


def sync(local_dir, gdrive_dir):
    print('Syncing drive...')
    drive_files = get_all_files(gdrive_dir)
    for file in drive_files:
        file['name'] = local_dir + file['name']


    local_files = set(glob.glob(local_dir + '*'))

    new_files = [
        file for file in drive_files
        if file['name'] not in local_files
    ]

    for file in new_files:
        with open(file['name'], 'wb') as output:
            print(f"Downloading {file['name']}")
            output.write(download_file(file['id']))

if __name__ == '__main__':
    sync()

    # file = download_file(real_file_id='1OePlCw-xFIEHPP3CLq0jknNzTYLp1UGe')
    # print(file)
    # with open("test.mp4", 'wb') as test_file:
    #     test_file.write(file.getvalue())