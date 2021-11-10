import argparse
import glob
import math
import os

from pydub import AudioSegment

DEFAULT_THRESHOLD = 60
DEFAULT_WINDOW_SIZE = 0.3


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


def extract_voice(file_in, file_out, threshold=DEFAULT_THRESHOLD, window_size=DEFAULT_WINDOW_SIZE):

    audio = AudioSegment.from_file(file_in, format="mp3")

    audio_end = len(audio)/1000
    # print("Duration", len(audio)/1000)

    n_windows = math.floor(audio_end / window_size)

    keep_clips = []

    is_prev_silence = True
    start_time = 0
    end_time = 0

    i = 2
    while i < n_windows:
        # s = audio.subclip(i * window_size, (i + 1) * window_size)
        s = audio[i * window_size*1000:(i + 1) * window_size*1000]
        # print(s.raw_data)
        # print(" #{}: {} - {} {}".format(i, i * window_size, (i + 1) * window_size, s.dBFS))
        # print(" #{}: {}".format(i, s.dBFS*-1))
        if s.dBFS*-1 < threshold:
            if is_prev_silence: # start speaking
                start_time = i * window_size
                # print(' #start_time', start_time)

            is_prev_silence = False

        else:
            if not is_prev_silence: # end speaking
                if i < n_windows - 1:
                    end_time = (i + 1) * window_size
                    i += 1
                else:
                    end_time = audio_end
                keep_clips.append(audio[start_time*1000:end_time*1000])
                # print(f' #duration:{start_time} - {end_time}')

            is_prev_silence = True

        i += 1

    if (len(keep_clips) == 0 and start_time > 0) or end_time < start_time:
        keep_clips.append(audio[start_time*1000:audio_end*1000])

    if len(keep_clips) > 0:
        edited_audio = keep_clips[0]

        # print("keep_clips:", len(keep_clips), len(keep_clips[0]), audio_end)
        for i in range(len(keep_clips)):
            if i == 0:
                continue
            # print("i", i, len(keep_clips[i]))
            edited_audio = edited_audio.append(keep_clips[i])

        print('Writing {} with duration {}'.format(file_out, len(edited_audio)))
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

    window_size = DEFAULT_WINDOW_SIZE
    if args.window_size:
        window_size = float(args.window_size)

    print("threshold={} window_size={}".format(threshold, window_size))
    extract_voices(args.path_in, args.path_out, threshold=threshold, window_size=window_size)
