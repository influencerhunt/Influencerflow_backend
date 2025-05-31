from fastapi import APIRouter, Request, HTTPException
from app.services.monitoring.schemas import MetricsRequest, MetricsResponse, PostMetrics
from app.services.monitoring.youtube_service import fetch_recent_youtube_videos
from app.services.monitoring.youtube_service import fetch_channel_overview
from fastapi import APIRouter
from app.services.monitoring.youtube_service import get_uploads_playlist_id, build_youtube_service, fetch_videos_from_playlist, get_video_metrics_from_playlist, get_video_details_by_id, fetch_video_comments, get_channel_id_by_username
from googleapiclient.discovery import build
from fastapi import Query
import re
from app.services.monitoring.youtube_service import get_video_details_by_id

router = APIRouter()

@router.get("/youtube/metrics")
def youtube_video_metrics(channel_id: str):
    return get_video_metrics_from_playlist(channel_id)

@router.get("/youtube/stats-by-name")
def youtube_stats_by_name(channel_name: str):
    try:
        channel_id = get_channel_id_by_username(channel_name)
        return fetch_channel_overview(channel_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/youtube/comments")
def get_video_comments(video_id: str, max_results: int = 10):
    try:
        return {"comments": fetch_video_comments(video_id, max_results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/youtube/video-details")
def get_video_details(video_url: str = Query(..., description="Full YouTube video URL")):
    # Extract video ID from URL
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]+)", video_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid YouTube video URL.")
    
    video_id = match.group(1)
    return get_video_details_by_id(video_id)

@router.get("/youtube/videos")
def fetch_uploaded_videos(channel_id: str):
    youtube = build_youtube_service()
    playlist_id = get_uploads_playlist_id(channel_id, youtube)
    videos = fetch_videos_from_playlist(playlist_id, youtube)
    return {"videos": videos}

@router.get("/youtube/playlist-id")
def fetch_playlist_id(channel_id: str):
    youtube = build_youtube_service()
    playlist_id = get_uploads_playlist_id(channel_id, youtube)
    return {"playlist_id": playlist_id}


@router.get("/youtube/stats")
def youtube_channel_stats(channel_id: str):
    return fetch_channel_overview(channel_id)


@router.get("/youtube/test")
def test_youtube(channel_id: str):
    return fetch_recent_youtube_videos(channel_id)

