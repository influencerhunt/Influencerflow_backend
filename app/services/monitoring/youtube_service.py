import os
import requests
from typing import List, Dict
from googleapiclient.discovery import build
from app.core.config import settings
import re

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

def build_youtube_service():
    return build("youtube", "v3", developerKey=settings.youtube_api_key)

def extract_hashtags(text):
    return re.findall(r"#\w+", text)

def get_channel_id_by_username(username: str) -> str:
    youtube = build_youtube_service()
    response = youtube.channels().list(
        part="id",
        forUsername=username
    ).execute()

    if response["items"]:
        return response["items"][0]["id"]
    else:
        # Try resolving from custom handle URL (e.g., youtube.com/@chrome)
        search_response = youtube.search().list(
            part="snippet",
            q=username,
            type="channel",
            maxResults=1
        ).execute()

        if search_response["items"]:
            return search_response["items"][0]["snippet"]["channelId"]
        else:
            raise ValueError("Channel ID not found for username/handle")

def fetch_video_comments(video_id: str, max_results: int = 20):
    youtube = build_youtube_service()

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        textFormat="plainText"
    )
    response = request.execute()

    comments = []
    for item in response.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        comments.append({
            "author": snippet["authorDisplayName"],
            "text": snippet["textDisplay"],
            "likes": snippet["likeCount"],
            "published_at": snippet["publishedAt"]
        })

    return comments


def get_video_details_by_id(video_id: str):
    youtube = build_youtube_service()
    response = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    ).execute()

    if not response["items"]:
        return {"error": "Video not found"}

    video = response["items"][0]
    snippet = video["snippet"]
    stats = video["statistics"]
    
    title = snippet["title"]
    description = snippet["description"]
    hashtags = extract_hashtags(title + " " + description)

    return {
        "video_id": video_id,
        "title": title,
        "description": description,
        "published_at": snippet["publishedAt"],
        "thumbnail": snippet["thumbnails"]["default"]["url"],
        "hashtags": hashtags,
        "metrics": {
            "views": stats.get("viewCount"),
            "likes": stats.get("likeCount"),
            "comments": stats.get("commentCount")
        }
    }

def get_video_metrics_from_playlist(channel_id: str, max_results: int = 5):
    # Step 1: Build the YouTube API service
    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)

    # Step 2: Get the uploads playlist ID for the channel
    channel_response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()

    uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Step 3: Fetch recent videos from the uploads playlist
    playlist_response = youtube.playlistItems().list(
        playlistId=uploads_playlist_id,
        part="snippet",
        maxResults=max_results
    ).execute()

    video_items = playlist_response.get("items", [])
    video_ids = [item["snippet"]["resourceId"]["videoId"] for item in video_items]

    # Step 4: Fetch detailed metrics for the videos
    stats_response = youtube.videos().list(
        part="statistics,snippet,contentDetails",
        id=",".join(video_ids)
    ).execute()

    # Step 5: Combine and format the result
    videos = []
    for item in stats_response["items"]:
        videos.append({
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "published_at": item["snippet"]["publishedAt"],
            "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
            "duration": item["contentDetails"]["duration"],
            "view_count": item["statistics"].get("viewCount"),
            "like_count": item["statistics"].get("likeCount"),
            "comment_count": item["statistics"].get("commentCount")
        })

    return {"videos": videos}


def fetch_recent_youtube_videos(channel_id: str) -> List[Dict]:
    # Step 1: Get the uploads playlist ID
    playlist_resp = requests.get(
        f"{YOUTUBE_API_BASE}/channels",
        params={
            "part": "contentDetails",
            "id": channel_id,
            "key": YOUTUBE_API_KEY
        }
    )
    playlist_resp.raise_for_status()
    uploads_playlist_id = playlist_resp.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Step 2: Get videos from the playlist
    videos_resp = requests.get(
        f"{YOUTUBE_API_BASE}/playlistItems",
        params={
            "part": "snippet",
            "playlistId": uploads_playlist_id,
            "maxResults": 5,
            "key": YOUTUBE_API_KEY
        }
    )
    videos_resp.raise_for_status()

    results = []
    for item in videos_resp.json()["items"]:
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        description = item["snippet"]["description"]
        published_at = item["snippet"]["publishedAt"]
        results.append({
            "title": title,
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "published_at": published_at,
            "description": description[:200]  # preview
        })

    return results

def fetch_channel_overview(channel_id: str) -> Dict:
    key = os.getenv("YOUTUBE_API_KEY")
    base = YOUTUBE_API_BASE

    # 1. Channel info
    ch_response = requests.get(
        f"{base}/channels",
        params={
            "part": "snippet,statistics,contentDetails",
            "id": channel_id,
            "key": key
        }
    )
    ch_response.raise_for_status()
    ch = ch_response.json()["items"][0]

    uploads_playlist_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]

    # 2. Latest videos (5)
    vids_response = requests.get(
        f"{base}/playlistItems",
        params={
            "part": "snippet",
            "playlistId": uploads_playlist_id,
            "maxResults": 5,
            "key": key
        }
    )
    vids_response.raise_for_status()
    videos = vids_response.json()["items"]

    video_ids = [v["snippet"]["resourceId"]["videoId"] for v in videos]

    # 3. Stats for those videos
    stats_response = requests.get(
        f"{base}/videos",
        params={
            "part": "statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": key
        }
    )
    stats_response.raise_for_status()
    stats_data = stats_response.json()["items"]

    # Return combined info
    return {
        "channel": {
            "id": ch["id"],
            "title": ch["snippet"]["title"],
            "description": ch["snippet"]["description"],
            "published_at": ch["snippet"]["publishedAt"],
            "subscriber_count": ch["statistics"].get("subscriberCount"),
            "total_views": ch["statistics"].get("viewCount"),
            "video_count": ch["statistics"].get("videoCount")
        },
        "recent_videos": [
            {
                "video_id": vid.get("id"),
                "url": f"https://youtube.com/watch?v={vid.get('id')}",
                "title": vid.get("snippet", {}).get("title", ""),
                "published_at": vid.get("snippet", {}).get("publishedAt", ""),
                "views": vid.get("statistics", {}).get("viewCount", "0"),
                "likes": vid.get("statistics", {}).get("likeCount", "0"),
                "comments": vid.get("statistics", {}).get("commentCount", "0"),
                "duration": vid.get("contentDetails", {}).get("duration", "")
            }
            for vid in stats_data if "snippet" in vid and "statistics" in vid and "contentDetails" in vid
        ]

    }
    # youtube_service.py

def fetch_videos_from_playlist(playlist_id, youtube, max_results=5):
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        video_data = {
            "video_id": snippet.get("resourceId", {}).get("videoId"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "published_at": snippet.get("publishedAt"),
            "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url")
        }
        videos.append(video_data)

    return videos

def get_uploads_playlist_id(channel_id: str, youtube):
    response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
