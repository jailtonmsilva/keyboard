"""Player de audio usando MCI nativo do Windows."""

from __future__ import annotations

import ctypes


class MCIPlayer:
    def __init__(self, alias: str = "lovebgm", volume: int = 700) -> None:
        self.alias = alias
        self.music_ready = False
        self.is_playing = False
        self.is_paused = False
        self.is_muted = False
        self.volume_level = volume
        self.previous_volume = volume

    def send(self, command: str):
        buffer = ctypes.create_unicode_buffer(255)
        error_code = ctypes.windll.winmm.mciSendStringW(command, buffer, 254, 0)
        return error_code, buffer.value

    def init_loop(self, audio_path: str) -> bool:
        open_cmd = f'open "{audio_path}" type mpegvideo alias {self.alias}'
        error_code, _ = self.send(open_cmd)
        if error_code != 0:
            return False

        self.send(f"setaudio {self.alias} volume to {self.volume_level}")
        self.send(f"play {self.alias} repeat")
        self.music_ready = True
        self.is_playing = True
        self.is_paused = False
        return True

    def toggle_play_stop(self) -> None:
        if not self.music_ready:
            return

        if self.is_playing:
            self.send(f"stop {self.alias}")
            self.is_playing = False
            self.is_paused = False
            return

        self.send(f"play {self.alias} repeat")
        self.is_playing = True
        self.is_paused = False

    def pause_music(self) -> None:
        if not self.music_ready or not self.is_playing:
            return

        if self.is_paused:
            self.send(f"resume {self.alias}")
            self.is_paused = False
            return

        self.send(f"pause {self.alias}")
        self.is_paused = True

    def toggle_volume(self) -> None:
        if not self.music_ready:
            return

        if self.is_muted:
            self.volume_level = self.previous_volume
            self.send(f"setaudio {self.alias} volume to {self.volume_level}")
            self.is_muted = False
            return

        self.previous_volume = self.volume_level
        self.send(f"setaudio {self.alias} volume to 0")
        self.is_muted = True

    def close(self) -> None:
        if not self.music_ready:
            return

        self.send(f"stop {self.alias}")
        self.send(f"close {self.alias}")
        self.music_ready = False
