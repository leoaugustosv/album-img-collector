from utils.libs.selenium import *
from utils.libs.general import *
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re, json
import requests, urllib.parse




def beatport_main(browser, path, file, use_id3_tags = False):

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
        query_return = search_beatport(browser, search_str=search_str)
        print(f"SUGGESTED COVER ARTS --- {search_str}:\n")
        
        for track in query_return:
            print(f'{track.get("position")}: {track.get("cover_img")} --- ARTIST:{track.get("username")} | TITLE:{track.get("name")}')
        print(f"\n")
    except Exception as e:
        query_return = []
        print({e})

    return query_return



def search_beatport(browser, search_str, limit:int = 10, offset:int = 0):
    
    parsed_search_str = urllib.parse.quote(search_str)
    url = f"https://www.beatport.com/search?q={parsed_search_str}"

    print(f"START: Searching Beatport for cover art... KEY: {parsed_search_str}")
    
    browser.get(url)
    user_agent = browser.execute_script("return navigator.userAgent;")


    time.sleep(1)

    page_html = browser.page_source
    page_soup = BeautifulSoup(page_html, "html.parser")

    script_next_data = (
        page_soup.find(
            'script', {'id': '__NEXT_DATA__'}
        )
        .text
        .encode().decode("unicode_escape")
        .encode("utf-8").decode("utf-8", "ignore")
    )

    try:
        build_id = script_next_data.split('"buildId":"')[-1].split('"')[0]
    except Exception as e:
        print({e})
        build_id = ''

    query_endpoint = f"https://www.beatport.com/_next/data/{build_id}/en/search.json?q={parsed_search_str}"
    print(query_endpoint)
    headers = {
        "Host": "www.beatport.com",
        "User-Agent": user_agent
    }

    response = requests.get(query_endpoint, headers=headers)

    dict_response = json.loads(response.text)

    list_songs_from_response = (
        dict_response
            .get('pageProps',{})
            .get('dehydratedState', {})
            .get('queries', {})
            [0]
            .get('state', {})
            .get('data', {})
            .get('tracks', {})
            .get('data', {})
    )[:limit]

    pos_counter = 1
    results = []

    for song in list_songs_from_response:

        name = song.get('track_name')

        artist = (
            ", ".join(a.get("artist_name") for a in song.get("artists"))
        )

        track_id = song.get('track_id')

        url = (
            f'https://www.beatport.com/track/{urllib.parse.quote(name.lower().replace(" ","-"))}/{track_id}'
        )

        cover_img = (
            song
            .get('release')
            .get('release_image_uri')
        )

        album = (
            song
            .get('release')
            .get('release_name')
        )

        date = song.get('release_date')[:4]

        songs_dict = {
            "position" : pos_counter,
            "name" : name,
            "url" : url,
            "cover_img" : cover_img,
            "date" : date,
            "description" : album,
            "username" : artist
        }
        results.append(songs_dict)
        pos_counter += 1

    return results
        