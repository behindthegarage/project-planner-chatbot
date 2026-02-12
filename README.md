# Project-Planner-Chatbot

## Overview
A collection of scripts with the goal of constructing an AI-powered chatbot system that builds a database of activities and projects from exported Gmail emails. It uses natural language processing to extract relevant information from email conversations, primarily focused on summer camps and childcare programs. The chatbot interface allows users to query the database for activity ideas and plan new projects by providing prompts. The system can also generate novel project suggestions by combining elements from the existing database entries using advanced language models. This project aims to streamline activity planning and facilitate creativity for camp organizers and childcare providers. 

A WORK IN PROGRESS

## Installation

To set up the project-planner-chatbot on your local machine, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/project-planner-chatbot.git
   cd project-planner-chatbot
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Before running the application, you need to specify the mbox file that contains the emails to be processed:

- Place your `.mbox` file in the root directory of the project.
- Open `process_emails.py` and modify the `mbox_file` variable to point to your mbox file:
  ```python
  mbox_file = 'your_mbox_filename.mbox'
  ```

## Running the Application

To run the project-planner-chatbot, execute the following command in the terminal:

```bash
python main.py
```

This will process the emails from the specified mbox file, extract relevant data, save it to a JSON file, and allow you to browse through the cleaned emails interactively.

## Features

- **Email Extraction**: Extracts and cleans email content from mbox files.
- **Data Storage**: Saves cleaned email data in JSON format for easy access and manipulation.
- **Interactive Email Browsing**: Allows users to browse through processed emails interactively.

## Contributing

Contributions to the project-planner-chatbot are welcome! Please refer to the contributing guidelines for more information on how to submit pull requests, report issues, and make suggestions for improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
An AI-powered chatbot system that builds a database of activities and projects from exported Gmail emails. It uses natural language processing to extract relevant information from email conversations, primarily focused on summer camps and childcare programs. The chatbot interface allows users to query the database for activity ideas and plan new projects by providing prompts. The system can also generate novel project suggestions by combining elements from the existing database entries using advanced language models. This project aims to streamline activity planning and facilitate creativity for camp organizers and childcare providers.# Auto-deploy test
