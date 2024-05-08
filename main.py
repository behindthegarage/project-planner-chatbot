import mailbox
import os
import requests
from dotenv import load_dotenv
import openai
import anthropic

# Load environment variables
load_dotenv()

# OpenAI setup
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_client = openai.OpenAI(api_key=openai_api_key)

# Claude API setup
# claude_api_key = os.getenv('CLAUDE_API_KEY')
# anthropic_client = anthropic.Anthropic(api_key=claude_api_key)

def analyze_email(content):
    # Analyze with OpenAI
    response_openai = openai_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Analyze the following email content:",
            },
            {
                "role": "user", "content": content,
            }
        ],
        model="gpt-3.5-turbo",
    )
    
    # Analyze with Claude using the anthropic client
    # response_claude = anthropic_client.messages.create(
    #     model="claude-3-opus-20240229",
    #     max_tokens=1000,
    #    temperature=0.0,
    #    system="Analyze the following email content:",
    #    messages=[{"role": "user", "content": content}]
    # )

    return response_openai, # response_claude

def process_mbox(file_path):
    mbox = mailbox.mbox(file_path)
    for message in mbox:
        subject = message['subject']
        payload = message.get_payload(decode=True)
        if payload:
            content = payload.decode()
            analysis_openai = analyze_email(content) # , analysis_claude
            print(f"Subject: {subject}")
            print("OpenAI Analysis:", analysis_openai)
            # print("Claude Analysis:", analysis_claude.content)

# Example usage
process_mbox('/home/user/mail/newsletters.mbox')