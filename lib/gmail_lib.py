import base64
import email

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError


# because the simplegmail library does not support reply to the email, we need to use the gmail library to reply to the email
def reply_email(config, message_content, message):
    try:
        creds = Credentials.from_authorized_user_file(
            "./gmail_token.json", scopes=config.GMAIL.SCOPES
        )
        service = build("gmail", "v1", credentials=creds)
        threads = (
            service.users()
            .threads()
            .list(userId="me", labelIds=["UNREAD"])
            .execute()
            .get("threads", [])
        )
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")
        return None
    # Retrieve the list of threads

    # Find the thread with the matching subject
    matching_thread = None
    for thread in threads:
        thread_id = thread["id"]
        try:
            thread_details = (
                service.users().threads().get(userId="me", id=thread_id).execute()
            )
        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f"An error occurred: {error}")
            return None
        top_message = thread_details["messages"][
            0
        ]  # Get the first message in the thread
        message_subject = next(
            (
                header["value"]
                for header in top_message["payload"]["headers"]
                if header["name"] == "Subject"
            ),
            None,
        )
        if message_subject == message.subject:
            matching_thread = thread
            break

    if matching_thread:
        thread_id = matching_thread["id"]
    else:
        raise ValueError("No matching thread found.")

    # Retrieve the details of the thread
    try:
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")
        return None
    messages = thread["messages"][0]["payload"]["headers"]

    # Retrieve the metadata of the thread
    for k in messages:
        # if k["name"] == "To":
        #     recipient = k["value"]
        if k["name"] == "Subject":
            email_subject = k["value"]
        if k["name"] == "From":
            sender = k["value"]
        if k["name"] == "Message-ID":
            message_id = k["value"]

    # Constructing the reply message
    raw = email.message.EmailMessage()
    raw.set_content(message_content)
    raw["To"] = sender
    raw["From"] = config.AssignmentSettings.my_email
    raw["Subject"] = "Re: " + email_subject
    raw["References "] = message_id
    raw["In-Reply-To "] = message_id

    encoded_message = base64.urlsafe_b64encode(raw.as_bytes()).decode()

    create_message = {"raw": encoded_message, "threadId": thread_id}
    # Sending the reply message to the thread
    try:
        send_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")
        return None
