import os
from datetime import datetime

from simplegmail import Gmail
from openai import OpenAI

from config.load_config import load_config
from lib.llm_lib import get_gpt_answer
from lib.gmail_lib import reply_email


def gmail_automate(
    config,
    client,
    system_prompt,
    task_prompt,
    reply_message_content,
    log_file_name,
    automate_log,
):
    gmail = Gmail()
    messages = gmail.get_unread_inbox()

    processed_unread_messages_num = 0
    processed_student_messages_num = 0

    for message in messages:
        processed_unread_messages_num += 1
        # 1. get email details
        sender = message.sender
        # receiver = message.recipient
        subject = message.subject
        send_date = message.date
        # snippet = message.snippet

        # get email content
        if message.plain:
            email_content = message.plain
        # not an email from student
        elif message.html:
            print(f"Email: {subject}\n from {sender}, has html content. \n")
            continue

        # get email attachment
        attach_filenames = []
        attachments = message.attachments
        if attachments:
            for attach in attachments:
                attach_filenames.append(attach.filename)
                # attach.download()  # downloads and saves each attachment under it's stored
                # filename. You can download without saving with `attm.download()`
        # not an email from student
        else:
            print(f"Email: {subject}\n from {sender}, has no attachments. \n")
            continue

        # 2. check whether the email is a student submitted assignment with gpt
        content = f"""
        Here is the detail of the email:
        Subject: {subject}
        Sender: {sender}
        Date: {send_date}
        Content: \n{email_content}
        Attachment_filenames: {attach_filenames}
        """

        gpt_answer = get_gpt_answer(config, client, system_prompt, task_prompt, content)
        print("Get GPT Answer:", gpt_answer, "\n")

        if gpt_answer["is_assignment"] != "true":
            continue
        else:
            if gpt_answer["whether_contain_other_questions"] == "true":
                # create a log corresponding to current assignment number under logs/
                with open(log_file_name, "a") as f:
                    f.write(f"Sender: {sender}\n")
                    f.write(f"Subject: {subject}\n")
                    f.write(f"Date: {send_date}\n")
                    f.write(f"Content: \n{email_content}\n")
                    f.write(f"Attachment_filenames: {attach_filenames}\n")
                    f.write(f"GPT Answer: {gpt_answer}\n")
                    f.write(f"Problem: exist other questions\n")
                    f.write("-" * 20 + "\n")
                continue
            else:
                if (
                    gpt_answer["assignment_number"]
                    != config.AssignmentSettings.assignment_number
                ):
                    with open(log_file_name, "a") as f:
                        f.write(f"Sender: {sender}\n")
                        f.write(f"Subject: {subject}\n")
                        f.write(f"Date: {send_date}\n")
                        f.write(f"Content: \n{email_content}\n")
                        f.write(f"Attachment_filenames: {attach_filenames}\n")
                        f.write(f"GPT Answer: {gpt_answer}\n")
                        f.write(f"Problem: Not submitting the correct assignment\n")
                        f.write("-" * 20 + "\n")
                else:
                    if (
                        gpt_answer["student_id"] == "unknown"
                        or gpt_answer["student_first_name"] == "unknown"
                        or gpt_answer["student_last_name"] == "unknown"
                    ):
                        with open(log_file_name, "a") as f:
                            f.write(f"Sender: {sender}\n")
                            f.write(f"Subject: {subject}\n")
                            f.write(f"Date: {send_date}\n")
                            f.write(f"Content: \n{email_content}\n")
                            f.write(f"Attachment_filenames: {attach_filenames}\n")
                            f.write(f"GPT Answer: {gpt_answer}\n")
                            f.write(f"Problem: student_id or student_name is unknown\n")
                            f.write("-" * 20 + "\n")
                    else:
                        # 3. save the assignment
                        student_folder_name = (
                            gpt_answer["student_id"]
                            + "_"
                            + gpt_answer["student_first_name"]
                            + gpt_answer["student_last_name"]
                        )
                        student_folder_path = os.path.join(
                            config.AssignmentSettings.assignment_save_path,
                            student_folder_name,
                        )
                        if not os.path.exists(student_folder_path):
                            os.makedirs(student_folder_path)
                            # write to automate_log
                            with open(automate_log, "a") as f:
                                f.write(
                                    f"Add new student folder: {student_folder_name}\n"
                                )

                        # create a folder for current assignment
                        assignment_folder_name = (
                            "Assignment" + config.AssignmentSettings.assignment_number
                        )
                        # check whether the assignment submitted after the deadline
                        # 将时间字符串转换为 datetime 对象
                        send_date_dt = datetime.strptime(
                            send_date, "%Y-%m-%d %H:%M:%S%z"
                        )
                        deadline_str = config.AssignmentSettings.deadline
                        # 将不带时区的时间字符串转换为 datetime 对象，并设置为 UTC+9 时区
                        deadline_dt = datetime.strptime(
                            deadline_str, "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=send_date_dt.tzinfo)

                        if send_date_dt > deadline_dt:
                            assignment_folder_name = (
                                "Assignment"
                                + config.AssignmentSettings.assignment_number
                                + "_late"
                            )
                        assignment_folder_path = os.path.join(
                            student_folder_path, assignment_folder_name
                        )
                        if not os.path.exists(assignment_folder_path):
                            os.makedirs(assignment_folder_path)
                            # write to automate_log
                            with open(automate_log, "a") as f:
                                f.write(
                                    f"Add new assignment folder: {student_folder_name} -- {assignment_folder_name}\n"
                                )

                        for attach in attachments:
                            attach.download()
                            # if the attachment name already exist, add a number to the end of the filename
                            whether_loop = True
                            counter = 1
                            while whether_loop:
                                if os.path.exists(
                                    os.path.join(
                                        assignment_folder_path, attach.filename
                                    )
                                ):
                                    attach.filename = (
                                        attach.filename.split(".")[0]
                                        + str(counter)
                                        + "."
                                        + attach.filename.split(".")[1]
                                    )
                                    counter += 1
                                else:
                                    whether_loop = False
                            with open(
                                os.path.join(assignment_folder_path, attach.filename),
                                "wb",
                            ) as f:
                                f.write(attach.data)
                            # write to automate_log
                            with open(automate_log, "a") as f:
                                f.write(
                                    f"Add new assignment file: {student_folder_name} -- {assignment_folder_name} -- {attach.filename}\n"
                                )
                        # write to automate_log
                        with open(automate_log, "a") as f:
                            # add solved email details to the log file
                            f.write(f"-" * 20 + "\n")
                            f.write(f"Sender: {sender}\n")
                            f.write(f"Subject: {subject}\n")
                            f.write(f"Date: {send_date}\n")
                            f.write(f"Content: \n{email_content}\n")
                            f.write(f"Attachment_filenames: {attach_filenames}\n")
                            f.write(f"GPT Answer: {gpt_answer}\n")

                            f.write(f"=" * 30 + "\n")

                        # 4. reply to the email
                        message_content = (
                            f"Dear {gpt_answer['student_first_name']} {gpt_answer['student_last_name']}, \n\n"
                            + reply_message_content
                        )

                        reply_email(config, message_content, message)
                        # 5. mark the email as read
                        message.mark_as_read()

                        processed_student_messages_num += 1

    print("-" * 20)
    print(f"Processed {processed_unread_messages_num} unread messages.")
    print(
        f"Processed and stored {processed_student_messages_num} student's assignments."
    )


def main():
    # set OpenAI API key
    config = load_config()
    os.environ["OPENAI_API_KEY"] = config.DEEPSEEK.API_KEY
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=config.ModelSettings.base_url,
    )

    system_prompt = (
        "You are a teaching assistant to help professor verify student's assignment."
    )

    task_prompt = """
    You will receive an email, you need to answer the following questions: 
    1. Whether the email is a student submitted assignment?
    2. If this is an email to submit an assignment from a student, you need to check whether the email contains other questions from the student.
    3. If this is an email to submit an assignment from a student, you need to check the student's assignment number.
    4. If this is an email to submit an assignment from a student, you need to check the student's student ID.
    5. If this is an email to submit an assignment from a student, you need to check the student's name.

    Usually, an email to submit an assignment from a studnet, its attachment's filename will follow our requirement, and should be like this: studentId_studentName_NN_assignmentNumber.fileFormat, where NN means the short name of the course neural network.
    For studentId, it usually is a 8-digit number, start from 44 (indicating the institute number), the following 2 digits indicate the year, the following 4 digits are the rest of the studentID. However, because there may be some students from other institutes, the studentId may also include alphabets, like: 5123DG00, or 2025MCB099. So the core idea is to check the beginning of attachment's filename.

    Your answer should be a json format, the following is the example of the format, please do follow it and include all the parts of the format:
    {
        "is_assignment": "true",
        "whether_contain_other_questions": "false",
        "assignment_number": "1",
        "student_id": "1234567890", 
        "student_first_name": "JohnSwe",
        "student_last_name": "DOE"
    }
    Note that if you cannot find the assignmentNumber, studentId or studentName, you can just return "unknown" as the assignment_number, student_id, student_first_name or student_last_name.
    As for the studentName, all the characters of the last name MUST be capitalized, while all the characters other than the first character of the first name MUST be lowercase. (However, If a student's first name includes more than one word, you MUST capitalize the first character of each word, and the rest of the characters MUST be lowercase. And all the words of the first name MUST be connected WITHOUT any space or other characters. For example, if a student's first name is "John Swe", you should return "JohnSwe" as the student_first_name.)

    """

    log_file_name = (
        "logs/"
        + "Assignment_"
        + config.AssignmentSettings.assignment_number
        + "_remain_to_solve.txt"
    )
    automate_log = (
        "logs/"
        + "Assignment_"
        + config.AssignmentSettings.assignment_number
        + "_automate_log.txt"
    )

    reply_message_content = (
        f"Your assignment has been accepted by an automated script, thank you very much. \n\n If you have any questions, please feel free to contact me. \n(If you need human assistant, please add [Ask for human assistant] at the beginning of the subject)\n\nBest regards, \n"
        + f"{config.AssignmentSettings.my_name}"
    )

    gmail_automate(
        config,
        client,
        system_prompt,
        task_prompt,
        reply_message_content,
        log_file_name,
        automate_log,
    )


if __name__ == "__main__":
    main()
