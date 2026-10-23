import json
import pygame
from .settings import ASSETS
from .animation import Animation


class Resources:
    def __init__(self):
        self.animations = {}
        manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
        for actor, states in manifest.items():
            self.animations[actor] = {}
            for state, data in states.items():
                sheet = pygame.image.load(str(ASSETS / data["file"])).convert_alpha()
                w, h = data["size"]
                frames = [sheet.subsurface((i * w, 0, w, h)).copy() for i in range(data["count"])]
                self.animations[actor][state] = Animation(frames, data["fps"], data["loop"])
        self.cave = pygame.transform.scale(pygame.image.load(str(ASSETS / "sanctuary.png")).convert(), (640, 360))
        self.wedding = pygame.image.load(str(ASSETS / "wedding.png")).convert()
        self.escape = pygame.image.load(str(ASSETS / "escape.png")).convert()
        self.fonts = {}

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            filename = "font_bold.ttf" if bold else "font.ttf"
            self.fonts[key] = pygame.font.Font(str(ASSETS / filename), size)
        return self.fonts[key]

    def sprite(self, actor, state, time, facing=1):
        states = self.animations[actor]
        animation = states.get(state, states["idle"])
        frame = animation.frame(time)
        # Both source atlases face right. Flip without filtering.
        return pygame.transform.flip(frame, True, False) if facing < 0 else frame


class Audio:
    def __init__(self):
        self.enabled = False
        self.muted = False
        self.sounds = {}
        self.track = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            pygame.mixer.set_num_channels(16)
            for path in (ASSETS / "audio").glob("*.wav"):
                self.sounds[path.stem] = pygame.mixer.Sound(str(path))
            self.channel = pygame.mixer.Channel(0)
            self.enabled = True
        except pygame.error:
            pass

    def music(self, name):
        if self.track == name:
            return
        self.track = name
        if self.enabled:
            self.channel.play(self.sounds[name], loops=-1, fade_ms=600)
            self.channel.set_volume(0 if self.muted else .35)

    def play(self, name):
        if self.enabled and not self.muted and name in self.sounds:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.set_volume(.55)
                channel.play(self.sounds[name])

    def toggle(self):
        self.muted = not self.muted
        if self.enabled:
            pygame.mixer.stop()
            self.track, track = None, self.track
            if track:
                self.music(track)
