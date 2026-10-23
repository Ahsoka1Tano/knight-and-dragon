import hashlib
import os
from pathlib import Path
import unittest

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')

from pixel_knight_dragon.characters import Knight, Dragon
from pixel_knight_dragon.combat import Encounter
from pixel_knight_dragon.settings import GROUND, ROOT, ORIGINAL_SHA256


def advance(enc,seconds,direction=0):
    for _ in range(round(seconds*120)):
        enc.update(1/120,direction)


class CombatTests(unittest.TestCase):
    def encounter(self):
        e=Encounter(7)
        e.age=1
        e.dragon.cooldown=100
        return e

    def test_original_is_byte_identical(self):
        original=ROOT.parent/'knight and dragon.py'
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),ORIGINAL_SHA256)

    def test_original_stats(self):
        k,d=Knight(),Dragon()
        self.assertEqual((k.health,k.weapon,k.zelka,k.gold),(100,25,3,0))
        self.assertEqual((d.health,d.weapon,d.fire,d.gold),(200,25,45,500))

    def test_heal_cap_and_no_wasted_potions(self):
        k=Knight()
        self.assertEqual(k.use_zelka(),0)
        self.assertEqual(k.zelka,3)
        k.health=85
        self.assertEqual(k.use_zelka(),15)
        self.assertEqual(k.health,100)
        for _ in range(2):
            k.health=10
            self.assertEqual(k.use_zelka(),30)
        self.assertEqual(k.use_zelka(),0)
        self.assertEqual(k.zelka,0)

    def test_next_damage_halved_once(self):
        k=Knight()
        k.defend()
        self.assertEqual(k.take_damage(25),12)
        self.assertFalse(k.shield)
        k.invulnerable=0
        self.assertEqual(k.take_damage(25),25)
        self.assertEqual(k.health,63)

    def test_short_invulnerability(self):
        k=Knight()
        k.take_damage(10)
        self.assertEqual(k.take_damage(45),0)
        self.assertEqual(k.health,90)

    def test_miss_from_far_away(self):
        e=self.encounter()
        e.action('attack')
        advance(e,.7)
        self.assertEqual(e.dragon.health,200)

    def test_one_sword_hit_per_animation(self):
        e=self.encounter()
        e.knight.x=e.dragon.x-95
        e.action('attack')
        advance(e,.5)
        self.assertEqual(e.dragon.health,175)
        self.assertEqual(sum(x[0]=='hit_dragon' for x in e.events),1)

    def test_cooldown_prevents_spam(self):
        e=self.encounter()
        e.knight.x=e.dragon.x-95
        for _ in range(25):
            e.action('attack')
            e.update(1/120)
        self.assertEqual(e.dragon.health,175)

    def test_sword_must_face_dragon(self):
        e=self.encounter()
        e.knight.x=e.dragon.x-95
        e.knight.facing=-1
        e.action('attack')
        advance(e,.5)
        self.assertEqual(e.dragon.health,200)

    def test_jump_and_floor_collision(self):
        e=self.encounter()
        e.action('jump')
        advance(e,.2)
        self.assertLess(e.knight.y,GROUND-30)
        advance(e,1)
        self.assertEqual(e.knight.y,GROUND)
        self.assertEqual(e.knight.vy,0)

    def test_attack_random_damage_bounds(self):
        d=Dragon()
        claws=[d.attack() for _ in range(300)]
        fire=[d.fire_attack() for _ in range(300)]
        self.assertTrue(all(10<=x<=25 for x in claws))
        self.assertTrue(all(10<=x<=45 for x in fire))

    def test_telegraph_before_damage(self):
        e=self.encounter()
        e.knight.x=e.dragon.x-100
        e.dragon.cooldown=0
        advance(e,.4)
        self.assertEqual(e.dragon.phase,'windup')
        self.assertEqual(e.knight.health,100)

    def test_dragon_attack_hits_only_once(self):
        e=self.encounter()
        e.knight.x=e.dragon.x-95
        d=e.dragon
        d.phase,d.action,d.phase_time='active','claw',0
        advance(e,.31)
        hp=e.knight.health
        self.assertTrue(75<=hp<=90)
        advance(e,.3)
        self.assertEqual(e.knight.health,hp)

    def test_jump_evades_claw(self):
        e=self.encounter()
        e.knight.x=e.dragon.x-95
        e.action('jump')
        advance(e,.22)
        e.dragon.phase,e.dragon.action,e.dragon.phase_time='active','claw',0
        advance(e,.25)
        self.assertEqual(e.knight.health,100)

    def test_slayer_ending_and_reward_exactly_once(self):
        e=self.encounter()
        e.knight.x=e.dragon.x-95
        e.dragon.health=25
        e.action('attack')
        advance(e,.5)
        self.assertEqual(e.ending,'slayer')
        self.assertEqual(e.knight.gold,500)
        self.assertFalse(e.finish('slayer'))
        e.action('attack')
        advance(e,1)
        self.assertEqual(e.knight.gold,500)
        self.assertEqual(sum(x[0]=='ending' for x in e.events),1)

    def test_fallen_ending(self):
        e=self.encounter()
        e.knight.x=e.dragon.x-95
        e.knight.health=1
        e.dragon.phase,e.dragon.action='active','claw'
        advance(e,.2)
        self.assertEqual(e.ending,'fallen')
        self.assertEqual(e.knight.health,0)

    def test_love_always_accepts_at_close_range(self):
        for seed in range(20):
            e=Encounter(seed)
            e.age=1
            e.knight.x=e.dragon.x-110
            e.action('interact')
            self.assertEqual(e.ending,'love')
            self.assertEqual(e.knight.state,'propose')

    def test_proposal_from_distance_does_not_finish(self):
        e=self.encounter()
        e.action('interact')
        self.assertIsNone(e.ending)

    def test_escape_by_walking_or_interaction(self):
        e=self.encounter()
        e.knight.x=21
        advance(e,.1,-1)
        self.assertEqual(e.ending,'escape')
        e=self.encounter()
        e.knight.x=50
        e.action('interact')
        self.assertEqual(e.ending,'escape')

    def test_restart_is_fresh_simulation(self):
        e=self.encounter()
        e.finish('slayer')
        e=Encounter()
        self.assertIsNone(e.ending)
        self.assertEqual((e.knight.health,e.dragon.health,e.knight.gold),(100,200,0))


if __name__=='__main__':
    unittest.main()
