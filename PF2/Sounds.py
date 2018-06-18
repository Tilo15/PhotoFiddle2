import subprocess
import threading


class SystemSounds:
    @staticmethod
    def play_sound(id):
        threading.Thread(target=SystemSounds.play_sound_blocking, args=(id,)).start()
        
    @staticmethod
    def play_sound_blocking(id):
        subprocess.call(['/usr/bin/canberra-gtk-play','--id',id])

    @staticmethod
    def window_attention():
        SystemSounds.play_sound("window-attention")

    @staticmethod
    def complete():
        SystemSounds.play_sound("complete")