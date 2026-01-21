import datetime
import os

from google import genai

if os.path.exists('.env'):
    with open('.env') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


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

    content = [prompt]
    uploaded_file = None
    if file_path != "":
        uploaded_file = client.files.upload(file=file_path)
        content.append(uploaded_file)

    response = client.models.generate_content(model='gemini-2.5-flash', contents=content)

    if uploaded_file:
        client.files.delete(name=uploaded_file.name)

    return response.text
