import random
from .characters import Knight, Dragon


class Encounter:
    """Simulation independent of rendering, audio, and event polling."""
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.knight, self.dragon = Knight(), Dragon(self.rng)
        self.ending = None
        self.events = []
        self.age = 0.
        self.jump_pending = False

    def emit(self, kind, x, y, value=None):
        self.events.append((kind, x, y, value))

    def finish(self, ending):
        if self.ending is not None:
            return False
        self.ending = ending
        if ending == "slayer":
            self.knight.add_gold(self.dragon.gold)
        self.emit("ending", self.knight.x, self.knight.y, ending)
        return True

    def action(self, action):
        if self.ending or self.age < .75:
            return
        k, d = self.knight, self.dragon
        if action == "attack" and k.attack():
            self.emit("sword", k.x, k.y - 28)
        elif action == "guard" and k.defend():
            self.emit("guard", k.x, k.y - 20)
        elif action == "heal":
            amount = k.use_zelka()
            self.emit("heal" if amount else "message", k.x, k.y - 52,
                      amount if amount else "Здоровье полное" if k.zelka else "Зелья закончились")
        elif action == "jump":
            self.jump_pending = True
        elif action == "interact":
            if d.health and abs(k.x - d.x) < 123 and k.grounded:
                k.propose()
                self.finish("love")
            elif k.x < 65:
                self.finish("escape")
            else:
                self.emit("message", k.x, k.y - 60, "Подойди ближе")

    def update(self, dt, direction=0):
        if self.ending:
            return
        # Bounded substeps keep attack windows and physics reliable after a stall.
        left = min(dt, .25)
        while left > 1e-8 and not self.ending:
            step = min(left, 1 / 120)
            self._step(step, direction)
            left -= step

    def _step(self, dt, direction):
        self.age += dt
        k, d = self.knight, self.dragon
        k.update(dt, direction if self.age > .75 else 0, self.jump_pending)
        self.jump_pending = False
        d.hurt_time = max(0, d.hurt_time - dt)
        # The solid torso can be approached from either side or jumped over.
        if k.rect.colliderect(d.rect.inflate(-78, -12)):
            k.x = d.x - 35 if k.x < d.x else d.x + 35
        if k.x <= 19 and self.age > .8:
            self.finish("escape")
            return
        elapsed = .46 - k.attack_time
        if k.attack_time and .13 <= elapsed <= .28 and not k.attack_connected:
            if k.sword_hitbox.colliderect(d.rect):
                k.attack_connected = True
                damage = d.take_damage(k.weapon)
                self.emit("hit_dragon", d.x - 35, d.y - 75, damage)
                if not d.health:
                    self.finish("slayer")
                    return
        self._dragon(dt)
        if not k.health:
            self.finish("fallen")

    def _dragon(self, dt):
        k, d = self.knight, self.dragon
        d.phase_time += dt
        distance = abs(k.x - d.x)
        if d.phase == "rest":
            d.cooldown -= dt
            d.facing = -1 if k.x < d.x else 1
            if distance > 160 and d.cooldown > .5:
                d.x += d.facing * 23 * dt
                d.x = max(300, min(536, d.x))
                d.animate("walk", dt)
            else:
                d.animate("idle", dt)
            if d.cooldown <= 0:
                roll = d.rng.random()
                d.action = "roar" if roll < .2 else "claw" if distance < 145 else "fire"
                d.phase, d.phase_time, d.connected = "windup", 0., False
                self.emit("warning", d.x, d.y - 142, d.action)
        elif d.phase == "windup":
            d.animate("windup_" + d.action, dt)
            if d.phase_time >= (.9 if d.action == "fire" else .65):
                d.phase, d.phase_time = "active", 0.
                self.emit(d.action, d.x, d.y - 70)
        elif d.phase == "active":
            d.animate(d.action, dt)
            if d.action != "roar" and not d.connected and d.attack_hitbox.colliderect(k.rect):
                d.connected = True
                shielded = k.shield
                damage = k.take_damage(d.fire_attack() if d.action == "fire" else d.attack())
                if damage:
                    self.emit("blocked" if shielded else "hit_knight", k.x, k.y - 36, damage)
            if d.phase_time > (.48 if d.action == "fire" else .32 if d.action == "claw" else .85):
                d.phase, d.phase_time, d.cooldown = "rest", 0., d.rng.uniform(1.15, 1.75)
