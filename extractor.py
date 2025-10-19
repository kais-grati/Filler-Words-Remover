from moviepy.editor import VideoFileClip
import whisper
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip, concatenate_videoclips
import os

def run_whisper(file_path, device, model):

    ROOT_DIR = os.getcwd()
    video = VideoFileClip(file_path)
    video.audio.write_audiofile(os.path.join(ROOT_DIR, "cache.wav"))
    audio = whisper.load_audio(os.path.join(ROOT_DIR, "cache.wav"))

    model = whisper.load_model(name=model, device=device)

    result = model.transcribe(audio, initial_prompt="Please transcribe the audio exactly as spoken, including all filler words and verbal hesitations such as 'uh,' 'um,' 'er,' 'ah,' 'like,' 'you know,' 'so,' 'well,' and similar expressions. Do not remove or clean up these natural speech patterns. Preserve all pauses, repetitions, and conversational elements to maintain an accurate representation of the original speech.", word_timestamps=True, language='en', fp16=False)

    # with open("test.json", "r") as file:
    #     result = json.load(file)

    words = []
    
    for segment in result['segments']:
        for word_info in segment['words']:
            words.append(word_info['word'])

    print(words, result, sep="\n\n\n")
    return (words, result)

def exporter(unwanted_words, result, video_path):

    ROOT_DIR = os.getcwd()
    split_times = []
    final_end_time = result["segments"][-1]["end"]


    for i in range(len(unwanted_words)):
        if i == 0:
            start = 0
            end = unwanted_words[i][0]
        else:
            start = unwanted_words[i-1][1]
            end = unwanted_words[i][0]  
            unwanted_words[i]
            
        split_times.append([start, end])
    split_times.append([unwanted_words[-1][1], final_end_time])

    for i in range(len(split_times)):
        start_time = split_times[i][0]
        end_time = split_times[i][1]
        ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=ROOT_DIR+"/cutvid"+str(i)+".mp4")

    clips=[]
    for i in range(len(split_times)):
        clip = ROOT_DIR+"/cutvid"+str(i)+".mp4"
        clips = clips + [VideoFileClip(clip)]


    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(os.path.join(ROOT_DIR, "final.mp4"))