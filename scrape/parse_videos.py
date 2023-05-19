import glob
import json
import yaml

RESULT_FILE = 'videos.json'
CAMPAIGNS_FILE = '../campaigns.yaml'

def main():
    files = sorted(list(glob.glob('data/*.json')), reverse=True)
    videos = dict()

    print("Reading campaigns...")
    with open(CAMPAIGNS_FILE, 'r') as file:
        campaigns = yaml.safe_load(file)
    campaign_tags = {
    campaign['tags'][0]
    for campaign in campaigns.values()
    }

    for file in files:
        response = json.load(open(file, 'r'))
        videos_resp = response['aweme_list']
        print(f"{len(videos_resp)} videos in {file}")

        # username check
        username = file.split(':')[-1][:-5]
        print(username, videos_resp[0]['author']['unique_id'])
        if not (username == 'serbianhitsongs' and videos_resp[0]['author']['unique_id'] == 'julijagarasan') \
            and not (username == 'bakapraseflexx' and videos_resp[0]['author']['unique_id'] == 'bakapraseflleex'):
            if videos_resp[0]['author']['unique_id'] != username:
                print(videos_resp[0]['author']['unique_id'])
                print(username)
                raise Exception(f"Username mismatch: {username} != {videos_resp[0]['author']['unique_id']}")

        for video_resp in videos_resp:
            video = dict()
            video_id = video_resp['aweme_id']
            video['video_id'] = video_id
            video['username'] = username
            video.update(**video_resp['statistics'])
            del video['aweme_id']
            video['url'] = f'https://www.tiktok.com/@{username}/video/{video_id}'
            video['create_time'] = video_resp['create_time']
            video['description'] = video_resp['desc']
            video['music'] = 'original' if video_resp['music']['title'].startswith('original sound') else video_resp['music']['title']
            video['region'] = video_resp['region']
            for k, v in video_resp['risk_infos'].items():
                video['risk_' + k] = v
            video['hashtags'] = [h['hashtag_name'] for h in video_resp['text_extra'] if h['type'] == 1]
            video['campaign'] = next((h for h in video['hashtags'] if h in campaign_tags), None)

            if video_id not in videos:
                videos[video_id] = video
    
    with open(RESULT_FILE, 'w') as file:
        videos_list = sorted(videos.values(), key=lambda v: v['create_time'])
        # json.dump(videos_list, file, indent=4)
        for video in videos_list:
            file.write(json.dumps(video) + '\n')


if __name__ == '__main__':
    main()
