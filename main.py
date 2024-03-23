import os

from openai import OpenAI
import moviepy.editor as mpy
import moviepy.video.fx.all as vfx
from youtube_upload.client import YoutubeUploader

# get an audio file
# get a subtitle stream from that audio file
# get a video for short-form
# make a video with subtitle

VERSION = "1.01"

TIME_LENGTH_MAX = 1.0
TEXT_LENGTH_MAX = 15

VID_CODEC = "libx264"
VID_FPS = 30

GOOGLE_CLIENT_SECRETS_FILE = "source/google_client_secret.json"
OPENAI_CLIENT_SECRETS_FILE = "source/openai_client_secret.txt"

INPUT_FOLDER = 'input/'
AUDIO_FILE = 'input/Rec.m4a'
VIDEO_FILE = 'input/eve1.mp4'
MUSIC_FILE = 'input/bgm_weather.mp4'
SUBTITLE_FILE = 'source/subtitle.txt'

RESULT_FILE = 'result.mp4'


if __name__ == '__main__':

    do_ai = False
    do_up = False

    print(f"Starting Speech2Shorts {VERSION}")
    file_list = [file_name for file_name in os.listdir(INPUT_FOLDER)]
    for file in file_list:
        if file.find('rec') >= 0:
            AUDIO_FILE = INPUT_FOLDER + file
        elif file.find('bgm') >= 0:
            MUSIC_FILE = INPUT_FOLDER + file
        elif file[-3:] in ('mp4', 'avi'):
            VIDEO_FILE = INPUT_FOLDER + file

    print(file_list, "-> Selection finished.")
    print("VIDEO: ", VIDEO_FILE)
    print("AUDIO: ", AUDIO_FILE)
    print("MUSIC: ", MUSIC_FILE)
    s = input('s to make a new subtitle script \nu to make upload to youtube shorts \ninsert your command: ')
    if s.find('s') >= 0:
        do_ai = True
    if s.find('u') >= 0:
        do_up = True

    if do_ai:
        print("connecting OpenAI...")
        api_key = open(OPENAI_CLIENT_SECRETS_FILE, 'r').read().strip()
        client = OpenAI(api_key=api_key)

        audio = open(AUDIO_FILE, 'rb')
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
        # print(transcription.text)

        gpt_result = client.chat.completions.create(
            model='gpt-4',
            messages=[
                {'role': 'system', 'content': 'You are a designer'},
                {'role': 'user', 'content': f'Bring me a short and compact title for a video with someone saying this: '
                                            f'\n\n\"{transcription.text}\"'}
            ]
        )
        # print(gpt_result.choices[0].message.content)
        title = gpt_result.choices[0].message.content

        with open(SUBTITLE_FILE, 'w') as subtitle_file:
            subtitle_file.write(f"{title}\n")
            for word in transcription.words:
                # print(word['word'], word['start'], word['end'])
                subtitle_file.write(f"{word['word']}\t{word['start']}\t{word['end']}\n")
        print("Script building: Done!")

    title = ""
    text = ""
    text_list = []
    with open(SUBTITLE_FILE, 'r') as subtitle_file:
        lines = subtitle_file.readlines()
        title += lines[0].strip().replace('\"', '').replace('\'', '')
        for line in lines[1:]:
            if len(line) == 0:
                continue
            word, start, end = line.split('\t')
            start, end = float(start), float(end)
            text_list.append({'word': word, 'start': start, 'end': end})
            text += word
            text += " "

    print(title)
    print(text)

    # if time overs 1.0 seconds, then do not sum the text.
    # if the length overs 15, do not sum the text.
    sub_list = [text_list[0]]
    text_list = text_list[1:]

    for text in text_list:
        word_1 = sub_list[-1]['word']
        start_1 = sub_list[-1]['start']
        end_1 = sub_list[-1]['end']

        word_2 = text['word']
        start_2 = text['start']
        end_2 = text['end']

        if (end_2 - start_1) < TIME_LENGTH_MAX and len(word_1 + ' ' + word_2) < TEXT_LENGTH_MAX:
            sub_list[-1]['word'] = word_1 + ' ' + word_2
            sub_list[-1]['end'] = end_2
        else:
            text['end'] = min(text['end'], text['start'] + TIME_LENGTH_MAX)
            sub_list.append(text)

    sub_vid_list = []
    for sub in sub_list:
        txt = mpy.TextClip(sub['word'], font='Georgia', fontsize=120, color='gray100',
                           bg_color='transparent', stroke_width=0, stroke_color='transparent') \
            .set_position(('center', 0.55), relative=True) \
            .set_start(sub['start']) \
            .set_duration(sub['end'] - sub['start']) \
            .fx(vfx.resize, lambda t: min(1, 1))
        sub_vid_list.append(txt)

    video = mpy.VideoFileClip(VIDEO_FILE).subclip(0, sub_list[-1]['end'])
    print(video.size)
    audio = mpy.AudioFileClip(AUDIO_FILE).set_duration(sub_list[-1]['end'])
    music = mpy.AudioFileClip(MUSIC_FILE).set_duration(sub_list[-1]['end']).audio_fadein(1).audio_fadeout(1)
    comp = mpy.CompositeAudioClip([audio, music])

    final_video = mpy.CompositeVideoClip([video] + sub_vid_list).set_audio(audio).set_audio(comp)

    final_video.write_videofile('result.mp4')

    #

    a = ""
    if not do_up:
        a = input("upload now?")

    if a in ('y', 'Y', 'yes') or do_up:
        uploader = YoutubeUploader(secrets_file_path=GOOGLE_CLIENT_SECRETS_FILE)
        uploader.authenticate()

        # Video options
        options = {
            "title": title,  # The video title
            "description": f"Follow for more! \n{title} by anyone",  # The video description
            "tags": ["shorts", 'EVE', 'online'] + title.split(' '),
            "categoryId": "22",
            "privacyStatus": "public",  # Video privacy. Can either be "public", "private", or "unlisted"
            "kids": False,  # Specifies if the Video if for kids or not. Defaults to False.
        }

        # upload video
        uploader.upload(RESULT_FILE, options)

