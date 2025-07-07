import os

import click
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

CLIENT_SECRETS_FILE = "client_secrets.json"
CREDENTIALS_FILE = "credentials.json"


def get_authenticated_service():
    """
    Authenticates with the Google API and returns a YouTube service object.
    Handles token creation, storage, and refresh.
    """
    creds = None

    if os.path.exists(CREDENTIALS_FILE):
        try:
            creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
            click.secho("Loaded credentials from file.", fg="blue")
        except Exception as e:
            click.secho(
                f"Could not load credentials from file: {e}. Re-authentication may be needed.",
                fg="yellow",
            )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                click.secho("Refreshing expired credentials...", fg="blue")
                creds.refresh(Request())
            except Exception as e:
                click.secho(
                    f"Failed to refresh token: {e}. Please re-authorize.", fg="red"
                )
                os.remove(CREDENTIALS_FILE)
                return get_authenticated_service()
        else:
            click.secho(
                "Credentials not found or invalid. Starting OAuth flow...", fg="blue"
            )
            if not os.path.exists(CLIENT_SECRETS_FILE):
                click.secho(
                    f"OAuth client secrets file not found at: {CLIENT_SECRETS_FILE}",
                    fg="red",
                )
                click.secho(
                    "Please download your OAuth 2.0 credentials from the Google Cloud Console",
                    fg="red",
                )
                click.secho(
                    "and save them as 'client_secrets.json' in the same directory as this script.",
                    fg="red",
                )
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # save credentials
        try:
            with open(CREDENTIALS_FILE, "w") as token_file:
                token_file.write(creds.to_json())
            click.secho(f"Credentials saved to {CREDENTIALS_FILE}", fg="blue")
        except Exception as e:
            click.secho(f"Failed to save credentials: {e}", fg="red")

    try:
        return build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    except Exception as e:
        click.secho(f"Failed to build YouTube service: {e}", fg="red")
        return None


def upload_video(
    youtube, video_path, title, description, category_id, privacy_status, tags=[]
):
    """
    Uploads a video to YouTube.

    Args:
        youtube: The authenticated YouTube service object.
        video_path (str): The path to the video file.
        title (str): The title of the video.
        description (str): The description of the video.
        category_id (str): The category ID for the video (e.g., '22' for People & Blogs).
        privacy_status (str): The privacy status ('public', 'private', or 'unlisted').
        tags (list): A list of tags for the video.
    """
    if not os.path.exists(video_path):
        click.secho(f"Video file not found at: {video_path}", fg="red")
        return

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": False},
    }

    try:
        click.secho(f"Starting upload of '{video_path}'...", fg="blue")
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part=",".join(body.keys()), body=body, media_body=media
        )

        # upload with progress
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                click.secho(f"Uploaded {int(status.progress() * 100)}%.", fg="blue")

        video_id = response.get("id")
        if video_id:
            click.secho(
                f"Video upload successful! Watch here: https://www.youtube.com/watch?v={video_id}",
                fg="green",
            )
        else:
            click.secho(
                f"Upload failed. No video ID returned. Full response: {response}",
                fg="red",
            )

    except HttpError as e:
        click.secho(
            f"An HTTP error {e.resp.status} occurred:\n{e.content.decode('utf-8')}",
            fg="red",
        )
    except Exception as e:
        click.secho(f"An unexpected error occurred: {e}", fg="red")


# google-api-python-client
# oauth2-client
# google_auth_oauthlib
# pyopenssl
