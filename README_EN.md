# Gmail Automation Assistant

This project is a Gmail automation tool designed to automatically read unread emails in the inbox, filter out student assignments, download attachments, and reply.

## 1. Environment Setup

### Create and Activate Conda Environment

```bash
conda create -n gmail_automate python=3.8
conda activate gmail_automate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Gmail API Authentication Setup

Reference:

[Gmail API Python Quick Start](https://developers.google.com/workspace/gmail/api/quickstart/python)

### Obtain API Credentials

Make sure to download the credentials file (credentials.json)
Rename the downloaded credentials file to `client_secret.json` and place it in the project root directory

### Notes

- You need to add test users on the OAuth permission request page
- Reference:
  - [Access blocked: Project has not completed the Google verification process](https://stackoverflow.com/questions/75454425/access-blocked-project-has-not-completed-the-google-verification-process)
- Due to the fact that the Gmail API starts reading from the latest email, if a student repeatedly submits attachments with the same file name, the duplicate attachments will be renamed starting from 9. If the same student submits the same assignment more than 9 times, the count will become negative.

## 3. Configuration File Setup

1. Copy `config/config.example.yaml` to `config/configs.yaml`
2. Edit the `configs.yaml` file and fill in the following information:
   - OpenAI or DeepSeek API key
   - Specify the model to use and its URL
   - Assignment settings (number, save path, deadline, etc.)
   - Your email information

## 4. Usage Instructions

### Run the Program

```bash
python main.py
```

The program will automatically:

1. Read unread emails and perform initial email filtering

    - Specific filtering rules:
        - If it's an HTML email, it's not considered a student assignment
        - If there are no attachments, it's not considered a student assignment

2. Use an LLM to analyze email content
3. Determine if it's a student email, and skip special student emails for manual processing

    - Specific emails to skip:
        - Emails that the LLM doesn't consider assignments
        (gpt_answer["is_assignment"] != "true")
        - Emails that the LLM considers to contain other questions
        (gpt_answer["whether_contain_other_questions"] == "true")
        - Emails that the LLM considers not for the current assignment
        (gpt_answer["assignment_number"] != config.AssignmentSettings.assignment_number)
        - Emails where the LLM cannot determine student ID or name
        (gpt_answer["student_id"] == "unknown" or gpt_answer["student_first_name"] == "unknown" or gpt_answer["student_last_name"] == "unknown")

4. Download attachments from student emails
5. Automatically reply to student emails

### Reply Email Functionality

Since simplegmail doesn't have a reply function, Gmail API is used to send reply emails.

Reference: [How to reply to an email using Gmail API](https://stackoverflow.com/a/76676129)
