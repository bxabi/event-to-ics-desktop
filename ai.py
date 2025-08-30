import base64
import datetime
import os

from openai import OpenAI

if os.path.exists('.env'):
    with open('.env') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


def ask_gpt(text, reminder, file_path):
    prompt = ("Create an ics file from the following event description. I only need the content of the ics file, "
              "no additional characters, no markdown, no ```plaintext")
    prompt += "Today's date is " + str(datetime.date.today()) + ". "
    prompt += "My time zone is " + str(datetime.datetime.now().astimezone().tzinfo) + ". "
    prompt += "The event: " + text + ". "
    if reminder != "":
        prompt += "The reminder: " + reminder
    else:
        prompt += "No reminder"

    messages = [{"role": "user",
                 "content": [
                     {"type": "text", "text": prompt},
                 ]}]

    if file_path != "":
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        image_url = f"data:image/png;base64,{base64_image}"
        messages[0]["content"].append({"type": "image_url", "image_url": {"url": image_url}})

    client = OpenAI()  # The key is taken from os.environ.get("OPENAI_API_KEY")
    chat_completion = client.chat.completions.create(model="gpt-5-mini", messages=messages)
    return chat_completion.choices[0].message.content
