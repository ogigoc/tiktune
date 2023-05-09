import pandas as pd

def get_from_name(file, pos):
    file_name = file.split('/')[-1]
    if '|' in file_name:
        file_parts = file_name.split('|')
        if len(file_parts) == 1:
            return ''
        if pos == 1:
            return ''
        elif len(file_parts) == 4:
            file_parts = [file_parts[0], ''.join(file_parts[1:3]), ''.join(file_parts[1:3]), file_parts[3]]

        return file_parts[pos]
    elif ';' in file_name:
        file_parts = file_name.split(';')
        return file_parts[pos]
parsed_videos = pd.read_json('videos.json', dtype={'video_id': str}, lines=True)
uploaded_videos = pd.read_json('../videos_db.json', lines=True)
accounts = pd.read_json('../accounts_db.json', lines=True, dtype={'user_id': str}).fillna('')

videos = parsed_videos.merge(uploaded_videos, how='left', left_on='video_id', right_on='tiktok_id')
videos = videos.merge(accounts, how='left', on='username')
del videos['tiktok_id']
del videos['title']

videos['background'] = videos.file.fillna('').apply(lambda f: get_from_name(f, 0))
videos['background_timing'] = videos.file.fillna('').apply(lambda f: get_from_name(f, -1))
videos['background_edit'] = videos.file.fillna('').apply(lambda f: get_from_name(f, 2))
videos['template'] = videos.file.fillna('').apply(lambda f: get_from_name(f, 1))

videos['hour'] = videos.create_time.dt.hour.apply(lambda x: f'{x}'.zfill(2) + ' - x')


videos.to_json('videos_joined.json', orient='records', lines=True)
