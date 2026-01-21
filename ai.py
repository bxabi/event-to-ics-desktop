import datetime
import os

import google.generativeai as genai

if os.path.exists('.env'):
    with open('.env') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


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

    model = genai.GenerativeModel('gemini-2.5-flash')

    content = [prompt]
    uploaded_file = None
    if file_path != "":
        uploaded_file = genai.upload_file(file_path)
        content.append(uploaded_file)

    response = model.generate_content(content)

    if uploaded_file:
        genai.delete_file(uploaded_file.name)

    return response.text
