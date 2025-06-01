
from app.services.monitoring.youtube_service import (
    fetch_channel_overview,
    get_video_metrics_from_playlist,
    fetch_video_comments
)

def compute_channel_metrics(channel_id: str):
    data = fetch_channel_overview(channel_id)
    channel = data["channel"]
    videos = data["recent_videos"]

    total_views = int(channel["total_views"])
    total_videos = int(channel["video_count"])
    avg_views_per_video = total_views / total_videos if total_videos else 0

    return {
        "channel_title": channel["title"],
        "subscribers": int(channel["subscriber_count"]),
        "total_views": total_views,
        "total_videos": total_videos,
        "average_views_per_video": round(avg_views_per_video, 2)
    }

def compute_video_metrics(channel_id: str, max_results: int = 5):
    result = get_video_metrics_from_playlist(channel_id, max_results)
    videos = result["videos"]

    if not videos:
        return {}

    total_views = sum(int(v["view_count"]) for v in videos)
    total_likes = sum(int(v.get("like_count", 0)) for v in videos)
    total_comments = sum(int(v.get("comment_count", 0)) for v in videos)

    avg_views = total_views / len(videos)
    avg_likes = total_likes / len(videos)
    avg_comments = total_comments / len(videos)

    top_video = max(videos, key=lambda x: int(x["view_count"]))

    return {
        "total_videos_analyzed": len(videos),
        "average_views": round(avg_views, 2),
        "average_likes": round(avg_likes, 2),
        "average_comments": round(avg_comments, 2),
        "top_video": {
            "title": top_video["title"],
            "video_id": top_video["video_id"],
            "views": top_video["view_count"],
            "url": f"https://youtube.com/watch?v={top_video['video_id']}"
        }
    }

def compute_comment_insights(video_id: str):
    comments = fetch_video_comments(video_id, max_results=20)

    if not comments:
        return {}

    top_comment = max(comments, key=lambda c: c["likes"])
    avg_likes = sum(c["likes"] for c in comments) / len(comments)

    return {
        "total_comments_analyzed": len(comments),
        "top_comment": {
            "text": top_comment["text"],
            "author": top_comment["author"],
            "likes": top_comment["likes"]
        },
        "average_likes_per_comment": round(avg_likes, 2)
    }
