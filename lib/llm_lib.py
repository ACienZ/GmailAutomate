import json


def openai_task(config, client, system_prompt, task_prompt, content):
    completion = client.chat.completions.create(
        model=config.ModelSettings.model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": task_prompt + content},
                ],
            },
        ],
    )
    answer = completion.choices[0].message.content

    return answer


def get_gpt_answer(config, client, system_prompt, task_prompt, content):
    # while gpt answer not fit json format, retry
    is_continue = True
    while is_continue:
        answer = openai_task(config, client, system_prompt, task_prompt, content)
        answer = answer.strip("```json").strip("```").strip()
        try:
            gpt_answer = json.loads(answer)
            is_continue = False
        except json.JSONDecodeError as e:
            print("!!Failed to parse JSON:", e)
            continue
    return gpt_answer
