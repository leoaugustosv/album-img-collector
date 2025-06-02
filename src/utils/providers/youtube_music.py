from utils.libs.selenium import *
from utils.libs.general import *
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re, json
import requests, urllib.parse





def get_imgs_from_ids(id_list):
    img_list = []
    img = None

    max_tries = 8
    counter = 1
    for id in id_list:
        while (not img) and counter <= max_tries:
            
            if len(id) > 15:
                img = fetch_yt_thumbnail(id)
            else:
                img = fetch_ytmusic_thumbnail(id)

            if not img:
                print(f"FAIL: Failed to fetch a valid thumbnail image. Trying again... ({counter}/{max_tries})")
                time.sleep(1)
                counter += 1
        
        if not img:
            print(f"FAIL: Unable to fetch a valid thumbnail image! Skipping ID...")
        else:
            img_list.append(img)
        
    return img_list



def fetch_yt_thumbnail(video_id):
    response = requests.get(f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
    img = Image.open(BytesIO(response.content))
    if img.size == (120, 90):
        response = requests.get(f"https://img.youtube.com/vi/{video_id}/sddefault.jpg")
        img = Image.open(BytesIO(response.content))
        if img.size == (120, 90):
            img=None
    return img

def fetch_ytmusic_thumbnail(internal_id):
    response = requests.get(f"https://lh3.googleusercontent.com/{internal_id}=w1000-h1000-l90-rj")
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
    else:
        response = requests.get(f"https://lh3.googleusercontent.com/{internal_id}")
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
        else:
            img=None
    return img


def youtube_music_main(browser, path, file, use_id3_tags = False):

    print(f"--- {file} ---")
    
    filetype = file.split(".")[-1]

    if use_id3_tags:
        name, artist, album_name, img_tuple = get_ID3_tags_info(f"{path}\\{file}")
        print(f"Name: {name}")
        print(f"Artist: {artist}")
        print(f"Album: {album_name}")
        print(f"IMG Info: {img_tuple}")
        id3_tags_info = [str(x) for x in get_ID3_tags_info(f"{path}\\{file}")[:2] if x]
        search_str = " - ".join(id3_tags_info) if len(id3_tags_info) > 0 else file.replace(f".{filetype}", "")
        
    else: 
        search_str = file.replace(f".{filetype}", "")
    print(f"Search: {search_str}")
    print(f"\n")

    try:
        query_return = search_youtubemusic(browser, search_str=search_str)
        print(f"SUGGESTED COVER ARTS --- {search_str}:\n")
        
        for track in query_return:
            print(f'{track.get("position")}: {track.get("cover_img")} --- ARTIST:{track.get("username")} | TITLE:{track.get("name")}')
        print(f"\n")
    except Exception as e:
        query_return = []
        print({e})

    return query_return



def search_youtubemusic(browser, search_str, limit:int = 10, offset:int = 0):
    print(f"START: Searching Youtube Music for cover art... KEY: {search_str}")

    parsed_search_str = urllib.parse.quote(search_str)
    url = f"https://music.youtube.com/search?q={search_str}"

    browser.get(url)

    time.sleep(1)

    page_html = browser.page_source
    page_soup = BeautifulSoup(page_html, "html.parser")

    script_ytcfg = (
        page_soup.find(
            'script', string=lambda text: text and text.startswith('var ytcfg={d:function()')
        )
        .text
        .split("ytcfg.set(")[-1]
        .split(");window.ytcfg.obfuscatedData_ = [];")[0]
    )

    script_initial_data = (
        page_soup.find(
            'script', string=lambda text: text and text.startswith('try {const initialData = [];initialData.push')
        )
        .text
        .encode().decode("unicode_escape")
        .encode("utf-8").decode("utf-8")
    )

    endpoint_songs_params = (
        json.loads(
        script_initial_data
        .split('"chips":')[-1]
        .split(',"collapsedRowCount"')[0]
        )
        [0]
        .get('chipCloudChipRenderer',{})
        .get('navigationEndpoint',{})
        .get('searchEndpoint',{})
    )

    json_ytcfg = json.loads(script_ytcfg)
    client_info = json_ytcfg['INNERTUBE_CONTEXT']['client']
    headers = {
    "Host": "music.youtube.com",
    "User-Agent": client_info.get("userAgent",{}),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.7,pt-BR;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": f"https://music.youtube.com/search?q={parsed_search_str}",
    "Content-Type": "application/json",
    "X-Youtube-Bootstrap-Logged-In": "false",
    "X-Youtube-Client-Name": str(json_ytcfg['INNERTUBE_CONTEXT_CLIENT_NAME']),
    "X-Youtube-Client-Version": json_ytcfg['INNERTUBE_CLIENT_VERSION'],
    "Origin": "https://music.youtube.com",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "same-origin",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0"
    }

    rurl = 'https://music.youtube.com/youtubei/v1/search?prettyPrint=false'

    body = {
        "context": {
            "client": client_info
        },
        "query": search_str,
        "params":endpoint_songs_params["params"] # Needed for "Songs" filter
    }


    response = requests.post(rurl, headers=headers, json=body)

    dict_response = json.loads(response.text)

    list_songs_from_response = (
        dict_response
            .get('contents',{})
            .get('tabbedSearchResultsRenderer', {})
            .get('tabs', {})
            [0]
            .get('tabRenderer', {})
            .get('content', {})
            .get('sectionListRenderer', {})
            .get('contents', {})
            [-1]
            .get('musicShelfRenderer', {})
            .get('contents', {})
    )[:limit]

    pos_counter = 1
    ytm_results = []

    for song in list_songs_from_response:

        main_info = (
            song
            .get('musicResponsiveListItemRenderer',{})
            .get('flexColumns',{})
        )

        name = (
            main_info
            [0]
            .get('musicResponsiveListItemFlexColumnRenderer',{})
            .get('text',{})
            .get('runs',{})
            [0]
            .get('text',{})
        )

        artist = (
            main_info
            [1]
            .get('musicResponsiveListItemFlexColumnRenderer',{})
            .get('text',{})
            .get('runs',{})
            [0]
            .get('text',{})
        )

        url = (
            'https://music.youtube.com/watch?v='
            +
            main_info
            [0]
            .get('musicResponsiveListItemFlexColumnRenderer',{})
            .get('text',{})
            .get('runs',{})
            [0]
            .get('navigationEndpoint',{})
            .get('watchEndpoint',{})
            .get('videoId',{})
        )

        cover_img = (
            song
            .get('musicResponsiveListItemRenderer',{})
            .get('thumbnail',{})
            .get('musicThumbnailRenderer',{}) 
            .get('thumbnail',{})
            .get('thumbnails',{})
            [0]
            .get('url',{})
            .split('=')[0]
            +
            '=w1000-h1000-l90-rj'
        )

        song_length = (
            main_info
            [1]
            .get('musicResponsiveListItemFlexColumnRenderer',{})
            .get('text',{})
            .get('runs',{})
            [-1]
            .get('text',{})
        )

        yt_songs_dict = {
            "position" : pos_counter,
            "name" : name,
            "url" : url,
            "cover_img" : cover_img,
            "date" : "",
            "description" : song_length,
            "username" : artist
        }
        ytm_results.append(yt_songs_dict)
        pos_counter += 1

    return ytm_results
        