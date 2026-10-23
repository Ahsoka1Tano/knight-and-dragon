"""The original Character / Knight / Dragon API, adapted for real time."""
import random
import pygame
from .settings import GROUND


class Character:
    def __init__(self, name, health, weapon, x):
        self.name, self.health, self.max_health = name, health, health
        self.weapon, self.x, self.y = weapon, float(x), float(GROUND)
        self.facing = 1
        self.state, self.anim_time = "idle", 0.0
        self.hurt_time = 0.0

    def animate(self, state, dt):
        if state != self.state:
            self.state, self.anim_time = state, 0.0
        else:
            self.anim_time += dt

    def take_damage(self, damage):
        actual = min(self.health, max(0, damage))
        self.health -= actual
        self.hurt_time = .22
        return actual

    def heal(self, amount_health):
        before = self.health
        self.health = min(self.max_health, self.health + amount_health)
        return self.health - before


class Knight(Character):
    def __init__(self):
        super().__init__("Пикми 2000", 100, 25, 138)
        self.zelka, self.shield, self.gold = 3, False, 0
        self.vy = 0.0
        self.attack_time = self.attack_cooldown = self.invulnerable = 0.0
        self.shield_cooldown = 0.0
        self.attack_connected = False

    @property
    def rect(self):
        return pygame.Rect(round(self.x) - 10, round(self.y) - 43, 20, 43)

    @property
    def grounded(self):
        return self.y >= GROUND

    def attack(self):
        if self.health and self.attack_cooldown <= 0:
            self.attack_time, self.attack_cooldown = .46, .56
            self.attack_connected = False
            self.state, self.anim_time = "attack", 0
            return True
        return False

    @property
    def sword_hitbox(self):
        return pygame.Rect(round(self.x) + (7 if self.facing == 1 else -65),
                           round(self.y) - 46, 58, 42)

    def defend(self):
        if self.health and self.shield_cooldown <= 0:
            self.shield = True
            self.shield_cooldown = .7
            return True
        return False

    def use_zelka(self):
        if self.zelka and 0 < self.health < self.max_health:
            self.zelka -= 1
            return self.heal(30)
        return 0

    def take_damage(self, damage):
        if self.invulnerable > 0 or not self.health:
            return 0
        if self.shield:
            damage //= 2
            self.shield = False
        self.invulnerable = .65
        return super().take_damage(damage)

    def add_gold(self, gold):
        self.gold += gold

    def propose(self):
        self.state, self.anim_time = "propose", 0
        return "Дракон, выйдешь за меня?"

    def update(self, dt, direction=0, jump=False):
        for name in ("attack_cooldown", "attack_time", "invulnerable", "hurt_time", "shield_cooldown"):
            setattr(self, name, max(0., getattr(self, name) - dt))
        if jump and self.grounded:
            self.vy = -310
        self.vy += 850 * dt
        self.y += self.vy * dt
        if self.y >= GROUND:
            self.y, self.vy = float(GROUND), 0
        if direction and not self.attack_time:
            self.facing = 1 if direction > 0 else -1
        self.x = max(16, min(620, self.x + direction * (65 if self.attack_time else 126) * dt))
        state = ("attack" if self.attack_time else "hurt" if self.hurt_time else
                 "walk" if direction else "guard" if self.shield else "idle")
        self.animate(state, dt)


class Dragon(Character):
    def __init__(self, rng=None):
        super().__init__("Змейка", 200, 25, 472)
        self.fire, self.gold, self.facing = 45, 500, -1
        self.rng = rng or random.Random()
        self.phase, self.phase_time, self.cooldown = "rest", 0., 1.7
        self.action, self.connected = "claw", False

    @property
    def rect(self):
        return pygame.Rect(round(self.x) - 62, round(self.y) - 103, 124, 103)

    def attack(self):
        return self.rng.randint(10, self.weapon)

    def fire_attack(self):
        return self.rng.randint(10, self.fire)

    def roar(self):
        return "МЯУ!"

    @property
    def attack_hitbox(self):
        reach = 234 if self.action == "fire" else 120
        x = self.x - reach if self.facing < 0 else self.x + 25
        y, h = (self.y - 67, 58) if self.action == "fire" else (self.y - 34, 34)
        return pygame.Rect(round(x), round(y), reach - 25, h)
