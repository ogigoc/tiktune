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

CAMPAIGNS_GROUPS = {
    # 'standard': {
        # 'pazljivo': {
            # 'name': 'pazljivo',
            # 'titles': ['SPOT NAPOKON IZASAO!!! VASA - PAZLJIVO'],
            # 'tags': ['vasa', 'pazljivo', 'vasa_uno', 'fyp'],
            # 'gdrive_dir': '1fOjznRlLYGPKPjashVJ9p36LvDV3SvGp',
            # 'local_dir': 'drive_videos/TikTok/pazljivo/',
            # 'videos_per_batch': 7,
        # },
        # 'mina10': {
            # 'name': 'mina10',
            # 'titles': ['"10 je ali" pesma je napokon izasla'],
            # 'tags': ['minaheart', '10jeali', '10jeali2', 'fyp'],
            # 'gdrive_dir': '1tt12PVSZFLoHuUtBxiC6QPm3919dDKVc',
            # 'local_dir': 'drive_videos/TikTok/mina10/',
            # 'videos_per_batch': 6,
        # },
    #},
    # 'yugo': {
    #     # 'yugofreestyle2': {
    #     #     'name': 'yugofreestyle2',
    #     #     'titles': [
    #     #         'Ja sam se zaljubila u ovu pesmu <3 Gabriel - Yugofreestyle @gabr1el_35',
    #     #         'Nova pesma uskoro izlazi Gabriel - Yugofreestyle Zapratite ga svi na @gabr1el_35',
    #     #         'Obozavam ovu pesmu!! Gabriel - Yugofreestyle @gabr1el_35',
    #     #         'Jeste culi za ovo? Gabriel - Yugofreestyle @gabr1el_35',
    #     #         'Jedva cekam da izadje Gabriel - Yugofreestyle @gabr1el_35',
    #     #         'Nisam cula za ovog lika ranije al ovo kida Gabriel - Yugofreestyle @gabr1el_35',
    #     #     ],
    #     #     'tags': ['yugo', 'yugofreestyle', 'yugofreestyle2', 'fyp'],
    #     #     'gdrive_dir': '1v2ygpUcAveJoA7wxfDdkKUJ01aDcv74q',
    #     #     'local_dir': 'drive_videos/TikTok/yugofreestyle2/',
    #     #     'videos_per_batch': 13,
    #     # },
    #     'yugofreestyle2': {
    #         'name': 'yugofreestyle2',
    #         'titles': [
    #             'Ja sam se zaljubila u ovu pesmu <3 Gabriel - Yugofreestyle @gabr1el_35',
    #             'Spot je napokon izasao <3 Gabriel - Yugofreestyle',
    #             'Jedva sam docekala Gabriel - Yugofreestyle',
    #             'Obozavam ovog lika Gabriel - Yugofreestyle',
    #             'Najdraza pesma ikad Gabriel - Yugofreestyle',
    #             'Balkanac repuje na nemackom i kida Gabriel - Yugofreestyle',
    #         ],
    #         'tags': ['gabr1el_35', 'yugofreestyle2', 'bakaprase', 'srbija', 'fyp', 'rafcamora'],
    #         'gdrive_dir': '1v2ygpUcAveJoA7wxfDdkKUJ01aDcv74q',
    #         'local_dir': 'drive_videos/TikTok/yugofreestyle2/',
    #         'videos_per_batch': 17,
    #     },
    #     'pazljivo': {
    #         'name': 'pazljivo',
    #         'titles': ['SPOT NAPOKON IZASAO!!! VASA - PAZLJIVO'],
    #         'tags': ['vasa', 'pazljivo', 'vasa_uno', 'fyp'],
    #         'gdrive_dir': '1fOjznRlLYGPKPjashVJ9p36LvDV3SvGp',
    #         'local_dir': 'drive_videos/TikTok/pazljivo/',
    #         'videos_per_batch': 0,
    #     },
    # },


#     Napisi mi 30 jako kratkih opisa za video na TikToku. Opisi ne smeju da imaju vise od 6 reci. Opisi su za pesmu koja se zove Provozamo, ima ljubavni karakter i pominje voznju kolima. Opisi treba da budu jednostavni, moderni i sa puno energije. Svi opisi treba da budu na Srpskom jeziku. Opisi treba da budu pisani iz prvog lica i u zenskom rodu.

# Primer:
# 1. Odlepila sam od ove pesme!
# 2. Mnogo jaka stvar



    'dance': {
        'onazna': {
            'name': 'onazna',
            'titles': [
                'Zaljubila sam se! DAVID - ONA ZNA',
                'DAVID - ONA ZNA',
                'Kako je pokidao! DAVID - ONA ZNA',
                'Tek pocinje, a tako kida DAVID - ONA ZNA',
                'YT DAVID - ONA ZNA',
            ],
            'tags': ['davidonazna', 'onazna', 'razbija', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/onazna/results/',
            'videos_per_batch': 2,
            'device': 'desk',
        },
        'provozamo': {
            'name': 'provozamo',
            'titles': [
                'Odlepila sam od ove pesme! PRAKSA - PROVOZAMO',
                'Mnogo jaka stvar PRAKSA - PROVOZAMO',
                'Praksa - Provozamo',
                'Brrrrr Praksa - Provozamo!',
                'Kada si pored mene PRAKSA - PROVOZAMO',
                'Vožnja uz ovu pesmu PRAKSA - PROVOZAMO',
                'Ne mogu da prestanem da pevam PRAKSA - PROVOZAMO',
                'Mnogo jaka stvar PRAKSA - PROVOZAMO',
            ],
            'tags': ['praksaprovozamo', 'srbija', 'bmw', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'drive_videos/TikTok/provozamo/',
            'videos_per_batch': 4,
            'device': 'desk',
        },
        # creator/data/ljubavnarepeat/results/00100
        'ljubavnarepeat': {
            'name': 'ljubavnarepeat',
            'titles': [
                'Kako kida lik Smiki - Ljubav na repeat',
                'Pokidao Smiki - Ljubav na repeat',
                'Luda sam za ovom pesmom Smiki - Ljubav na repeat',
                'Pravi MC Smiki - Ljubav na repeat',
                'Smiki - Ljubav na repeat',
            ],
            'tags': ['ljubavnarepeat', 'srbija', 'mc', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/ljubavnarepeat/results/',
            'videos_per_batch': 5,
            'device': 'desk',
        },
        'srceluduje': {
            'name': 'srceluduje',
            'titles': [
                'Moje srce opet luduje Kiki - Srce Luduje <3',
                'Kiki opet iskidao - Srce Luduje <3',
                'Poludela sam za ovom pesmom <3 Kiki - Srce Luduje',
                'Ne mogu da se suzdrzim uz ovo Kiki - Srce Luduje',
                'Ludim uz ovaj hit Kiki - Srce Luduje',
                'Kako ne bih ludela uz ovo? Kiki - Srce Luduje',
                'Ludim uz ovaj hit Kiki - Srce Luduje',
                'Pesma koja me vraća u život! Kiki - Srce Luduje',
            ],
            'tags': ['kiki', 'srceluduje', 'srbija', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/srceluduje/results/',
            'videos_per_batch': 2,
            'device': 'desk',
        },
        'belebembare': {
            'name': 'belebembare',
            'titles': [
                'STEVAN SEKULIC & DAYNE - BELE BEMBARE',
                'Kako vozi!! STEVAN SEKULIC & DAYNE - BELE BEMBARE',
                'Jedna od jacih pesama BELE BEMBARE',
                'Najbrzi momci STEVAN SEKULIC & DAYNE - BELE BEMBARE',
                'Kakva stvar! BELE BEMBARE',
            ],
            'tags': ['belebembare', 'dayne', 'stevan', 'fyp', 'bmw'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/belebembare/results/',
            'videos_per_batch': 1,
            'device': 'desk',
        },
        'rari': {
            'name': 'rari',
            'titles': [
                'Vraca se na scenu RAJKE - Rari',
                'RAJKE - Rari',
                'Evo ga opet RAJKE - Rari',
                'Napokon na sceni RAJKE - Rari',
                'Vratio se!!!! RAJKE - Rari',
            ],
            'tags': ['rajkerari', 'rajke', 'srbija', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/rari/results/',
            'videos_per_batch': 2,
            'device': 'desk',
        }
        # 'dance': {
            # 'name': 'dance',
            # 'titles': [
                # 'Vasa - Dance',
                # 'Kako je dobra ova pesma 😍 Vasa - Dance',
                # 'Najjaca pesma koju sam cula!! Vasa - Dance',
                # 'Jel se neko seca ovoga? Vasa - Dance',
                # 'Hit ovog leta - Vasa - Dance',
            # ],
            # 'tags': ['dance', 'vasa', 'vasadance', 'fyp', 'srbija', 'bakaprase'],
            # 'gdrive_dir': None,
            # 'local_dir': 'drive_videos/TikTok/dance/',
            # 'videos_per_batch': 5,
            # 'device': 'desk',
        # },
    },
    'redminote': {
        'onazna': {
            'name': 'onazna',
            'titles': [
                'Zaljubila sam se! DAVID - ONA ZNA',
                'DAVID - ONA ZNA',
                'Kako je pokidao! DAVID - ONA ZNA',
                'Tek pocinje, a tako kida DAVID - ONA ZNA',
                'YT DAVID - ONA ZNA',
            ],
            'tags': ['davidonazna', 'onazna', 'razbija', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/onazna/results/',
            'videos_per_batch': 1,
            'device': 'redminote',
            'sound_url': 'https://www.tiktok.com/music/Ona-zna-7211316912238626817',
            'sound_name': 'Ona zna',
            'device_id': '3646ec0f',
        },
        'ljubavnarepeat': {
            'name': 'ljubavnarepeat',
            'titles': [
                'Kako kida lik Smiki - Ljubav na repeat',
                'Pokidao Smiki - Ljubav na repeat',
                'Luda sam za ovom pesmom Smiki - Ljubav na repeat',
                'Pravi MC Smiki - Ljubav na repeat',
                'Smiki - Ljubav na repeat',
            ],
            'tags': ['ljubavnarepeat', 'srbija', 'mc', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/ljubavnarepeat/results/',
            'videos_per_batch': 1,
            'device': 'redminote',
            'sound_url': None,
            'sound_name': None,
            'device_id': '3646ec0f',
        },
        'belebembare': {
            'name': 'belebembare',
            'titles': [
                'STEVAN SEKULIC & DAYNE - BELE BEMBARE',
                'Kako vozi!! STEVAN SEKULIC & DAYNE - BELE BEMBARE',
                'Jedna od jacih pesama BELE BEMBARE',
                'Najbrzi momci STEVAN SEKULIC & DAYNE - BELE BEMBARE',
                'Kakva stvar! BELE BEMBARE',
            ],
            'tags': ['belebembare', 'dayne', 'stevan', 'fyp', 'bmw'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/belebembare/results/',
            'videos_per_batch': 1,
            'device': 'desk',
            'device': 'redminote',
            'sound_url': 'https://www.tiktok.com/music/original-sound-7211478577685367557',
            'sound_name': 'Stevan Sekulic x Dayne x Bele Bembare',
            'device_id': '3646ec0f',
        },
        'provozamo': {
            'name': 'provozamo',
            'titles': [
                'Odlepila sam od ove pesme! PRAKSA - PROVOZAMO',
                'Mnogo jaka stvar PRAKSA - PROVOZAMO',
                'Praksa - Provozamo',
                'Brrrrr Praksa - Provozamo!',
                'Kada si pored mene PRAKSA - PROVOZAMO',
                'Vožnja uz ovu pesmu PRAKSA - PROVOZAMO',
                'Ne mogu da prestanem da pevam PRAKSA - PROVOZAMO',
                'Mnogo jaka stvar PRAKSA - PROVOZAMO',
            ],
            'tags': ['praksaprovozamo', 'srbija', 'bmw', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'drive_videos/TikTok/provozamo/',
            'videos_per_batch': 1,
            'device': 'redminote',
            'sound_url': 'https://www.tiktok.com/music/Provozamo-7203423793157720065',
            'sound_name': 'Provozamo',
            'device_id': '3646ec0f',
        },
        'srceluduje': {
            'name': 'srceluduje',
            'titles': [
                'Moje srce opet luduje Kiki - Srce Luduje <3',
                'Kiki opet iskidao - Srce Luduje <3',
                'Poludela sam za ovom pesmom <3 Kiki - Srce Luduje',
                'Ne mogu da se suzdrzim uz ovo Kiki - Srce Luduje',
                'Ludim uz ovaj hit Kiki - Srce Luduje',
                'Kako ne bih ludela uz ovo? Kiki - Srce Luduje',
                'Ludim uz ovaj hit Kiki - Srce Luduje',
                'Pesma koja me vraća u život! Kiki - Srce Luduje',
            ],
            'tags': ['kiki', 'srceluduje', 'srbija', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/srceluduje/results/',
            'videos_per_batch': 1,
            'device': 'redminote',
            'sound_url': 'https://www.tiktok.com/music/Srce-luduje-7206151702318189317',
            'sound_name': 'Srce luduje',
            'device_id': '3646ec0f',
        },
        'rari': {
            'name': 'rari',
            'titles': [
                'Vraca se na scenu RAJKE - Rari',
                'RAJKE - Rari',
                'Evo ga opet RAJKE - Rari',
                'Napokon na sceni RAJKE - Rari',
                'Vratio se!!!! RAJKE - Rari',
            ],
            'tags': ['rajkerari', 'rajke', 'srbija', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/rari/results/',
            'videos_per_batch': 1,
            'device': 'redminote',
            'sound_url': 'https://www.tiktok.com/music/RAJKE-RARI-SPEED-UP-7207038222911032069',
            'sound_name': 'RAJKE RARI SPEED UP',
            'device_id': '3646ec0f',
        },
    },
    'j7': {
        'onazna': {
            'name': 'onazna',
            'titles': [
                'Zaljubila sam se! DAVID - ONA ZNA',
                'DAVID - ONA ZNA',
                'Kako je pokidao! DAVID - ONA ZNA',
                'Tek pocinje, a tako kida DAVID - ONA ZNA',
                'YT DAVID - ONA ZNA',
            ],
            'tags': ['davidonazna', 'onazna', 'razbija', 'fyp'],
            'gdrive_dir': None,
            'local_dir': 'creator/data/onazna/results/',
            'videos_per_batch': 1,
            'device': 'j7',
            'sound_url': 'https://www.tiktok.com/music/Ona-zna-7211316912238626817',
            'sound_name': 'Ona zna',
            'device_id': '100.99.18.17',
        },
    },
}

ACCOUNTS_DB = 'accounts_db.json'
VIDEOS_DB = 'videos_db.json'
UPLOAD_RETRY = 3



def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--campaign", help="Campaign Name", required=True)
    parser.add_argument("-d", "--device", help="Device Name", required=True)
    args = parser.parse_args()

    print()
    print('Starting job...')
    # Load data
    print('Reading accounts...')
    accounts = pd.read_json(ACCOUNTS_DB, lines=True)
    print('Reading video...')
    videos = pd.read_json(VIDEOS_DB, lines=True)

    active_accounts = accounts[accounts.active & (accounts.device == args.device)].sample(frac=1)

    if args.campaign not in CAMPAIGNS_GROUPS:
        raise Exception(f"Unknown campaign group {args.campaign}")
    campaign_group = CAMPAIGNS_GROUPS[args.campaign]
        

    videos_per_batch = sum(camp['videos_per_batch'] for camp in campaign_group.values())
    if videos_per_batch != len(active_accounts):
        print(f"Campaign videos {videos_per_batch}, active accounts {len(active_accounts)}")
        raise Exception("Number of accounts does not match number of videos per batch")
    
    message_report = dict()
    for campaign_name in campaign_group:
        assert campaign_group[campaign_name]['device'] == args.device
        vids = campaign_group[campaign_name]['videos_per_batch']
        message_report[campaign_name] = do_campaign(campaign_group[campaign_name], active_accounts.head(vids), videos, args.device)
        if vids != 0:
            active_accounts = active_accounts.tail(-vids)

    return message_report


def do_campaign(campaign, active_accounts, videos, device):
    print(f"Executing campaign {campaign['name']} with {campaign['videos_per_batch']} videos")

    # Sync drive videos
    if campaign['gdrive_dir']:
        drive.sync(local_dir=campaign['local_dir'], gdrive_dir=campaign['gdrive_dir'])

    local_files = sorted(list(glob.glob(campaign['local_dir'] + '*')))
    new_files = [
        file for file in local_files
        if file not in videos.file.values
    ]
    random.shuffle(new_files)
    print(f"Unuploaded videos: {len(new_files)}")
    if len(new_files) <= len(active_accounts):
        telegram.send_message(f"No new files for campaign {campaign['name']}")

    print('Posting videos...')
    errors = 0

    for video_file, account in zip(new_files, active_accounts.itertuples(index=False)):
        title = random.choice(campaign['titles'])

        tiktok_id = ''
        tiktok_url = ''
        successful_upload = False
        if device == 'desk':
            for retry in range(UPLOAD_RETRY):
                try:
                    print(f"Trying to upload video, retry: {retry} account: {account.username} video: {video_file}")
                    tiktok_id = str(tiktok_uploader.uploadVideo(
                        session_id=account.session_id,
                        video=video_file,
                        title=title,
                        tags=campaign['tags'],
                        verbose=True
                    ))

                    if tiktok_id == False:
                        print("Ohhhhh")
                        raise Exception("Upload Failed")

                    successful_upload = True
                    break
                except Exception as e:
                    if retry == UPLOAD_RETRY - 1:
                        print(f"Upload failed with account {account.username} for video {video_file}")
                        print(f"{e}")
                        errors += 1
                        # maybe send tiktok
                        # raise e
                    else:
                        print(f"Upload failed, retrying, error: {e}")
                        time.sleep(61)
        else:
            print(f"Trying to upload video on {device}, account: {account.username},{account.name} video: {video_file}")
            try:
                d = android.upload_video(
                    account=account,
                    video=video_file,
                    title=title,
                    tags=campaign['tags'],
                    sound_url=campaign['sound_url'],
                    sound_name=campaign['sound_name'],
                    device_id=campaign['device_id'],
                    device=device,
                )
                successful_upload = bool(d)
                tiktok_url = android.get_link(d)
                android.cleanup(d)
            except Exception as e:
                print(f"Upload failed with account {account.username} for video {video_file}")
                print(f"{e}")
                traceback.print_exc()
                errors += 1

    

        if successful_upload:
            with open(VIDEOS_DB, 'a') as videos_db:
                videos_db.write(json.dumps({
                    "file": video_file,
                    "account_id": account.id,
                    "tiktok_id": tiktok_id,
                    "title": title,
                    "time": str(datetime.now()),
                    "device": device,
                    "tiktok_url": tiktok_url,
                }) + '\n')

            print(f'Uploaded video {video_file} with account {account.id} {account.username} tiktok_id {tiktok_id}')

        wait_min = 5
        print(f"Waiting 1-{wait_min + 1} minutes")
        # time.sleep(5 + random.randint(1, 6))
        time.sleep(60 + random.randint(1, wait_min * 60))
    
    uploaded = len(list(zip(new_files, active_accounts.iterrows())))
    unpuloaded = len(new_files) - uploaded
    return uploaded, unpuloaded, errors

if __name__ == '__main__':
    try:
        telegram.send_message(f"Starting campaign uploads...")
        message_report = main()
        message = '\n'.join([f"Uploaded {val[0]} videos, {val[2]} errors, {val[1]} left for campaign {key}" for key,val in message_report.items()])
        telegram.send_message(f"All good!\n" + message)
    except Exception as e:
        telegram.send_message(f"Error {str(e)}")
        raise e
