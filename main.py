import yaml
import glob
import json
from datetime import datetime
import random
import time
import traceback

import pandas as pd

import drive
import tiktok_uploader
import telegram
from uploader import android
from uploader import utils

import logging
log = logging.getLogger(__name__)

ACCOUNTS_DB = 'accounts_db.json'
VIDEOS_DB = 'videos_db.json'
UPLOAD_RETRY = 3

def do_campaign(campaign, active_accounts, videos, device, interactive=False):
    log.info(f"Executing campaign {campaign['name']} with {device['videos_per_campaign'][campaign['name']]} videos")

    # Sync drive videos
    if campaign['gdrive_dir']:
        drive.sync(local_dir=campaign['local_dir'], gdrive_dir=campaign['gdrive_dir'])

    local_files = sorted(list(glob.glob(campaign['local_dir'] + '*')))
    uploaded_files = [
        file.split('/')[-1]
        for file in videos.file.values
    ]
    new_files = [
        file 
        for file in local_files
        if file.split('/')[-1] not in uploaded_files
    ]

    random.shuffle(new_files)
    log.info(f"Unuploaded videos: {len(new_files)}")
    if len(new_files) <= len(active_accounts):
        telegram.send_message(f"No new files for campaign {campaign['name']}")

    log.info('Posting videos...')
    errors = []
    uploaded = 0

    for video_file, account in zip(new_files, active_accounts.itertuples(index=False)):
        title = random.choice(campaign['titles'])

        tiktok_id = ''
        tiktok_url = ''
        drive_id = ''
        overlay_text = ''
        successful_upload = False
        if device['name'] == 'desk':
            for retry in range(UPLOAD_RETRY):
                try:
                    log.info(f"Trying to upload video, retry: {retry} account: {account.username} video: {video_file}")

                    tiktok_id = str(tiktok_uploader.uploadVideo(
                        session_id=account.session_id,
                        video=video_file,
                        title=title,
                        tags=campaign['tags'],
                        verbose=True
                    ))

                    if tiktok_id == False:
                        log.warn(f"Failed!")
                        raise Exception("Upload Failed")

                    successful_upload = True
                    break
                except Exception as e:
                    if retry == UPLOAD_RETRY - 1:
                        log.error(f"Upload failed with account {account.username} for video {video_file}")
                        log.error(str(e))
                        traceback.print_exc()
                        errors.append(str(e))
                        # maybe send tiktok
                        # raise e
                    else:
                        log.warning(f"Upload failed, retrying, error: {e}")
                        time.sleep(61)
        elif device['name'] == 'repurpose':
            log.info(f"Trying to upload video on {device['name']}, account: {account.username},{account.name} video: {video_file}")
            try:
                drive_id = drive.upload_to_dir(
                    gdrive_dir_name=account.username,
                    video_path=video_file,
                    video_name=title + ' #' + ' #'.join(campaign['tags']) + '.mp4',
                )
                successful_upload = True
            except Exception as e:
                log.error(f"Upload failed with account {account.username} for video {video_file}")
                log.exception(f"{e}")
                errors.append(str(e))
        else:
            log.info(f"Trying to upload video on {device['name']}, account: {account.username},{account.name} video: {video_file}")
            try:
                android_device = android.MODELS[device['model']](
                    device['name'],
                    device['device_id'],
                    utils.read_accounts_for_device(device['name']).itertuples(index=False),
                    interactive=interactive,
                )

                if 'overlay_text' in campaign and random.random() < 0.5:
                    overlay_text = random.choice(campaign['overlay_text'])

                android_device.upload_video(
                    account=account,
                    video=video_file,
                    title=title,
                    tags=campaign['tags'],
                    sound_url=campaign['sound_url'],
                    sound_name=campaign['sound_name'],
                    overlay_text=overlay_text,
                )
                successful_upload =  True
                # tiktok_url = android.get_link(d)
                android_device.lock()
            except Exception as e:
                log.error(f"Upload failed with account {account.username} for video {video_file}")
                log.error(f"{e}")
                traceback.print_exc()
                errors.append(str(e))
                try:
                    log.info("Trying to lock device...")
                    android_device.connect()
                    android_device.log_state()
                    android_device.lock()
                except Exception as e:
                    error_message = f"Error while locking device: {str(e)}"
                    log.error(error_message)
                    log.exception(error_message)

        if successful_upload:
            with open(VIDEOS_DB, 'a') as videos_db:
                videos_db.write(json.dumps({
                    "file": video_file,
                    "account_id": account.id,
                    "tiktok_id": tiktok_id,
                    "title": title,
                    "time": str(datetime.now()),
                    "device": device['name'],
                    "tiktok_url": tiktok_url,
                    "drive_id": drive_id,
                    "overlay_text": overlay_text,
                }) + '\n')
            uploaded += 1

            log.info(f'Uploaded video {video_file} with account {account.id} {account.username} tiktok_id {tiktok_id}')
        
        wait_min = 1
        if device['name'] == 'desk':
            wait_min = 3
        log.info(f"Waiting 1-{wait_min + 1} minutes")
        # time.sleep(5 + random.randint(1, 6))
        time.sleep(20 + random.randint(1, int(wait_min * 60)))

    unpuloaded = len(new_files) - uploaded
    return uploaded, unpuloaded, errors


def main():
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--device", help="Device Name", required=True)
        parser.add_argument("-s", "--silent", action=argparse.BooleanOptionalAction, help="Do not send telegram messages", default=False)
        parser.add_argument("-i", "--interactive", action=argparse.BooleanOptionalAction, help="Start a repl on error", default=False)
        
        args = parser.parse_args()

        # Send message at start.
        # if not args.silent:
        #     telegram.send_message(f"Starting campaign uploads for device {args.device}...")

        log.info("\n")
        log.info('Starting job...')
        # Load data
        log.info("Reading campaigns...")
        with open('campaigns.yaml', 'r') as file:
            campaigns = yaml.safe_load(file)
        log.info("Reading devices...")
        with open('devices.yaml', 'r') as file:
            devices = yaml.safe_load(file)
        log.info('Reading accounts...')
        accounts = pd.read_json(ACCOUNTS_DB, lines=True)
        log.info('Reading video...')
        videos = pd.read_json(VIDEOS_DB, lines=True)

        if args.device not in devices:
            raise Exception(f"Unknown device {args.device}")

        device = devices[args.device]

        active_accounts = accounts[accounts.active & (accounts.device == args.device)].sample(frac=1)

        videos_per_batch = sum(vids for vids in device['videos_per_campaign'].values())
        if videos_per_batch != len(active_accounts):
            log.info(f"Device videos {videos_per_batch}, active accounts {len(active_accounts)}")
            raise Exception(f"Number of accounts {len(active_accounts)} does not match number of videos {videos_per_batch}")
        
        message_report = dict()
        for campaign_name, video_count in device['videos_per_campaign'].items():
            message_report[campaign_name] = do_campaign(campaigns[campaign_name], active_accounts.head(video_count), videos, device, interactive=args.interactive)
            if video_count != 0:
                active_accounts = active_accounts.tail(-video_count)

        # Send message the the end.
        message = ''
        # message = '\n'.join([f"{key}: videos:\t{val[0]} errors: {len(val[2])} left:\t{val[1]}" for key,val in message_report.items()])
        if any(val[2] for val in message_report.values()):
            message += '\n\nERRORS:\n'
            message += '\n'.join([f"{key}: {val[2]}" for key, val in message_report.items()])
        
        uploaded = sum(val[0] for val in message_report.values())
        errors = sum(len(val[2]) for val in message_report.values())

        if not args.silent:
            telegram.send_message(f"UPLOADS {args.device} SUCCESSFUL: {uploaded} ERRORS: {errors}" + message)
        if not args.silent and args.device == 'redminote':
            campaign_files_left = '\n'.join([f"{key}: {val[1]}" for key, val in message_report.items()])
            telegram.send_message(f"Campaign Files Left:\n" + campaign_files_left)
    except Exception as e:
        log.exception(f"General error: {str(e)}")
        if not args.silent:
            telegram.send_message(f"UPLOADS ERROR {args.device} ERROR: {str(e)}")
        raise e


if __name__ == '__main__':
    main()
