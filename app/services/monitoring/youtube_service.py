import os
import requests
from typing import List, Dict
from googleapiclient.discovery import build
from app.core.config import settings
import re
from app.services.monitoring.utils import get_start_date
from googleapiclient.discovery import build
from app.core.config import settings

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

def build_youtube_service():
    return build("youtube", "v3", developerKey=settings.youtube_api_key)

def extract_hashtags(text):
    return re.findall(r"#\w+", text)

def calculate_engagement_rate(channel_id: str, duration: str = "30d"):
    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
    start_date = get_start_date(duration)

    # Step 1: Get uploads playlist ID
    ch_resp = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()

    uploads_playlist = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Step 2: Get recent video IDs from playlist after start_date
    video_ids = []
    next_page_token = None
    while True:
        playlist_resp = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in playlist_resp["items"]:
            published = item["snippet"]["publishedAt"]
            if published >= start_date:
                video_ids.append(item["snippet"]["resourceId"]["videoId"])

        next_page_token = playlist_resp.get("nextPageToken")
        if not next_page_token:
            break

    # Step 3: Calculate engagement per video
    engagement_rates = []
    total_engagement = 0
    count_with_views = 0

    for i in range(0, len(video_ids), 50):
        stats_resp = youtube.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids[i:i+50])
        ).execute()

        for video in stats_resp["items"]:
            stats = video.get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))

            if views > 0:
                rate = round(((likes + comments) / views) * 100, 2)
                engagement_rates.append({
                    "video_id": video["id"],
                    "title": video["snippet"]["title"],
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagement_rate": rate
                })
                total_engagement += rate
                count_with_views += 1

    avg_rate = round(total_engagement / count_with_views, 2) if count_with_views else 0

    return {
        "channel_id": channel_id,
        "video_count": count_with_views,
        "average_engagement_rate": avg_rate,
        "videos": engagement_rates
    }

def get_channel_id_by_username(username: str) -> str:
    try:
        youtube = build_youtube_service()
        
        # Clean the username - remove @ if present
        clean_username = username.strip().lstrip('@')
        
        # First try: forUsername (legacy usernames)
        response = youtube.channels().list(
            part="id",
            forUsername=clean_username
        ).execute()

        # Check if response has items and handle API errors
        if "items" not in response:
            raise ValueError(f"YouTube API error: {response.get('error', {}).get('message', 'Unknown error')}")

        if response["items"]:
            return response["items"][0]["id"]
        
        # Second try: Search for the channel by name/handle
        search_response = youtube.search().list(
            part="snippet",
            q=clean_username,
            type="channel",
            maxResults=10
        ).execute()

        if "items" not in search_response:
            raise ValueError(f"YouTube API error: {search_response.get('error', {}).get('message', 'Unknown error')}")

        if search_response["items"]:
            # Look for exact matches first
            for item in search_response["items"]:
                channel_title = item["snippet"]["title"].lower()
                channel_custom_url = item["snippet"].get("customUrl", "").lower()
                
                # Check for exact match in title or custom URL
                if (clean_username.lower() == channel_title or 
                    clean_username.lower() == channel_custom_url.lstrip('@') or
                    f"@{clean_username.lower()}" == channel_custom_url):
                    return item["snippet"]["channelId"]
            
            # If no exact match, return the first result
            return search_response["items"][0]["snippet"]["channelId"]
        
        # Third try: Search with @ prefix if not already present
        if not username.startswith('@'):
            search_with_at = youtube.search().list(
                part="snippet",
                q=f"@{clean_username}",
                type="channel",
                maxResults=5
            ).execute()
            
            if "items" in search_with_at and search_with_at["items"]:
                return search_with_at["items"][0]["snippet"]["channelId"]
        
        raise ValueError(f"Channel not found for: {username}")
        
    except Exception as e:
        if "quota" in str(e).lower():
            raise ValueError("YouTube API quota exceeded. Please check your API settings.")
        elif "key" in str(e).lower() or "credential" in str(e).lower():
            raise ValueError("YouTube API key not configured or invalid. Please check your .env file.")
        else:
            raise ValueError(f"Failed to find channel: {str(e)}")

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
    try:
        key = os.getenv("YOUTUBE_API_KEY")
        base = YOUTUBE_API_BASE

        if not key:
            raise ValueError("YouTube API key not configured. Please add YOUTUBE_API_KEY to your .env file.")

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
        ch_data = ch_response.json()
        
        # Check if response has items and handle API errors
        if "items" not in ch_data:
            error_msg = ch_data.get("error", {}).get("message", "Unknown error")
            raise ValueError(f"YouTube API error: {error_msg}")
        
        if not ch_data["items"]:
            raise ValueError("Channel not found")
            
        ch = ch_data["items"][0]

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
        vids_data = vids_response.json()
        
        # Check if response has items and handle API errors
        if "items" not in vids_data:
            error_msg = vids_data.get("error", {}).get("message", "Unknown error")
            raise ValueError(f"YouTube API error: {error_msg}")
            
        videos = vids_data["items"]

        video_ids = [v["snippet"]["resourceId"]["videoId"] for v in videos]

        if not video_ids:
            # No videos found, return channel info with empty videos list
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
                "recent_videos": []
            }

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
        stats_data_response = stats_response.json()
        
        # Check if response has items and handle API errors
        if "items" not in stats_data_response:
            error_msg = stats_data_response.get("error", {}).get("message", "Unknown error")
            raise ValueError(f"YouTube API error: {error_msg}")
            
        stats_data = stats_data_response["items"]

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
    except requests.exceptions.RequestException as e:
        if "quota" in str(e).lower():
            raise ValueError("YouTube API quota exceeded. Please check your API settings.")
        elif "key" in str(e).lower() or "credential" in str(e).lower():
            raise ValueError("YouTube API key not configured or invalid. Please check your .env file.")
        else:
            raise ValueError(f"Failed to fetch channel overview: {str(e)}")
    except Exception as e:
        if "quota" in str(e).lower():
            raise ValueError("YouTube API quota exceeded. Please check your API settings.")
        elif "key" in str(e).lower() or "credential" in str(e).lower():
            raise ValueError("YouTube API key not configured or invalid. Please check your .env file.")
        else:
            raise ValueError(f"Failed to fetch channel overview: {str(e)}")

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
