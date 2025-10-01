import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import winreg
import subprocess
import os
import sys
import ctypes
import time
import urllib.request
import urllib.error

# ---------- Versioning ----------
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/GreenCore16/BackgroundBack/master/Version.md"
LOCAL_VERSION_FILE = "Version.md"

def read_text_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return ""

def normalize_version(s: str) -> str:
    return s.strip().splitlines()[0].strip()

def get_local_version() -> str:
    return normalize_version(read_text_file(resource_path(LOCAL_VERSION_FILE)))

def get_remote_version(timeout_sec: float = 3.0) -> str:
    try:
        with urllib.request.urlopen(GITHUB_VERSION_URL, timeout=timeout_sec) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
            return normalize_version(text)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
        return ""

def prompt_if_outdated(local_v: str, remote_v: str):
    if not remote_v:
        return
    if local_v.strip().lower() != remote_v.strip().lower():
        messagebox.showinfo(
            "Update Available",
            f"You are running {local_v or 'an unknown version'}.\n"
            f"A newer version is available: {remote_v}.\n\n"
            "Please update to the latest version.\n\n"
            "Click OK to continue."
        )

# ---------- Existing code ----------
def resource_path(relative_path: str) -> str:
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(f'"{arg}"' for arg in sys.argv), None, 1)
        sys.exit()
    except Exception as e:
        messagebox.showerror("Administrator Privileges Required",
                             f"Failed to elevate to administrator.\n\nError: {e}")
        sys.exit(1)

# Always require admin
if not is_admin():
    run_as_admin()

# Build APP_TITLE dynamically from local Version.md
_LOCAL_VERSION = get_local_version() or "V2.9"
APP_TITLE = f"BackgroundBack {_LOCAL_VERSION}"
WINDOW_ICON = 'assets/window_icon.ico'  # <-- moved into assets/

def select_file():
    file_path = filedialog.askopenfilename(
        title="Select image file",
        filetypes=[("Image files", "*.bmp;*.jpg;*.jpeg;*.png;*.gif")]
    )
    if file_path:
        entry_var.set(file_path)

def set_wallpaper_registry(path):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
    try:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        except FileNotFoundError:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "Wallpaper", 0, winreg.REG_SZ, path)
        winreg.CloseKey(key)
        return True
    except PermissionError:
        return False
    except Exception as e:
        messagebox.showerror("Registry Error", f"Unexpected error updating registry:\n{e}")
        return False

def refresh_wallpaper():
    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02
    result = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, None, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
    return result != 0

def restart_explorer():
    try:
        subprocess.run(["taskkill", "/im", "explorer.exe"], check=True)
        time.sleep(1)
        subprocess.Popen("explorer.exe")
        return True
    except Exception as e:
        print("Restart explorer error:", e)
        return False

def change_background():
    path = entry_var.get()
    if not os.path.isfile(path):
        messagebox.showerror("Error", "Selected file does not exist.")
        return

    if not set_wallpaper_registry(path):
        messagebox.showerror("Error", "Access denied: could not update registry.\nRun as administrator.")
        return

    if refresh_wallpaper():
        messagebox.showinfo("Success", "Background changed successfully!")
    else:
        if restart_explorer():
            messagebox.showinfo("Success", "Background changed successfully!")
        else:
            messagebox.showwarning("Warning", "Failed to restart Explorer automatically.\nRestart manually.")

def apply_advanced():
    if var_delete_wallpaper_policy.get():
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                winreg.DeleteValue(key, "Wallpaper")
            messagebox.showinfo("Success", "Wallpaper policy registry key deleted.")
        except FileNotFoundError:
            messagebox.showinfo("Info", "Wallpaper registry key does not exist.")
        except PermissionError:
            messagebox.showerror("Error", "Permission denied. Run as administrator.")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{e}")

    if var_nochangingwallpaper.get():
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                winreg.DeleteValue(key, "NoChangingWallPaper")
            messagebox.showinfo("Success", "NoChangingWallPaper registry key deleted.")
        except FileNotFoundError:
            messagebox.showinfo("Info", "NoChangingWallPaper registry key does not exist.")
        except PermissionError:
            messagebox.showerror("Error", "Permission denied. Run as administrator.")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{e}")

    if var_restart_explorer.get():
        if restart_explorer():
            messagebox.showinfo("Success", "Explorer restarted successfully.")
        else:
            messagebox.showerror("Error", "Failed to restart Explorer.")

def toggle_advanced():
    global advanced_open
    if advanced_open:
        advanced_frame.pack_forget()
        adv_toggle_btn.configure(text="▶ Advanced Options")
        root.geometry(f"{BASE_WIDTH}x{BASE_HEIGHT}")
        advanced_open = False
    else:
        advanced_frame.pack(fill='x', padx=20, pady=(5, 15))
        adv_toggle_btn.configure(text="▼ Advanced Options")
        root.geometry(f"{BASE_WIDTH}x{EXPANDED_HEIGHT}")
        advanced_open = True

# ------------------ UI ------------------
BASE_WIDTH = 560
BASE_HEIGHT = 250
EXPANDED_HEIGHT = 400

root = tk.Tk()
root.title(APP_TITLE)
root.geometry(f"{BASE_WIDTH}x{BASE_HEIGHT}")
root.resizable(False, False)

try:
    root.iconbitmap(resource_path(WINDOW_ICON))
except Exception:
    pass

# ---- Version check after Tk init ----
try:
    remote_version = get_remote_version(timeout_sec=3.0)
    prompt_if_outdated(_LOCAL_VERSION, remote_version)
except Exception:
    pass

style = ttk.Style(root)
try:
    style.theme_use('vista')
except:
    try:
        style.theme_use('clam')
    except:
        pass

# Header
header_frame = ttk.Frame(root, padding=(12, 15))
header_frame.pack(fill='x')

header_label = ttk.Label(header_frame, text="BackgroundBack", font=('Segoe UI', 18, 'bold'))
header_label.pack()

sub_label = ttk.Label(header_frame, text="A Background Restore Tool", font=('Segoe UI', 10))
sub_label.pack()

# Content Frame
content_frame = ttk.Frame(root, padding=(20, 10))
content_frame.pack(fill='x')

entry_var = tk.StringVar()
entry = ttk.Entry(content_frame, textvariable=entry_var, font=('Segoe UI', 10))
entry.pack(side='left', fill='x', expand=True, padx=(0, 10), ipady=3)

browse_btn = ttk.Button(content_frame, text="Browse Files", command=select_file)
browse_btn.pack(side='right')

# Buttons Frame
buttons_frame = ttk.Frame(root, padding=(20, 10))
buttons_frame.pack(fill='x')

exit_btn = ttk.Button(buttons_frame, text="Exit", command=root.destroy)
change_btn = ttk.Button(buttons_frame, text="Change Background", command=change_background)

exit_btn.pack(side='left', padx=(130, 10), ipadx=10, ipady=4)
change_btn.pack(side='left', padx=(10, 0), ipadx=10, ipady=4)

# Advanced Toggle
adv_toggle_btn = ttk.Button(root, text="▶ Advanced Options", command=toggle_advanced)
adv_toggle_btn.pack(anchor='w', padx=20, pady=(5, 0))

# Advanced Frame (hidden initially)
advanced_frame = ttk.Frame(root, padding=(20, 10), relief="groove", borderwidth=2)

var_delete_wallpaper_policy = tk.BooleanVar()
chk_delete_policy = ttk.Checkbutton(
    advanced_frame, text="Delete Wallpaper Policy Registry Key", variable=var_delete_wallpaper_policy
)
chk_delete_policy.pack(anchor='w', pady=3)

var_nochangingwallpaper = tk.BooleanVar()
chk_nochangingwallpaper = ttk.Checkbutton(
    advanced_frame, text="Delete NoChangingWallPaper Registry Key", variable=var_nochangingwallpaper
)
chk_nochangingwallpaper.pack(anchor='w', pady=3)

var_restart_explorer = tk.BooleanVar()
chk_restart_explorer = ttk.Checkbutton(
    advanced_frame, text="Restart Explorer After Changes", variable=var_restart_explorer
)
chk_restart_explorer.pack(anchor='w', pady=3)

apply_adv_btn = ttk.Button(advanced_frame, text="Apply Advanced", command=apply_advanced)
apply_adv_btn.pack(pady=(10, 5), ipadx=8, ipady=3)

# Track advanced state
advanced_open = False

# Key bindings
root.bind('<Return>', lambda e: change_background())
root.bind('<Escape>', lambda e: root.destroy())

root.mainloop()