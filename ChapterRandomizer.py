import os
import sys

# Credits to https://stackoverflow.com/questions/59086193/pyinstaller-onedir-option-exe-file-outside-the-directory
if getattr(sys, 'frozen', False):
    app_path = os.path.join(os.path.dirname(sys.executable),"lib")
    sys.path.append(app_path) # search this path for modules

import time
import random
import argparse
import glob
import locale
from tkinter import Tk, filedialog, messagebox
from urllib.parse import unquote
from wakepy import keepawake
from pynput.keyboard import Key, Listener

VLC_SUPPORTED_EXT = ('.m2v', '.m4v', '.mpeg1', '.mpeg2', '.mts', '.ogm', '.divx', '.dv', '.flv', '.m1v', '.m2ts', '.mkv', \
                     '.mov', '.mpeg4', '.ts', '.3g2', '.avi', '.mpeg', '.mpg', '.3gp', '.wmv', '.asf', '.mp4', '.m4p')

sys_lang = locale.getdefaultlocale()[0].split("_")[0]

try:
    import vlc
except Exception:
    if sys_lang == "es":
        msg = "No se pudo encontrar VLC. Por favor checkeá que esté bien instalado."
    else:
        msg = "Failed to detect VLC. Please check it's properly installed."
    messagebox.showerror("Error", msg)
    sys.exit(1)

class ChapterRandomizer():
    """ Main class for the chapter randomizer """

    def __init__(self, folderPath=None, isNostalgic=False):
        self.folderPath = folderPath
        self.isNostalgic = isNostalgic
        self.media_player = None
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
                if sys_lang == "es":
                    msg = "La carpeta especificada no contiene ningún archivo válido. Por favor intente de nuevo"
                else:
                    msg = "The specified path does not contain any playable files. Please try again."
                messagebox.showerror("Error", msg)
                self.folderPath = filedialog.askdirectory()
                if not self.folderPath:
                    sys.exit(0)

    def validateVLC(self):
        """ Validates that VLC is properly installed """
        try:
            vlc.find_lib()
        except Exception:
            if sys_lang == "es":
                msg = "No se pudo encontrar VLC. Por favor checkeá que esté bien instalado."
            else:
                msg = "Failed to detect VLC. Please check it's properly installed."
            messagebox.showerror("Error", msg)
            sys.exit(1)

    def chooseRandomFile(self):
        """ Chooses a random file from folderPath and returns the full path """        
        # TODO: Make this smarter. i.e. Don't repeat a chapter that was played recently
        recursivePath = os.path.join(self.folderPath, "**")
        files = [path for path in glob.glob(recursivePath, recursive=True) if path.lower().endswith(VLC_SUPPORTED_EXT)]
        randomFile = random.choice(files)
        return randomFile

    def on_press(self, key):
        """ Key press bindings"""
        if hasattr(key, "char"):
            if key.char == "+":
                self.media_player.set_time(self.media_player.get_time() + 5000)
            elif key.char == "-":
                self.media_player.set_time(self.media_player.get_time() - 5000)

    def on_release(self, key):
        """ Key release bindings"""
        if key == Key.esc:
            os._exit(0)
        elif key == Key.space:
            self.media_player.pause()

    def main(self):
        """ This does the whole thing """
        file = self.chooseRandomFile()

        with keepawake(keep_screen_awake=True):
            media = vlc.Media(file)
            self.media_player = vlc.MediaPlayer()
            if self.isNostalgic:
                logoPath = os.path.abspath("./assets/t3lef3.png")
                self.media_player.video_set_logo_int(vlc.VideoLogoOption.logo_enable, 1)
                self.media_player.video_set_logo_string(vlc.VideoLogoOption.logo_file, logoPath)
                self.media_player.video_set_logo_int(vlc.VideoLogoOption.logo_position, 6)
            self.media_player.set_media(media)
            self.media_player.video_set_key_input(True)
            self.media_player.video_set_mouse_input(True)
            self.media_player.set_fullscreen(True)
            self.media_player.play()

            currentTitle = ''
            with Listener(on_press=self.on_press, on_release=self.on_release):
                while True:
                    state = self.media_player.get_state()
                    if state == vlc.State.Error:
                        break
                    elif state.value == vlc.State.Ended:
                        file = self.chooseRandomFile()
                        media = vlc.Media(file)
                        self.media_player.set_media(media)
                        self.media_player.play()
                    newTitle = self.media_player.get_media().get_mrl()
                    newTitle = unquote(newTitle).split("/")[-1]
                    if newTitle != currentTitle:
                        print('Playing - "%s"' % newTitle)
                        currentTitle = newTitle
                    time.sleep(0.5)

def main(path=None, nostalgia=None):
    """ Main function """
    Tk().withdraw()
    if not path:
        path = filedialog.askdirectory()
        if not path:
            sys.exit(0)
    if not nostalgia:
        if sys_lang == "es":
            msg = "¿Activar nostalgia?"
        else:
            msg = "Enable nostalgia? (Note this will make sense for Arg people mostly)"
        isNostalgic = messagebox.askyesno("Nostalgia", msg)
    else:
        isNostalgic = (nostalgia.lower() == "y")
    ChapterRandomizer(path, isNostalgic)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set the full folder path containing the chapters you want to shuffle.")
    parser.add_argument("-p", "--Path", help="Folder Path")
    parser.add_argument("-n", "--Nostalgia", help="True Nostalgia ('Y' or 'N')")
    args = parser.parse_args()
    main(path=args.Path, nostalgia=args.Nostalgia)