import argparse
import AudioOwl as audioowl
from moviepy.editor import AudioFileClip, VideoFileClip
from moviepy.video.fx.all import invert_colors
from moviepy.video.compositing.concatenate import concatenate_videoclips
from madmom.features.beats import RNNBeatProcessor, MultiModelSelectionProcessor
import librosa

import numpy as np
from scenedetect import detect, ContentDetector


BEAT_EFFECT_DURATION = 0.05

def get_beat_times(template):
    import aubio
    # Parameters
    win_s = 512                 # fft size
    hop_s = win_s // 2          # hop size

    # Create an aubio source object
    source = aubio.source(template, hop_size=hop_s)

    # Create an aubio tempo object for beat tracking
    tempo = aubio.tempo("default", win_s, hop_s, source.samplerate)

    # Process the audio file and detect beats
    beats = []
    total_frames = 0
    while True:
        samples, read = source()
        is_beat = tempo(samples)
        if is_beat:
            beats.append(total_frames)
        total_frames += read
        if read < source.hop_size:
            break

    # Convert the beat frame numbers to timestamps in seconds
    print(source.samplerate)
    print(beats)
    beat_times = np.array(beats) / float(source.samplerate)
    print(beat_times)
    return beat_times


def analyze_audio(template):
    print(f"Analyzing audio for {template}")
    audio_clip = AudioFileClip(template)
    sample_rate = int(audio_clip.fps)
    print(f"Sample rate: {sample_rate}")
    data = audioowl.analyze_file(path=template, sr=sample_rate)
    beat_samples = data['beat_samples']
    beat_times = [sample / sample_rate for sample in beat_samples]
    print(f"Beat times: {beat_times}")

    # beat_times = get_beat_times(template)

    # print(f"Loading audio...")
    # audio, sample_rate = librosa.load(template, sr=sample_rate)
    # print(f"Calculating beats...")
    # beat_times = get_beat_times(audio)
    print(f"Done")
    print(f"Number of beats: {len(beat_times)}")
    return beat_times

def invert_color_on_beat(video, beat_times):
    videos = []
    prev_time = 0
    for beat_time in beat_times:
        before_beat = video.subclip(prev_time, beat_time)
        on_beat = video.subclip(beat_time, min(beat_time + BEAT_EFFECT_DURATION, video.duration))
        on_beat = on_beat.fx(invert_colors)
        videos.append(before_beat)
        videos.append(on_beat)
        prev_time = beat_time + BEAT_EFFECT_DURATION
    if prev_time < video.duration:
        videos.append(video.subclip(prev_time, video.duration))
    return concatenate_videoclips(videos)

def invert_color_on_3_4_beat(video, beat_times, offset=3):
    videos = []
    prev_time = 0
    for i, beat_time in enumerate(beat_times):
        if (i + offset) % 4 == 0:
            before_beat = video.subclip(prev_time, beat_time)

            next_beat_time = beat_times[i + 1] if i + 1 < len(beat_times) else video.duration
            on_beat = video.subclip(beat_time, next_beat_time)
            on_beat = on_beat.fx(invert_colors)
            videos.append(before_beat)
            videos.append(on_beat)
            prev_time = next_beat_time
    if prev_time < video.duration:
        videos.append(video.subclip(prev_time, video.duration))
    return concatenate_videoclips(videos)

def get_scenes(video_path):
    scene_list = detect(video_path, ContentDetector())
    # scenes = []
    print(scene_list)
    # for scene in scene_list:
    #     scenes.append(scene[1].get_frames())
    # return scenes
    return scene_list

def main():
    parser = argparse.ArgumentParser(description="Apply video effects based on audio beats.")
    parser.add_argument('video_file', type=str, help="The path to the video file to analyze.")
    parser.add_argument('--effect', type=str, default="invert", help="The effect to apply on beats. Default is 'invert'.")
    args = parser.parse_args()
    
    video_clip = VideoFileClip(args.video_file)
    beat_times = analyze_audio(args.video_file)

    if args.effect == 'invert':
        final_video = invert_color_on_beat(video_clip, beat_times)
    elif args.effect == 'invert_3_4':
        final_video = invert_color_on_3_4_beat(video_clip, beat_times)
    elif args.effect == 'scene_split':
        scenes = get_scenes(args.video_file)
        scene_times = [scene[0].get_seconds() for scene in scenes][1:]
        final_video = invert_color_on_beat(video_clip, scene_times)
    else:
        print(f"Unknown effect: {args.effect}")
        return
    
    output_file = 'test_inverted.mp4'
    final_video.write_videofile(output_file)
    print(f"Video saved to {output_file}")

if __name__ == "__main__":
    main()
