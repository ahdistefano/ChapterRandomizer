#!/usr/bin/env python
import os
import sys
# Credits to https://stackoverflow.com/questions/59086193/pyinstaller-onedir-option-exe-file-outside-the-directory
if getattr(sys, 'frozen', False):
    app_path = os.path.join(os.path.dirname(sys.executable),"lib")
    sys.path.append(app_path) # search this path for modules
import time
import pathlib
import random
import argparse
import glob
import locale
from tkinter import Tk, Toplevel, filedialog, messagebox
from urllib.parse import unquote
from wakepy import keep
from pynput.keyboard import Key, Listener
from messages import get_message

VLC_SUPPORTED_EXT = ('.m2v', '.m4v', '.mpeg1', '.mpeg2', '.mts', '.ogm', '.divx', '.dv', '.flv', '.m1v', '.m2ts', '.mkv', \
                     '.mov', '.mpeg4', '.ts', '.3g2', '.avi', '.mpeg', '.mpg', '.3gp', '.wmv', '.asf', '.mp4', '.m4p')

sys_lang = locale.getdefaultlocale()[0].split("_")[0]

try:
    import vlc
except Exception:
    messagebox.showerror("Error", get_message('NO_VLC', sys_lang))
    sys.exit(1)

class ChapterRandomizer():
    """ Main class for the chapter randomizer """

    def __init__(self, folderPath=None, isNostalgic=False, tk_root=None):
        self.folderPath = folderPath
        self.isNostalgic = isNostalgic
        self.media_player = None
        self.tk_root = tk_root
        if self.folderPath:
            self.validatePath()
            self.validateVLC()
            self.main()

    def validatePath(self):
        """ Checks that the path passed is valid and contains playable files """
        isValidPath = False        
        while not isValidPath:
            recursivePath = os.path.join(self.folderPath, "**")
            if any(path.lower().endswith(VLC_SUPPORTED_EXT) for path in glob.glob(recursivePath, recursive=True)):
                isValidPath = True
            else:
                messagebox.showerror("Error", get_message('NO_VALID_FILES', sys_lang))
                self.folderPath = filedialog.askdirectory()
                if not self.folderPath:
                    sys.exit(0)

    def validateVLC(self):
        """ Validates that VLC is properly installed """
        try:
            vlc.find_lib()
        except Exception:
            messagebox.showerror("Error", get_message('NO_VLC', sys_lang))
            sys.exit(1)

    def chooseRandomFile(self):
        """ Chooses a random file from folderPath and returns the full path """        
        # TODO: Make this smarter. i.e. Don't repeat a chapter that was played recently
        recursivePath = os.path.join(self.folderPath, "**")
        files = [path for path in glob.glob(recursivePath, recursive=True) if path.lower().endswith(VLC_SUPPORTED_EXT)]
        randomFile = random.choice(files)
        return randomFile

    def on_press(self, key):
        """ Key press bindings

            +:  Forward video by 5 seconds
            -:  Rewind video by 5 seconds
        """
        if hasattr(key, "char"):
            if key.char == "+":
                self.media_player.set_time(self.media_player.get_time() + 5000)
            elif key.char == "-":
                self.media_player.set_time(self.media_player.get_time() - 5000)

    def on_release(self, key):
        """ Key release bindings

            Esc:    Exit application
            Space:  Pause/play video
        """
        if key == Key.esc:
            os._exit(0)
        elif key == Key.space:
            self.media_player.pause()

    def _playback_loop(self, currentTitle):
        """ Inner polling loop; returns updated currentTitle or raises on playback error """
        state = self.media_player.get_state()
        if state.value == vlc.State.Ended:
            file = self.chooseRandomFile()
            media = vlc.Media(file)
            self.media_player.set_media(media)
            self.media_player.play()
            if self.isNostalgic:
                self.media_player.video_set_logo_int(vlc.VideoLogoOption.logo_enable, 1)
            newTitle = self.media_player.get_media().get_mrl()
            newTitle = unquote(newTitle).split("/")[-1]
            if newTitle != currentTitle:
                print('Playing - "%s"' % newTitle)
                currentTitle = newTitle
        elif state == vlc.State.Error:
            messagebox.showerror("Error", get_message('PLAYBACK_ERR', sys_lang))
            sys.exit(1)
        return currentTitle

    def main(self):
        """ This does the whole thing """
        file = self.chooseRandomFile()

        media = vlc.Media(file)

        basePath = pathlib.Path(__file__).parent.resolve()
        self.logoPath = os.path.join(basePath, "assets", "t3lef3.png")

        is_wsl = sys.platform == "linux" and "microsoft" in os.uname().release.lower()

        if sys.platform=="win32":
            options = ["--no-xlib", "--codec=av1", "--avcodec-hw=dxva2", "--verbose=2"]
        elif is_wsl:
            # WSLg's Wayland compositor doesn't implement wl_shell set_fullscreen.
            # We embed VLC into a tkinter Toplevel window instead (tkinter has a
            # working X11 connection via XWayland even when VLC's xcb_window doesn't).
            options = ["--codec=av1", "--avcodec-hw=none", "--verbose=0",
                       "--avcodec-threads=4", "--avcodec-skiploopfilter=all",
                       "--avcodec-fast", "--drop-late-frames", "--skip-frames"]
        elif sys.platform=="linux":
            options = ["--no-xlib", "--codec=av1", "--avcodec-hw=none", "--verbose=0",
                       "--avcodec-threads=4", "--avcodec-skiploopfilter=all",
                       "--avcodec-fast", "--drop-late-frames", "--skip-frames"]
        else:
            options = ["--no-xlib", "--verbose=0",]

        if self.isNostalgic:
            options += [
                "--sub-source=logo",
                f"--logo-file={self.logoPath}",
                "--logo-position=6",
            ]

        self.instance = vlc.Instance(options)
        self.media_player = self.instance.media_player_new()

        video_win = None
        if is_wsl and self.tk_root:
            video_win = Toplevel(self.tk_root)
            video_win.attributes('-fullscreen', True)
            video_win.configure(background='black')
            video_win.update()
            self.media_player.set_xwindow(video_win.winfo_id())

        with keep.presenting():
            
            if self.isNostalgic:
                self.media_player.video_set_logo_string(vlc.VideoLogoOption.logo_file, self.logoPath)
                self.media_player.video_set_logo_int(vlc.VideoLogoOption.logo_position, 6)
                self.media_player.video_set_logo_int(vlc.VideoLogoOption.logo_enable, 1)

            self.media_player.set_media(media)
            if not is_wsl:
                self.media_player.set_fullscreen(True)
            self.media_player.play()

            currentTitle = ''
            while True:
                try:
                    with Listener(on_press=self.on_press, on_release=self.on_release):
                        while True:
                            currentTitle = self._playback_loop(currentTitle)
                            if video_win:
                                video_win.update()
                            time.sleep(0.5)
                except Exception as e:
                    # Xlib drops the display connection after long runtimes on Linux;
                    # recreating the Listener reopens the connection transparently.
                    if "ConnectionClosedError" in type(e).__name__ or "Broken pipe" in str(e):
                        print("X display connection lost, reconnecting keyboard listener...")
                        time.sleep(2)
                        continue
                    raise e

def main(path=None, nostalgia=None):
    """ Main function """
    tk_root = Tk()
    tk_root.withdraw()
    if not path:
        path = filedialog.askdirectory()
        if not path:
            sys.exit(0)
    if not nostalgia:
        isNostalgic = messagebox.askyesno("Nostalgia", get_message('NOSTALGIA', sys_lang))
    else:
        isNostalgic = (nostalgia.lower() == "y")
    ChapterRandomizer(path, isNostalgic, tk_root)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set the full folder path containing the chapters you want to shuffle.")
    parser.add_argument("-p", "--Path", help="Folder Path")
    parser.add_argument("-n", "--Nostalgia", help="True Nostalgia ('Y' or 'N')")
    args = parser.parse_args()
    main(path=args.Path, nostalgia=args.Nostalgia)