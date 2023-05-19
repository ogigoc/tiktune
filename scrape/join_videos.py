import re

import pandas as pd

old_old_filename_mapping = {
    'background': 0,
    'background_edit': 1,
    'background_timing': -1,
}
old_filename_mapping = {
    'background': 0,
    'template': 1,
    'background_edit': 2,
    'background_timing': -1,
}
new_filename_mapping = {
    'background_timing': 0,
    'background': 1,
    'template': 2,
    'background_edit': 3,
}



def get_from_name_internal(file, field):
    file_name = file.split('/')[-1]

    # skip handmade videos
    if re.match(r'^\w\d+.mp4', file_name):
        return ''

    # starts with 5 digits and a semicolon
    if re.match(r'^\d{5};', file_name):
        # new format
        pos = new_filename_mapping[field]
        file_parts = file_name.split(';')
        # return file_parts[pos]
        return re.sub(r'[^\w]', '', file_parts[pos])
    else:
        # old format
        if '|' in file_name:
            if field == 'template':
                return ''

            pos = old_old_filename_mapping[field]
            
            file_parts = file_name.split('|')
            if len(file_parts) == 1:
                return ''
            if pos == 1:
                return ''
            elif len(file_parts) == 4:
                file_parts = [file_parts[0], ''.join(file_parts[1:3]), ''.join(file_parts[1:3]), file_parts[3]]

            return file_parts[pos]
        elif ';' in file_name:
            pos = old_filename_mapping[field]
            file_parts = file_name.split(';')
            return file_parts[pos]

def get_from_name(file, field):
    result = get_from_name_internal(file, field)
    if field == 'background_edit' and result and result.endswith('mp4'):
        result = result[:-4].replace('\s+', '_')
        print(result)
        print(file)
    
    return result
            
            
parsed_videos = pd.read_json('videos.json', dtype={'video_id': str}, lines=True)
uploaded_videos = pd.read_json('../videos_db.json', lines=True)
accounts = pd.read_json('../accounts_db.json', lines=True, dtype={'user_id': str}).fillna('')

videos = parsed_videos.merge(uploaded_videos, how='left', left_on='video_id', right_on='tiktok_id')
videos = videos.merge(accounts, how='left', on='username')
del videos['tiktok_id']
del videos['title']

videos['background'] = videos.file.fillna('').apply(lambda f: get_from_name(f, 'background'))
videos['background_timing'] = videos.file.fillna('').apply(lambda f: get_from_name(f, 'background_timing'))
videos['background_edit'] = videos.file.fillna('').apply(lambda f: get_from_name(f, 'background_edit'))
videos['template'] = videos.file.fillna('').apply(lambda f: get_from_name(f, 'template'))

videos['hour'] = videos.create_time.dt.hour.apply(lambda x: f'{x}'.zfill(2) + ' - x')


videos.to_json('videos_joined.json', orient='records', lines=True)
