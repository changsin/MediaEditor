import argparse
import glob
import math
import os

from moviepy.editor import AudioFileClip, concatenate_audioclips
from pydub import AudioSegment

DEFAULT_THRESHOLD = 65      # 65 for pydub, 0.01 for moviepy
DEFAULT_WINDOW_SIZE = 0.1


def glob_files(folder, file_type='*'):
    search_string = os.path.join(folder, file_type)
    files = glob.glob(search_string)

    print('Searching ', search_string)
    paths = []
    for f in files:
        if os.path.isdir(f):
            sub_paths = glob_files(f + '/')
            paths += sub_paths
        else:
            paths.append(f)

    # We sort the images in alphabetical order to match them
    #  to the annotation files
    paths.sort()

    return paths


def extract_voice_movie_py(file_in, file_out, threshold=DEFAULT_THRESHOLD, window_size=DEFAULT_WINDOW_SIZE):

    audio_clip = AudioFileClip(file_in)

    audio_end = audio_clip.end
    # print("Duration", len(audio)/1000)

    n_windows = math.floor(audio_end / window_size)

    clips_to_save = []

    is_started = False
    start_time = 0
    end_time = 0

    i = 2   # skip the first two windows for there is usually some noise
    while i < n_windows:
        sub_clip = audio_clip.subclip(i * window_size, (i + 1) * window_size)
        if sub_clip.max_volume() > threshold:
            if not is_started:  # started speaking
                start_time = i * window_size
                # print(' #start_time', start_time)

            is_started = True

        else:
            if is_started:  # speaking ended
                if i < n_windows - 1:
                    # add one more window to capture the fade out effect
                    end_time = (i + 1) * window_size
                    i += 1
                else:
                    end_time = audio_end
                clips_to_save.append(audio_clip.subclip(start_time, end_time))
                # print(f' #duration:{start_time} - {end_time}')

            is_started = False

        i += 1

    # If the audio track never fades out (kept talking till the end)
    #   take the rest of the audio track.
    # This can happen in two occasions:
    #   1. The entire audio clip is filled with noise - no kept clips
    #   2. There was a moment of silence in the middle but noise started and never ended in silence
    if (len(clips_to_save) == 0 and start_time > 0) or end_time < start_time:
        clips_to_save.append(audio_clip.subclip(start_time, audio_end))

    if len(clips_to_save) > 0:
        edited_audio = concatenate_audioclips(clips_to_save)
        print('Writing {} with duration {:.2f}'.format(file_out, edited_audio.end))
        edited_audio.write_audiofile(file_out)
        edited_audio.close()
    else:
        print("###Empty clips ", file_in)

    audio_clip.close()


def extract_voice(file_in, file_out, threshold=DEFAULT_THRESHOLD, window_size=DEFAULT_WINDOW_SIZE):

    audio_clip = AudioSegment.from_file(file_in, format="mp3")

    audio_end = len(audio_clip)
    # print("Duration", len(audio)/1000)

    # window_size is in seconds so scale it to milliseconds
    window_size = window_size * 1000
    n_windows = math.floor(audio_end / window_size)

    clips_to_save = []

    is_started = False
    start_time = 0
    end_time = 0

    i = 2   # skip the first two windows for there is usually some noise
    while i < n_windows:
        sub_clip = audio_clip[i * window_size:(i + 1) * window_size]
        # db relative to the maximum possible loudness
        # https://github.com/jiaaro/pydub/blob/master/API.markdown
        # turn the negative db to positive to make it easy to understand
        print(" #{}: {:.2f}".format(i, sub_clip.dBFS*-1))
        if sub_clip.dBFS * -1 < threshold:
            if not is_started:  # started speaking
                start_time = i * window_size
                # print(' #start_time', start_time)

            is_started = True

        else:
            if is_started:      # speaking ended
                if i < n_windows - 1:
                    # add one more window to capture the fade out effect
                    end_time = (i + 1) * window_size
                    i += 1
                else:
                    end_time = audio_end
                clips_to_save.append(audio_clip[start_time:end_time])
                # print(f' #duration:{start_time} - {end_time}')

            is_started = False

        i += 1

    # If the audio track never fades out (kept talking till the end)
    #   take the rest of the audio track.
    # This can happen in two occasions:
    #   1. The entire audio clip is filled with noise - no kept clips
    #   2. There was a moment of silence in the middle but noise started and never ended in silence
    if (len(clips_to_save) == 0 and start_time > 0) or end_time < start_time:
        clips_to_save.append(audio_clip[start_time:audio_end])

    if len(clips_to_save) > 0:
        edited_audio = clips_to_save[0]

        # print("clips_to_save:", len(keep_clips), len(keep_clips[0]), audio_end)
        for i in range(1, len(clips_to_save)):
            edited_audio = edited_audio.append(clips_to_save[i], crossfade=min(100, len(clips_to_save[i])))

        print('Writing {} with duration {:.2f}'.format(file_out, len(edited_audio)))
        edited_audio.export(file_out, format='mp3')

    else:
        print("###Empty clips ", file_in)


def extract_voices(path_in, path_out, threshold=DEFAULT_THRESHOLD, window_size=DEFAULT_WINDOW_SIZE):
    files = glob_files(path_in)

    if not os.path.exists(path_out):
        print("Creating folder to ", path_out)
        os.mkdir(path_out)

    for file_in in files:
        file_out = os.path.join(path_out, os.path.basename(file_in))

        # extract_voice(file_in, file_out, threshold=threshold, window_size=window_size)
        extract_voice(file_in, file_out, threshold=threshold, window_size=window_size)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_in", action="store", dest="path_in", type=str)
    parser.add_argument("--path_out", action="store", dest="path_out", type=str)
    parser.add_argument("--threshold", action="store", dest="threshold", type=str)
    parser.add_argument("--window_size", action="store", dest="window_size", type=str)

    args = parser.parse_args()

    threshold = DEFAULT_THRESHOLD
    if args.threshold:
        threshold = float(args.threshold)
        print(threshold, 'specified ####')

    window_size = DEFAULT_WINDOW_SIZE
    if args.window_size:
        window_size = float(args.window_size)

    print("threshold={} window_size={}".format(threshold, window_size))
    extract_voices(args.path_in, args.path_out, threshold=threshold, window_size=window_size)
