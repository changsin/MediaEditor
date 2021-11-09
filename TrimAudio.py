import argparse
import glob
import math
import os

# from moviepy.audio.io import AudioFileClip
# from moviepy.audio.AudioClip import concatenate_audioclips
# import moviepy

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


def extract_voice(file_in, file_out, threshold=0.01, window_size=0.3):
    print("Processing {} to {}".format(file_in, file_out))
    audio = AudioFileClip(file_in)

    print(audio.duration)
    n_windows = math.floor(audio.end / window_size)

    keep_clips = []

    is_prev_silence = True
    start_time = 0
    end_time = 0

    i = 2
    while i < n_windows:
        # print(" #{} - {}".format(i * window_size, (i + 1) * window_size))
        s = audio.subclip(i * window_size, (i + 1) * window_size)
        print(i, s.max_volume())
        if s.max_volume() >= threshold:
            if is_prev_silence: # start speaking
                start_time = i * window_size
                print('start_time', start_time)

            is_prev_silence = False

        else:
            if not is_prev_silence: # end speaking
                if i < n_windows - 1:
                    end_time = (i + 1) * window_size
                    i += 1
                else:
                    end_time = audio.end
                keep_clips.append(audio.subclip(start_time, end_time))
                print(f'{start_time} - {end_time}')

            is_prev_silence = True

        i += 1

    if (len(keep_clips) == 0 and start_time > 0) or end_time < start_time:
        end_time = audio.end
        keep_clips.append((audio.subclip(start_time, end_time)))

    if len(keep_clips) > 0:
        edited_audio = concatenate_audioclips(keep_clips)

        print("Writing to {}".format(file_out))
        edited_audio.write_audiofile(file_out)
        edited_audio.close()
    else:
        print("###Empty clips ", file_in)

    audio.close()


def extract_voices(path_in, path_out, threshold=0.01, window_size=0.3):
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
    parser.add_argument("-threshold", action="store", dest="threshold", type=str)
    parser.add_argument("-window_size", action="store", dest="window_size", type=str)

    args = parser.parse_args()

    extract_voices(args.path_in, args.path_out, threshold=args.threshold, window_size=args.window_size)
