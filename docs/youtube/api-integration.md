# YouTube Data API v3 - Integration Notes

## Overview

The YouTube Data API v3 can automate channel management tasks as production scales up.

## Useful Endpoints

### Uploads
- `videos.insert` - Upload videos programmatically
- `thumbnails.set` - Set custom thumbnails after upload

### Channel Management
- `channels.list` - Get channel stats (subscribers, views)
- `playlists.insert` / `playlistItems.insert` - Create and populate playlists

### Analytics (YouTube Analytics API)
- View counts, watch time, audience retention
- Traffic sources and demographic data

## Setup Requirements

1. Google Cloud project with YouTube Data API v3 enabled
2. OAuth 2.0 credentials (for uploading/managing content)
3. API key (for read-only public data)
4. Python client: `pip install google-api-python-client google-auth-oauthlib`

## Example: Upload Video

```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

youtube = build("youtube", "v3", credentials=credentials)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": "Character Showcase: Jetplane",
            "description": "Meet Jetplane, the color-farting dinosaur.",
            "tags": ["AI animation", "animated movie", "AI filmmaking"],
            "categoryId": "1"  # Film & Animation
        },
        "status": {
            "privacyStatus": "public"
        }
    },
    media_body=MediaFileUpload("video.mp4")
)
response = request.execute()
```

## Quota Limits

- Default quota: 10,000 units/day
- Video upload: 1,600 units per upload
- Most read operations: 1 unit
- Plan uploads during off-peak to stay within limits

## Future Automation Ideas

- Auto-upload rendered scenes with metadata from build pipeline
- Playlist management (group by act, character, or content type)
- Pull analytics into production dashboard
- Schedule uploads via `status.publishAt`
