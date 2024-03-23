# Speech2Shorts

Record your speech and put the video&music together,

Make and upload shorts video at once!

## Dependencies

openai: using OpenAI API models for generating title and subtitle of the video.

moviepy: generating video(with ffmpeg, opencv2 and [imagemagick](https://imagemagick.org/index.php)).

youtube_upload: uploading youtube video.

Windows user should install imagemagick with almost all options on.

## How it works

1. Reading all files in input folder, and perform selection.

    ('rec' means recorded speech, 'bgm' means music, and other video means the background video)

2. Generate subtitle text from recorded speech, if needed. (OpenAI STT)

    (Once generated, it is saved as an editable 'subtitle.txt' file in source folder)

3. Generate title for the video from the subtitle text, if needed. (OpenAI GPT)

    (Also saved in the first line of 'subtitle.txt' file in source folder)

4. Generate video from all inputs. (moviepy)

5. Upload the video as a shorts, if needed. (youtube_upload)

   (You can take time for tasting the video or cancel the upload)

   (The uploaded video is often automatically set private video)

