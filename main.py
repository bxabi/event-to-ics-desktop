import datetime
import os
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk

from openai import OpenAI

tmpFile = os.path.expanduser("~") + "/.event-ai.ics"

if os.path.exists('.env'):
    with open('.env') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


def ask_gpt(prompt):
    client = OpenAI()  # The key is taken from os.environ.get("OPENAI_API_KEY")
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
    generate_button.config(state="disabled")
    add_calendar_button.config(state="disabled")
    progress_bar.pack()
    progress_bar.start()

    def threaded_process():
        text = event_field.get("0.0", tk.END)
        prompt = "Create an ics file from the following event description. I only need the content of the ics file, no additional text, no ics markdown. "
        prompt += "Today's date is " + str(datetime.date.today()) + ". "
        prompt += "My time zone is " + str(datetime.datetime.now().astimezone().tzinfo) + ". "
        prompt += "The event: " + text
        try:
            response = ask_gpt(prompt)
            window.after(0, lambda: ics_field.replace("0.0", tk.END, response))
        except Exception as e:
            window.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            window.after(0, cleanup)

    def cleanup():
        progress_bar.stop()
        progress_bar.pack_forget()
        generate_button.config(state="normal")
        add_calendar_button.config(state="normal")

    thread = threading.Thread(target=threaded_process)
    thread.start()


def add_to_calendar():
    with open(tmpFile, 'w') as file:
        file.write(ics_field.get("0.0", tk.END))
    open_ics_file(tmpFile)


window = tk.Tk()
window.title("Text to ICS")
icon = tk.PhotoImage(file="icon.png")
window.iconphoto(True, icon)

event_field = tk.Text(window, height=10)
event_field.pack()

ics_field = tk.Text(window, height=10)
ics_field.pack()

button_frame = tk.Frame(window)
button_frame.pack()
generate_button = tk.Button(button_frame, text="Generate", command=click)
generate_button.pack(side=tk.LEFT, padx=5)
add_calendar_button = tk.Button(button_frame, text="Add to Calendar", command=add_to_calendar)
add_calendar_button.pack(side=tk.LEFT, padx=5)

progress_bar = ttk.Progressbar(window, mode='indeterminate')
progress_bar.pack()
progress_bar.pack_forget()  # Hide it initially

window.mainloop()
