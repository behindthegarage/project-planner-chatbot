from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from PyPDF2 import PdfReader
import docx2txt
import os

SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']
     
def export_summer_camp_text(creds):
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Search for files containing 'summer camp' in the name
    query = "fullText contains 'summer camp' or name contains 'summer camp'"
    
    try:
        results = drive_service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found containing summer camp information.')
            return
        
        # Create the data/google directory if it doesn't exist
        os.makedirs('data/google', exist_ok=True)
        
        for item in items:
            file_id = item['id']
            file_name = item['name']
            mime_type = item['mimeType']
            
            if mime_type == 'application/vnd.google-apps.document':
                # Export Google Doc as plain text
                export_mime_type = 'text/plain'
                request = drive_service.files().export_media(fileId=file_id, mimeType=export_mime_type)
                file_content = request.execute().decode('utf-8')  # Decode the content

            elif mime_type == 'application/pdf':
                # Download PDF file and extract text
                request = drive_service.files().get_media(fileId=file_id)
                file_content = io.BytesIO(request.execute())
                pdf_reader = PdfReader(file_content)
                file_content = "\n".join(page.extract_text() for page in pdf_reader.pages)

            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                # Download Word document and extract text
                request = drive_service.files().get_media(fileId=file_id)
                file_content = io.BytesIO(request.execute())
                file_content = docx2txt.process(file_content)  # Process the Word document

            else:
                print(f'Skipping unsupported file type: {file_name}')
                continue

            print(f'Exporting text from: {file_name}')
            file_name = file_name.replace('/', '_')  # Replace forward slashes with underscores
            file_path = os.path.join('data', 'google', f'{file_name}.txt')
            with open(file_path, 'w') as f:
                f.write(file_content)
            
    except HttpError as error:
        print(f'An error occurred: {error}')

# Set the path to the credentials.json file
credentials_path = 'credentials.json'

# Authenticate and get credentials (not shown)
creds = None
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
else:
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

export_summer_camp_text(creds)