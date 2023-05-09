"""This is a script that will plot the play_count of all videos of a given campaign chronologically."""

import argparse
import json
import os

import pandas as pd
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('campaign', type=str, help='Campaign name')
    args = parser.parse_args()

    videos = pd.read_json('videos_joined.json', lines=True).fillna('')
    videos = videos[videos['campaign'] == args.campaign]
    videos = videos.sort_values(by='time')

    videos['date'] = pd.to_datetime(videos['time']).dt.date

    results = videos.groupby('date').sum()

    print(f"Total views: {results['play_count'].sum()}")
    print(f"Total videos: {len(videos)}")
    print(f"Average views per video: {results['play_count'].sum() / len(videos)}")

    plt.plot(results.index, results['play_count'])
    plt.show()
    
    
if __name__ == "__main__":
    main()
