import argparse
import os
from keys import google_api_key, pixabay_api_key, pexels_api_key
from utils import Google, save, load
from crawler.crawler import Crawler
from author.author import Author
from splitter.splitter import Splitter
from tts.tts import TTS
from image.imager import Imager
from editor.editor import Editor

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("keyword", type=str, help="Four-character idiom or historical idiom")
parser.add_argument("--all", action="store_true", help="Perform all processes from the given idiom to the final video. (Equivalent to --crawler --author --tts --imager --editor)")
parser.add_argument("--crawler", action="store_true", help="Perform the Crawler process: Search for information related to the idiom")
parser.add_argument("--author", action="store_true", help="Perform the Author process: Write a script based on the information")
parser.add_argument("--tts", action="store_true", help="Perform the TTS process: Generate voice audio from the script")
parser.add_argument("--imager", action="store_true", help="Perform the Imager process: Search/create images/videos matching the script (Equivalent to --imager-parser --image-constructor --imager-story --imager-generator)")
parser.add_argument("--imager-parser", action="store_true", help="Perform the parser process within Imager: Search for images/videos matching the script")
parser.add_argument("--imager-constructor", action="store_true", help="Perform the constructor process within Imager: Create Chinese character images matching the script")
parser.add_argument("--imager-story", action="store_true", help="Generate photo descriptions for the generator process within Imager")
parser.add_argument("--imager-generator", action="store_true", help="Perform the generator process within Imager: Generate images matching the script")
parser.add_argument("--editor", action="store_true", help="Perform the Editor process: Final video editing")
parser.add_argument("--gpt-model", type=str, choices=["gpt-3.5-turbo"], default="gpt-3.5-turbo", help="ChatGPT model")
parser.add_argument("--gpt-temp", type=float, default=0.7, help="ChatGPT model creativity (0.0 ~ 1.0)")
#parser.add_argument("--sd-model", type=str, choices=["CompVis/stable-diffusion-v1-4", "runwayml/stable-diffusion-v1-5", "stabilityai/stable-diffusion-2-1"], default="CompVis/stable-diffusion-v1-4", help="Stable Diffusion model")
parser.add_argument("--sd-model", type=str, choices=["stabilityai/stable-diffusion-xl-base-1.0"], default="stabilityai/stable-diffusion-xl-base-1.0", help="Stable Diffusion model")
parser.add_argument("--sd-seed", type=int, default=-1, help="Stable Diffusion seed value (-1 for random seed)")
parser.add_argument("--width", type=int, default=1080, help="Video width")
parser.add_argument("--height", type=int, default=1920, help="Video height")
parser.add_argument("--chalkboard", type=str, default="background.png", help="Background for the idiom introduction scene. It is recommended to use the default value.")
parser.add_argument("--font", type=str, default="NanumGothicExtraBold.ttf", help="Subtitle font file location")
parser.add_argument("--text-chinese-size", type=int, default=305, help="Chinese character size in the idiom introduction scene")
parser.add_argument("--text-korean-size", type=int, default=86, help="Korean pronunciation size in the idiom introduction scene")
parser.add_argument("--text-chinese-color", type=str, default="black", help="Chinese character color in the idiom introduction scene")
parser.add_argument("--fps", type=int, default=30, help="Video FPS")
parser.add_argument("--text-size", type=int, default=86, help="Subtitle size")
parser.add_argument("--text-color", type=str, default="white", help="Subtitle color")
parser.add_argument("--text-stroke-width", type=int, default=5, help="Subtitle stroke width")
parser.add_argument("--text-stroke-color", type=str, default="black", help="Subtitle stroke color")
parser.add_argument("--bgm", type=str, default="bgm.mp3", help="Background music for the video")
parser.add_argument("--bgm-vol", type=float, default=0.2, help="Background music volume adjustment (0.0 ~ 1.0)")
args = parser.parse_args()

if __name__ == "__main__":
  # make output directory
  dirpath = os.path.join("video_outputs", args.keyword)
  os.makedirs(dirpath, exist_ok=True)

  # load data
  data, scripts, speakers, scenes, story = load(dirpath)

  # ChatGPT model
  gpt = ChatGPT(
    openai_api_key=openai_api_key,
    model=args.gpt_model,
    temperature=args.gpt_temp
  )
  
  if args.all or args.crawler:
    # crawl data about the keyword
    crawler = Crawler()
    data = crawler.crawl(args.keyword)
    save(dirpath, data, scripts, speakers, scenes, story)
  
  if args.all or args.author:
    try:
      # generate script for video
      author = Author(gpt)
      scripts = author.write_script(data)
    except AssertionError:
      print("Can't run Author: Make sure to run: Crawler")
    finally:
      save(dirpath, data, scripts, speakers, scenes, story)

    try:
      # split script
      splitter = Splitter()
      speakers, scenes = splitter.split(scripts)
    except AssertionError:
      print("Can't run Splitter: Make sure to run: Crawler, Author")
    finally:
      save(dirpath, data, scripts, speakers, scenes, story)

  if args.all or args.tts:
    try:
      # generate audio using TTS
      tts = TTS(speakers)
      scenes = tts.read_script(scenes, dirpath)
    except AssertionError:
      print("Can't run TTS: Make sure to run: Crawler, Author, Splitter")
    finally:
      save(dirpath, data, scripts, speakers, scenes, story)
  
  if args.all or args.imager or args.imager_parser or args.imager_constructor or args.imager_story or args.imager_generator:
    try:
      # instance of Imager
      imager = Imager(
        gpt_model=gpt,
        pexels_api_key=pexels_api_key,
        pixabay_api_key=pixabay_api_key,
        target_resolution=(args.width, args.height),
        chalkboard=args.chalkboard,
        font=args.font,
        text_chinese_size=args.text_chinese_size,
        text_korean_size=args.text_korean_size,
        text_chinese_color=args.text_chinese_color,
        sd_model=args.sd_model
      )
    except AssertionError:
      print("Can't run Imager: Make sure to run: Crawler, Author, Splitter")

  if args.all or args.imager or args.imager_parser:
    try:
      # parse images/videos for intro and outro
      scenes = imager.parse(
        scenes=scenes,
        dirpath=dirpath
      )
    except AssertionError:
      print("Can't run Imager-parser: Make sure to run: Crawler, Author, Splitter")
    finally:
      save(dirpath, data, scripts, speakers, scenes, story)
  
  if args.all or args.imager or args.imager_constructor:
    try:
      # construct hanja image
      scenes = imager.construct(
        data=data,
        scenes=scenes,
        dirpath=dirpath
      )
    except AssertionError:
      print("Can't run Imager-constructor: Make sure to run: Crawler, Author, Splitter")
    finally:
      save(dirpath, data, scripts, speakers, scenes, story)
  
  if args.all or args.imager or args.imager_story:
    try:
      # generate story
      story = imager.get_story(
        speakers=speakers,
        scenes=scenes
      )
    except AssertionError:
      print("Can't run Imager-story: Make sure to run: Crawler, Author, Splitter")
    finally:
      save(dirpath, data, scripts, speakers, scenes, story)
  
  if args.all or args.imager or args.imager_generator:
    try:
      # generate images for story
      scenes = imager.generate(
        scenes=scenes,
        story=story,
        dirpath=dirpath,
        seed=args.sd_seed if args.sd_seed > -1 else None
      )
    except AssertionError:
      print("Can't run Imager-generator: Make sure to run: Crawler, Author, Splitter, Imager-story")
    finally:
      save(dirpath, data, scripts, speakers, scenes, story)
  
  if args.all or args.editor:
    try:
      # generate final video
      editor = Editor(
        target_resolution=(args.width, args.height), 
        fps=args.fps, 
        font=args.font, 
        text_size=args.text_size, 
        text_color=args.text_color, 
        text_stroke_width=args.text_stroke_width, 
        text_stroke_color=args.text_stroke_color
      )
      video_name = editor.edit_video(
        scenes=scenes, 
        dirpath=dirpath,
        bgm=args.bgm,
        bgm_vol=args.bgm_vol
      )
    except AssertionError:
      print("Can't run Editor: Make sure to run: Crawler, Author, Splitter, TTS, Imager")
    finally:
      save(dirpath, data, scripts, speakers, scenes, story)
