
from io import BytesIO
import json
import os
import mutagen as mtg
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
import requests
from PIL import Image, ImageTk
from utils.params.params import *

def get_audio_files_from_path(path:str, supported_audio_types:list):
    list_directory = os.listdir(path)
    files = [f for f in list_directory if os.path.isfile(os.path.join(path, f))]
    audio_files = [x for x in files if x.split(".")[-1] in supported_audio_types]
    return audio_files

def get_ID3_tags_info(filepath):

    audio_file = mtg.File(filepath)

    name = audio_file.get("TIT2")
    artist = audio_file.get("TPE1")
    album_name = audio_file.get("TALB")
    img_info = None
    img_data = None

    if audio_file.tags:
        for tag in audio_file.tags.values():
            if isinstance(tag, APIC):
                img_info = f'{tag.mime} - {tag.type}'
                img_data = tag.data
                break
    return name, artist, album_name, img_info, img_data

def delete_id3_cover(audiopath):
    try:
        audio_id3 = ID3(audiopath)
        audio_id3.delall("APIC")
        audio_id3.save(audiopath)
    except Exception as e:
        print(f"{e}")



def get_mimetype_from_url(img_url):
    extension_from_url = img_url.split(".")[-1][:4]
    detected_mime = ""
    if extension_from_url not in SUPPORTED_IMG_TYPES:
        detected_mime = requests.get(img_url).headers.get('Content-Type', {})
        if not detected_mime:
            detected_mime = ""
    else:
        if extension_from_url == "png":
            detected_mime = "image/png"
        elif extension_from_url in ("jpg","jpeg"):
            detected_mime = "image/jpeg"
        
    return detected_mime



def add_image_to_id3(img_url, audio_path):
    detected_mime = get_mimetype_from_url(img_url)
    if not detected_mime:
        print(f"ERROR: {img_url} - unable to determine file format/mimetype.")
        return
    
    try:
        img = response_to_img(img_url)
        try:
            audio_id3 = ID3(audio_path)
            audio_id3.delall("APIC")
        except:
            audio_id3 = ID3()

        audio_id3.add(
                    APIC(
                        encoding=3, # utf-8
                        mime=detected_mime,
                        type=3, # Front cover
                        desc='FRONT_COVER',
                        data=img.read()
                    )
                )
        audio_id3.save(audio_path, v2_version=3)
        print(f"New cover added to {audio_path} succesfully.")
    except Exception as e:
        print(f"ERROR: Unable to update cover - {e}")



def response_to_img(url):
    response = requests.get(url)
    img = BytesIO(response.content)
    return img

def prompt_user_opt(prompt):
    option = ""
    while option.upper() not in ("Y","N"):
        option = input(prompt).strip()
    return option.upper()

def center_crop_image(img):
    width, height = img.size
    new_width, new_height = height, height

    left = (width - new_width) // 2
    top = (height - new_height) // 2
    right = left + new_width
    bottom = top + new_height

    cropped_img = img.crop((left, top, right, bottom))
    return cropped_img


