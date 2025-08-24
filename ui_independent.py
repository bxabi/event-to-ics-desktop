import os
import platform
import subprocess


def open_ics_file(ics_file_path):
    os_name = platform.system()
    if os_name == 'Windows':
        subprocess.call(['start', ics_file_path], shell=True)
    elif os_name == 'Darwin':
        subprocess.call(['open', ics_file_path])
    elif os_name == 'Linux':
        subprocess.call(['xdg-open', ics_file_path])
    else:
        raise ValueError("Unsupported operating system: " + os_name)


def add_to_calendar(ics):
    tmp_file = os.path.expanduser("~") + "/.event-ai.ics"
    with open(tmp_file, 'w') as f:
        f.write(ics)
    open_ics_file(tmp_file)
