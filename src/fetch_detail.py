import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from diskcache import Cache

# Constants
BASE_URL = "https://store.steampowered.com/app/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}
cache = Cache("./cache")


def extract_system_requirements(soup):
    requirements = {"Minimum": None, "Recommended": None}
    sys_req_section = soup.find("div", class_="game_area_sys_req_full")
    if sys_req_section:
        for p in sys_req_section.find_all("p"):
            strong_tag = p.find("strong")
            if strong_tag:
                text = strong_tag.text.strip().lower()
                if "minimum" in text:
                    requirements["Minimum"] = p.text.replace("Minimum: ", "").strip()
                elif "recommended" in text:
                    requirements["Recommended"] = p.text.replace("Recommended: ", "").strip()
    return requirements


def extract_developer_info(soup):
    dev_row = soup.find("div", class_="dev_row")
    if dev_row:
        developer_tag = dev_row.find("a")
        if developer_tag:
            return {
                "name": developer_tag.text.strip(),
                "link": developer_tag.get("href"),
            }
    return {"name": None, "link": None}


def extract_media_links(soup):
    media = []
    highlight_ctn = soup.find("div", class_="highlight_ctn")
    if highlight_ctn:
        for video in highlight_ctn.find_all("div", class_="highlight_player_item highlight_movie"):
            video_link = video.get("data-mp4-hd-source") or video.get("data-mp4-source")
            image_link = video.get("data-poster")
            if video_link and image_link:
                media.append({"type": "video", "video_link": video_link, "image_link": image_link})

        for screenshot in highlight_ctn.find_all("div", class_="highlight_player_item highlight_screenshot"):
            screenshot_link = screenshot.find("a", class_="highlight_screenshot_link")
            if screenshot_link and screenshot_link.get("href"):
                media.append({"type": "screenshot", "image_link": screenshot_link["href"]})
    return media


def extract_website_link(soup):
    website_tag = soup.find("a", class_="linkbar")
    return website_tag.get("href") if website_tag else None


def scrape_game_details(app_id):
    if app_id in cache:
        return cache[app_id]

    url = f"{BASE_URL}{app_id}/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch details for app_id {app_id}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    try:
        name = soup.find("div", class_="apphub_AppName").text.strip()
        detailed_description = soup.find("div", id="game_area_description").decode_contents()
        website = extract_website_link(soup)
        developer_info = extract_developer_info(soup)
        requirements = extract_system_requirements(soup)
        media = extract_media_links(soup)

        data = {
            "id": app_id,
            "name": name,
            "developer_name": developer_info["name"],
            "developer_link": developer_info["link"],
            "detailed_description": detailed_description,
            "website": website,
            "requirements": requirements,
            "media": media,
        }

        cache[app_id] = data
        return data

    except AttributeError as e:
        print(f"Error parsing details for app_id {app_id}: {e}")
        return None

