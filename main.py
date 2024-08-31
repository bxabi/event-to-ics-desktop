import datetime
import platform
import subprocess
import tkinter as tk
from tkinter import messagebox

from openai import OpenAI

tmpFile = "/tmp/event-ai.ics"


def ask_gpt(prompt):
    client = OpenAI(
        # Defaults to os.environ.get("OPENAI_API_KEY")
    )
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat_completion.choices[0].message.content


def open_ics_file(ics_file_path):
    os_name = platform.system()

    if os_name == 'Windows':
        command = ['start', ics_file_path]
    elif os_name == 'Darwin':  # macOS
        command = ['open', ics_file_path]
    elif os_name == 'Linux':
        command = ['xdg-open', ics_file_path]
    else:
        raise ValueError("Unsupported operating system: " + os_name)

    subprocess.call(command)


def click():
    text = event_field.get("0.0", tk.END)
    prompt = ("create an ics file from the following event description."
              " I only need the content of the ics file, no additional text, no ics markdown."
              " Today's date is " + str(datetime.date.today()) + ". "
              " My time zone is " + str(datetime.datetime.now().astimezone().tzinfo) + ". "
              " The event: ") + text
    try:
        response = ask_gpt(prompt)
        ics_field.replace("0.0", tk.END, response)
    except Exception as e:
        messagebox.showerror("Error", str(e))


def add_to_calendar():
    with open(tmpFile, 'w') as file:
        file.write(ics_field.get("0.0", tk.END))
    open_ics_file(tmpFile)


window = tk.Tk()
window.title("Text to ics")

event_field = tk.Text(window, height=10)
event_field.pack()
ics_field = tk.Text(window, height=10)
ics_field.pack()

button = tk.Button(window, text="Generate", command=click)
button.pack()

button = tk.Button(window, text="Add to Calendar", command=add_to_calendar)
button.pack()

window.mainloop()
