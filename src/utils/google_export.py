import re
import io
import os
import zipfile
import pandas as pd
import xlrd
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from PyPDF2 import PdfReader
import docx2txt

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_folder_id(service, folder_path):
    folder_names = folder_path.split('/')
    parent_id = 'root'
    for folder_name in folder_names:
        query = f"'{parent_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            print(f'No folder found with the name: {folder_name}')
            return None
        parent_id = items[0]['id']
    return parent_id

def list_files_in_folder(service, folder_id, folder_path=""):
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])
    files = []
    for item in items:
        item_path = os.path.join(folder_path, item['name'])
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            files.extend(list_files_in_folder(service, item['id'], item_path))
        else:
            files.append((item, item_path))
    return files

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def export_summer_camp_text(creds, folder_id):
    drive_service = build('drive', 'v3', credentials=creds)
    
    files = list_files_in_folder(drive_service, folder_id)
    
    if not files:
        print('No files found in the specified folder.')
        return
    
    output_dir = 'data/google/'
    os.makedirs(output_dir, exist_ok=True)
    
    for item, item_path in files:
        file_id = item['id']
        file_name = sanitize_filename(item['name'])
        mime_type = item['mimeType']
        
        try:
            if mime_type == 'application/vnd.google-apps.document':
                # Export Google Doc as plain text
                export_mime_type = 'text/plain'
                request = drive_service.files().export_media(fileId=file_id, mimeType=export_mime_type)
                file_content = request.execute().decode('utf-8')
                
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
                with open(os.path.join(output_dir, f'{file_name}.docx'), 'wb') as temp_file:
                    temp_file.write(file_content.getbuffer())
                file_content = docx2txt.process(os.path.join(output_dir, f'{file_name}.docx'))
                os.remove(os.path.join(output_dir, f'{file_name}.docx'))
            
            elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mime_type == 'application/vnd.ms-excel':
                # Download Excel file (.xlsx or .xls) and extract text
                request = drive_service.files().get_media(fileId=file_id)
                file_content = io.BytesIO(request.execute())
                df = pd.read_excel(file_content)
                file_content = df.to_csv(index=False)
                
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Export Google Sheets as CSV and extract text
                export_mime_type = 'text/csv'
                request = drive_service.files().export_media(fileId=file_id, mimeType=export_mime_type)
                file_content = request.execute().decode('utf-8')
                
            elif mime_type == 'text/csv':
                # Download CSV file and extract text
                request = drive_service.files().get_media(fileId=file_id)
                file_content = io.StringIO(request.execute().decode('utf-8'))
                df = pd.read_csv(file_content)
                file_content = df.to_csv(index=False)
                
            elif mime_type == 'text/html':
                # Download HTML file and extract text
                request = drive_service.files().get_media(fileId=file_id)
                file_content = request.execute().decode('utf-8')
                soup = BeautifulSoup(file_content, 'html.parser')
                file_content = soup.get_text()
                
            else:
                print(f'Skipping unsupported file type: {item_path}')
                continue
                
            print(f'Exporting text from: {item_path}')
            with open(os.path.join(output_dir, f'{file_name}.txt'), 'w') as f:
                f.write(file_content)
                
        except HttpError as error:
            print(f'An error occurred while processing file {item_path}: {error}')
        except zipfile.BadZipFile as error:
            print(f'An error occurred while processing Word document {item_path}: {error}')

# Authenticate and get credentials
creds = None
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
else:
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
     
with open('token.json', 'w') as token:
    token.write(creds.to_json())

drive_service = build('drive', 'v3', credentials=creds)
folder_id = get_folder_id(drive_service, 'Documents/Export')
if folder_id:
    print(f'Folder ID for "Documents/Export": {folder_id}')
    export_summer_camp_text(creds, folder_id)
else:
    print('Specified folder not found.')