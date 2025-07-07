import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# --- Configuration ---
# Define the scope required for uploading videos. The original scope was incorrect.
# This scope allows managing your YouTube account, including video uploads.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# File paths
# It's clearer to distinguish between the client secrets file (from Google)
# and the credentials file (generated after user authorization).
CLIENT_SECRETS_FILE = "client_secrets.json"
CREDENTIALS_FILE = "credentials.json"

# --- Setup Logging ---
# Using the standard logging module for better portability instead of a custom one.
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_authenticated_service():
    """
    Authenticates with the Google API and returns a YouTube service object.
    Handles token creation, storage, and refresh.
    """
    creds = None
    
    if os.path.exists(CREDENTIALS_FILE):
        try:
            creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
            logging.info("Loaded credentials from file.")
        except Exception as e:
            logging.warning(f"Could not load credentials from file: {e}. Re-authentication may be needed.")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logging.info("Refreshing expired credentials...")
                creds.refresh(Request())
            except Exception as e:
                logging.error(f"Failed to refresh token: {e}. Please re-authorize.")
                os.remove(CREDENTIALS_FILE)
                return get_authenticated_service()
        else:
            logging.info("Credentials not found or invalid. Starting OAuth flow...")
            if not os.path.exists(CLIENT_SECRETS_FILE):
                logging.error(f"OAuth client secrets file not found at: {CLIENT_SECRETS_FILE}")
                logging.error("Please download your OAuth 2.0 credentials from the Google Cloud Console")
                logging.error("and save them as 'client_secrets.json' in the same directory as this script.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # save credentials
        try:
            with open(CREDENTIALS_FILE, 'w') as token_file:
                token_file.write(creds.to_json())
            logging.info(f"Credentials saved to {CREDENTIALS_FILE}")
        except Exception as e:
            logging.error(f"Failed to save credentials: {e}")

    try:
        return build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    except Exception as e:
        logging.error(f"Failed to build YouTube service: {e}")
        return None

def upload_video(youtube, video_path, title, description, category_id, privacy_status, tags=[]):
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
        logging.error(f"Video file not found at: {video_path}")
        return

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    try:
        logging.info(f"Starting upload of '{video_path}'...")
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        # upload with progress
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Uploaded {int(status.progress() * 100)}%.")
        
        video_id = response.get('id')
        if video_id:
            logging.info(f"Video upload successful! Watch here: https://www.youtube.com/watch?v={video_id}")
        else:
            logging.error(f"Upload failed. No video ID returned. Full response: {response}")

    except HttpError as e:
        logging.error(f"An HTTP error {e.resp.status} occurred:\n{e.content.decode('utf-8')}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# google-api-python-client
# oauth2-client
# google_auth_oauthlib
# pyopenssl
