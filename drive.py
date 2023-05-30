from __future__ import print_function

import io
import glob

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
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


def upload_to_dir(gdrive_dir_name, video_path, video_name):
    """Uploads a video file to a directory in Google Drive
    Args:
        gdrive_dir_name: Name of the directory to upload the file to
        video_path: Path to the video file to upload
        video_name: Name of the video file once uploaded
    """
    # Query to get the folder id from the folder name
    response = service.files().list(
        q=f"name='{gdrive_dir_name}' and mimeType='application/vnd.google-apps.folder' and '1-W30kZ2CD99B28PNjY3_u3CCKQXl1ql7' in parents",
        spaces='drive',
        fields='files(id)').execute()
    print(response)
    print(response.get('files', []))
    gdrive_dir_id = response.get('files', [])[0].get('id')

    file_metadata = {
        'name': video_name,
        'parents': [gdrive_dir_id]
    }
    media = MediaFileUpload(video_path, 
                            mimetype='video/mp4',
                            resumable=True)
    request = service.files().create(body=file_metadata,
                                     media_body=media,
                                     fields='id')
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print("Uploaded {0}".format(int(status.progress() * 100)))
    
    print("Upload Complete.")
    return response.get('id')

    
if __name__ == '__main__':
    upload_to_dir('test', 'tmp/videos/a91.mp4', 'test #test @vasa_uno .mp4')
    # sync()

    # file = download_file(real_file_id='1OePlCw-xFIEHPP3CLq0jknNzTYLp1UGe')
    # print(file)
    # with open("test.mp4", 'wb') as test_file:
    #     test_file.write(file.getvalue())