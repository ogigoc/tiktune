import csv
import glob

import yt_dlp

def main():
    videos = list(csv.reader(open('backgrounds.csv', 'r')))[1:]

    # skip old unnamed vids
    videos = videos[43:]
    
    for video in videos:
        output_dir = f'data/{video[1]}/music_videos/'
        output_name = video[2]
        
        existing = glob.glob(f'{output_dir}{output_name}*')
        if existing:
            print(f"Already found video {existing[0]}")
            continue

        with yt_dlp.YoutubeDL({'outtmpl': output_dir + output_name + '.%(ext)s'}) as ydl:
            print(f"Downloading video {video[0]} for {video[1]}")
            ydl.download(video[0])


if __name__ == '__main__':
    main()
