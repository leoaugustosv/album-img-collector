from utils.libs.selenium import *
from utils.libs.general import *
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import requests, urllib.parse


def get_sc_client_id(browser=None, url="https://soundcloud.com/"):
    if not browser:
        browser = init_browser()
        
    browser.get(url)
    try:
        elem = WebDriverWait(browser, 30).until(
        EC.presence_of_element_located((By.ID, "g_id_intermediate_iframe"))
        )
        html_content = browser.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        client_id = soup.find(id="g_id_intermediate_iframe").get("data-src").split("=", maxsplit=1)[1].split("&", maxsplit=1)[0]
        print(f"CLIENT_ID: {client_id}")
    except Exception as e:
        client_id = None
    return client_id


def get_request_body(url):
    body = ""
    max_tries = 8
    counter = 1

    while (not body or body == '{}') and counter <= max_tries:
        print(f"FAIL: Failed to get search results. Trying again... ({counter}/{max_tries})")
        time.sleep(2)
        body = requests.get(url).text
        counter += 1
    
    return body



def search_soundcloud(browser, client_id, search_str, limit:int = 10, offset:int = 0):
    print(f"START: Searching SoundCloud for cover art of the song: {search_str}")

    max_tries = 8
    counter = 1
    while not client_id and counter <= max_tries:
        print(f"FAIL: Failed to get SoundCloud client_id. Trying again... ({counter}/{max_tries})")
        time.sleep(2)
        client_id = get_sc_client_id(browser)
        counter += 1
    else:
        tracks_info = []

        if not client_id:
            print("FAIL: Unable to get SoundCloud client_id. Try again in a few seconds.")
            return tracks_info
        else:
            search_str = urllib.parse.quote(search_str)
            api_url = f"https://api-v2.soundcloud.com/search/tracks?q={search_str}&client_id={client_id}&limit={limit}&offset={offset}"
            body = get_request_body(api_url)

            if (not body or body == '{}'):
                print("FAIL: Unable to get search results. Try again in a few seconds.")
                return tracks_info
            else:
                try:
                    collection_list = json.loads(body).get("collection")

                    pos_counter = 1
                    for song in collection_list:
                        track = {}
                        track["position"] = pos_counter 
                        track["name"] = song["title"]
                        track["url"] = song["permalink_url"]
                        track["cover_img"] = song["artwork_url"].replace("large", "original")
                        track["date"] = song["created_at"]
                        track["description"] = song["description"]
                        track["username"] = song["user"]["username"]

                        
                        tracks_info.append(track)
                        pos_counter += 1
                except Exception as e:
                    print(f"ERROR: {e}\n\n\nSong: {song}\n\n")
                    

            return tracks_info




def soundcloud_main(browser, path, file, use_id3_tags = False):
    
    client_id = get_sc_client_id(browser)

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
        query_return = search_soundcloud(browser, client_id=client_id, search_str=search_str)
        print(f"SUGGESTED COVER ARTS --- {search_str}:\n")
        
        for track in query_return:
            print(f'{track.get("position")}: {track.get("cover_img")} --- SC_USER:{track.get("username")} | SC_NAME:{track.get("name")}')
        print(f"\n")
    except Exception as e:
        query_return = []
        print({e})

    return query_return