import argparse
import glob
import math
import os

from moviepy.editor import AudioFileClip, concatenate_audioclips


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


def extract_voice(file_in, file_out, threshold=0.03, window_size=0.5):
    print("Processing {} to {}".format(file_in, file_out))
    audio = AudioFileClip(file_in)

    print(audio.duration)
    n_windows = math.floor(audio.end / window_size)

    keep_clips = []

    is_prev_silence = True
    start_time = 0

    i = 1
    while i < n_windows:
        # print(" #{} - {}".format(i * window_size, (i + 1) * window_size))
        s = audio.subclip(i * window_size, (i + 1) * window_size)
        print(i, s.max_volume())
        if s.max_volume() >= threshold:
            if is_prev_silence: # start speaking
                start_time = i * window_size

            is_prev_silence = False

        else:
            if not is_prev_silence: # end speaking
                if i < n_windows - 2:
                    end_time = (i + 2) * window_size
                else:
                    end_time = i * window_size
                i += 1
                keep_clips.append(audio.subclip(start_time, end_time))
                # print(f'{start_time} - {end_time}')

            is_prev_silence = True
        i += 1

    edited_audio = concatenate_audioclips(keep_clips)

    print("Writing to {}".format(file_out))
    edited_audio.write_audiofile(file_out)

    audio.close()
    edited_audio.close()


def extract_voices(path_in, path_out):
    files = glob_files(path_in)

    if not os.path.exists(path_out):
        print("Creating folder to ", path_out)
        os.mkdir(path_out)

    for file_in in files:
        file_out = os.path.join(path_out, os.path.basename(file_in))

        extract_voice(file_in, file_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-path_in", action="store", dest="path_in", type=str)
    parser.add_argument("-path_out", action="store", dest="path_out", type=str)

    args = parser.parse_args()

    extract_voices(args.path_in, args.path_out)
