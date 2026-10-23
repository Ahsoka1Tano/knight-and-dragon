from dataclasses import dataclass


@dataclass
class Animation:
    """Time-based atlas player; non-looping actions hold their final frame."""
    frames: list
    fps: float = 10
    loop: bool = True

    def frame(self, time):
        index = max(0, int(time * self.fps))
        index = index % len(self.frames) if self.loop else min(index, len(self.frames) - 1)
        return self.frames[index]
