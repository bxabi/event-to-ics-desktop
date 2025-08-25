import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import tkinter.ttk as ttk

from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from ai import ask_gpt
from ui_independent import add_to_calendar


def click():
    generate_button.config(state="disabled")
    show_ics.config(state="disabled")
    progress_bar.pack()
    progress_bar.start()

    def threaded_process():
        text = event_field.get("1.0", tk.END)
        reminder = reminder_field.get("1.0", tk.END)
        success = False
        response = None
        try:
            response = ask_gpt(text, reminder, file_path)
            window.after(0, lambda: ics_field.replace("1.0", tk.END, response))
            success = True
        except Exception as e:
            err = str(e)
            print(err)
            window.after(0, lambda: messagebox.showerror("Error", err))

        finally:
            window.after(0, cleanup(success, response))

    def cleanup(success: bool, ics_content: str):
        progress_bar.stop()
        progress_bar.pack_forget()
        generate_button.config(state="normal")
        show_ics.config(state="normal")
        if success:
            add_to_calendar(ics_content)

    thread = threading.Thread(target=threaded_process)
    thread.start()


window = TkinterDnD.Tk()
window.title("Text to ICS")
window.geometry("500x650")
icon = tk.PhotoImage(file="icon.png")
window.iconphoto(True, icon)

event_label = tk.Label(window, text="Event Description:")
event_label.pack(pady=(10, 0))
event_field = tk.Text(window, height=10)
event_field.pack(padx=10, expand=True, fill=tk.BOTH)
reminder_label = tk.Label(window, text="Reminder:")
reminder_label.pack(pady=(10, 0))
reminder_field = tk.Text(window, height=2)
reminder_field.pack(padx=10, fill=tk.X)


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
        ics_field.pack(padx=10, expand=True, fill=tk.BOTH)
        show_ics.config(text="Hide the ICS")


def show_event_menu(event):
    event_menu.tk_popup(event.x_root, event.y_root)


event_menu = tk.Menu(window, tearoff=0)
event_menu.add_command(label="Paste", command=lambda: event_field.event_generate("<<Paste>>"))
event_field.bind('<Control-a>', select_all)
event_field.bind('<Control-A>', select_all)
event_field.bind("<Button-3>", show_event_menu)

file_path = ""


def on_drop(event):
    global file_path
    file_path = event.data.strip('{}')
    set_image_preview()


def choose_file(event=None):
    global file_path
    path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.png *.jpeg *.JPG *.PNG *.JPEG")],
        initialdir=os.path.expanduser("~") + "/Desktop"
    )
    if path:
        file_path = path
        set_image_preview()


def set_image_preview():
    if not file_path:
        return
    try:
        image_frame.update_idletasks()
        width = image_frame.winfo_width()
        height = image_frame.winfo_height()

        img = Image.open(file_path)
        resample_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS
        img.thumbnail((width, height), resample_filter)

        photo = ImageTk.PhotoImage(img)
        image_preview.config(image=photo, text="")
        image_preview.image = photo
    except Exception as e:
        image_preview.config(text="Error loading image", image=None)
        print(e)


def on_frame_configure(event):
    set_image_preview()


image_frame = tk.Frame(window, height=100, relief=tk.SUNKEN, borderwidth=1)
image_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
image_frame.pack_propagate(False)

image_preview = tk.Label(image_frame, text="Drop an image here or Click to open file.")
image_preview.pack(expand=True, fill=tk.BOTH)
image_preview.drop_target_register(DND_FILES)
image_preview.dnd_bind('<<Drop>>', on_drop)
image_preview.bind("<Button-1>", choose_file)
image_frame.bind("<Configure>", on_frame_configure)

ics_label = tk.Label(window, text="ICS:")
ics_field = tk.Text(window, height=10)

button_frame = tk.Frame(window)
button_frame.pack(pady=5)
generate_button = tk.Button(button_frame, text="Generate", command=click)
generate_button.pack(side=tk.LEFT, padx=5)
show_ics = tk.Button(button_frame, text="Show the ICS", command=toggle_ics)
show_ics.config(state="disabled")
show_ics.pack(side=tk.LEFT, padx=5)

progress_bar = ttk.Progressbar(window, mode='indeterminate')

window.mainloop()
