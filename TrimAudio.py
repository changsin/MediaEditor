from moviepy.editor import AudioClip, AudioFileClip, concatenate_audioclips
import math

def detect_leading_silence(audio, threshold=-0.05, window_size=0.1):
    start_time = 0
    n_windows = math.floor(audio.end / window_size)

    for i in range(n_windows):
        print(" #{} - {}".format(i * window_size, (i + 1) * window_size))
        s = audio.subclip(i * window_size, (i + 1) * window_size)
        print(s.max_volume())
        if s.max_volume() >= threshold:
            start_time = i * window_size
            break

    return start_time


def detect_trailing_silence(audio, threshold=-0.05, window_size=0.1):
    end_time = 0
    n_windows = math.floor(audio.end / window_size)

    for i in range(n_windows, -1, -1):
        print(" #{} - {}".format(i * window_size, (i - 1) * window_size))
        s = audio.subclip(i * window_size, (i - 1) * window_size)
        print(s.max_volume())
        if s.max_volume() < threshold:
            end_time = i * window_size
            break

    return end_time


audio_path = 'data\\audio\\50A_F_1402_6.mp3'

threshold = 0.05
window_size = 0.5

audio = AudioFileClip(audio_path)

print(audio.duration)

n_windows = math.floor(audio.end / window_size)

keep_clips = []

is_prev_silence = True
start_time = 0
end_time = 0

i = 0
while i < n_windows:
    print(" #{} - {}".format(i * window_size, (i + 1) * window_size))
    s = audio.subclip(i * window_size, (i + 1) * window_size)
    print(s.max_volume())
    if s.max_volume() >= threshold:
        if is_prev_silence: # start speaking
            start_time = i * window_size

        is_prev_silence = False
    else:
        if not is_prev_silence: # end speaking
            end_time = (i + 1) * window_size
            i += 2
            keep_clips.append(audio.subclip(start_time, end_time))
            print(f'{start_time} - {end_time}')

        is_prev_silence = True
    i += 1

# for i in range(n_windows):
#     print(" #{} - {}".format(i * window_size, (i + 1) * window_size))
#     s = audio.subclip(i * window_size, (i + 1) * window_size)
#     print(s.max_volume())
#     if s.max_volume() >= threshold:
#         if is_prev_silence: # start speaking
#             start_time = i * window_size
#
#         is_prev_silence = False
#     else:
#         if not is_prev_silence: # end speaking
#             end_time = i * window_size
#             keep_clips.append(audio.subclip(start_time, end_time))
#             print(f'{start_time} - {end_time}')
#
#         is_prev_silence = True

edited_audio = concatenate_audioclips(keep_clips)

edited_audio.write_audiofile(
    'out.mp3',
    # codec='aac'
)

audio.close()
edited_audio.close()

#
# from pydub import AudioSegment
#
# def detect_leading_silence(sound, silence_threshold=-0.05, chunk_size=10):
#     '''
#     sound is a pydub.AudioSegment
#     silence_threshold in dB
#     chunk_size in ms
#
#     iterate over chunks until you find the first one with sound
#     '''
#     trim_ms = 0 # ms
#
#     assert chunk_size > 0 # to avoid infinite loop
#     while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
#         print(sound[trim_ms:trim_ms+chunk_size].dBFS)
#         trim_ms += chunk_size
#
#     return trim_ms
#
# sound = AudioSegment.from_file('data\\audio\\50A_F_1402_6.mp3', format="mp3")
#
# start_trim = detect_leading_silence(sound)
# end_trim = detect_leading_silence(sound.reverse())
#
# duration = len(sound)
# trimmed_sound = sound[start_trim:duration-end_trim]
#
# trimmed_sound.export('out-1.mp3', format='mp3')
#
# # audio_path = 'data\\audio\\50A_F_1402_6.mp3'
