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


def ask_gpt(text, reminder):
    prompt = ("Create an ics file from the following event description. I only need the content of the ics file, "
              "no additional characters, no markdown, no ```plaintext")
    prompt += "Today's date is " + str(datetime.date.today()) + ". "
    prompt += "My time zone is " + str(datetime.datetime.now().astimezone().tzinfo) + ". "
    prompt += "The event: " + text + ". "
    if reminder != "":
        prompt += "The reminder: " + reminder
    else:
        prompt += "No reminder"

    client = OpenAI()  # The key is taken from os.environ.get("OPENAI_API_KEY")
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat_completion.choices[0].message.content


def open_ics_file(ics_file_path):
    os_name = platform.system()
    if os_name == 'Windows':
        command = ['start', ics_file_path]
        subprocess.call(command, shell=True)
    elif os_name == 'Darwin':  # macOS
        command = ['open', ics_file_path]
        subprocess.call(command)
    elif os_name == 'Linux':
        command = ['xdg-open', ics_file_path]
        subprocess.call(command)
    else:
        raise ValueError("Unsupported operating system: " + os_name)


def click():
    generate_button.config(state="disabled")
    show_ics.config(state="disabled")
    progress_bar.pack()
    progress_bar.start()

    def threaded_process():
        text = event_field.get("1.0", tk.END)
        reminder = reminder_field.get("1.0", tk.END)
        try:
            response = ask_gpt(text, reminder)
            window.after(0, lambda: ics_field.replace("1.0", tk.END, response))
        except Exception as e:
            err = str(e)
            window.after(0, lambda: messagebox.showerror("Error", err))
        finally:
            window.after(0, cleanup)

    def cleanup():
        progress_bar.stop()
        progress_bar.pack_forget()
        generate_button.config(state="normal")
        show_ics.config(state="normal")
        add_to_calendar()

    thread = threading.Thread(target=threaded_process)
    thread.start()


def add_to_calendar():
    with open(tmpFile, 'w') as f:
        f.write(ics_field.get("1.0", tk.END))
    open_ics_file(tmpFile)


window = tk.Tk()
window.title("Text to ICS")
icon = tk.PhotoImage(file="icon.png")
window.iconphoto(True, icon)

event_label = tk.Label(window, text="Event Description:")
event_label.pack(pady=(10, 0))
event_field = tk.Text(window, height=10)
event_field.pack()
reminder_label = tk.Label(window, text="Reminder:")
reminder_label.pack(pady=(10, 0))
reminder_field = tk.Text(window, height=2)
reminder_field.pack()


def select_all(event):
    event.widget.tag_add(tk.SEL, "1.0", tk.END)
    event.widget.mark_set(tk.INSERT, "1.0")
    event.widget.see(tk.INSERT)
    return 'break'


def toggle_ics():
    if ics_label.winfo_viewable():
        ics_label.pack_forget()
        ics_field.pack_forget()
        show_ics.config(text="Show the ICS")
    else:
        ics_label.pack(pady=(10, 0))
        ics_field.pack()
        show_ics.config(text="Hide the ICS")


event_field.bind('<Control-a>', select_all)
event_field.bind('<Control-A>', select_all)

event_menu = tk.Menu(window, tearoff=0)
event_menu.add_command(label="Paste", command=lambda: event_field.event_generate("<<Paste>>"))

def show_event_menu(event):
    event_menu.tk_popup(event.x_root, event.y_root)

event_field.bind("<Button-3>", show_event_menu)

ics_label = tk.Label(window, text="ICS:")
ics_field = tk.Text(window, height=10)

button_frame = tk.Frame(window)
button_frame.pack()
generate_button = tk.Button(button_frame, text="Generate", command=click)
generate_button.pack(side=tk.LEFT, padx=5)
show_ics = tk.Button(button_frame, text="Show the ICS", command=toggle_ics)
show_ics.config(state="disabled")
show_ics.pack(side=tk.LEFT, padx=5)

progress_bar = ttk.Progressbar(window, mode='indeterminate')

window.mainloop()
