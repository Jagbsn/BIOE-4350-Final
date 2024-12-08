from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

def get_drive_service():
    """Initialize Google Drive service using service account"""
    try:
        # Use service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            'drive.json',
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"Error initializing Drive service: {e}")
        return None

def upload_to_drive(file_path, folder_id, new_filename=None):
    """Upload file to Google Drive and return the shareable link"""
    try:
        service = get_drive_service()
        if not service:
            return None

        file_metadata = {
            'name': new_filename if new_filename else os.path.basename(file_path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        print(f"File uploaded to Drive: {file.get('webViewLink')}")
        return file.get('webViewLink')
    except Exception as e:
        print(f"Error uploading to Drive: {e}")
        return None
