import random

class Character:
    def __init__(self, name, health, weapon):
        self.name = name
        self.health = health
        self.max_health = health
        self.weapon = weapon

    def attack(self):
        print(f'{self.name} атакует')
        return self.weapon

    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0

    def heal(self, amount_health):
        self.health += amount_health
        if self.health > self.max_health:
            self.health = self.max_health

    def show_info(self):
        print(f'Ник - {self.name}')
        print(f'Здоровье - {self.health}')
        print(f'Ружка - {self.weapon}')


class Knight(Character):
    def __init__(self, name, health, weapon):
        self.name = name
        self.health = health
        self.max_health = health
        self.weapon = weapon

        self.zelka = 3
        self.shield = False
        self.gold = 0

    def use_zelka(self):
        if self.zelka > 0:
            self.zelka -= 1
            self.heal(30)
            print(f'{self.name} выпил зельку')
        else:
            print(f'Нету зельки')

    def defend(self):
        self.shield = True
        print(f'{self.name} поднял ШИТ')

    def take_damage(self, damage):
        if self.shield:
            damage = damage // 2
            self.shield = False
            print('ШИТ уменьшил урон вдвое')

        self.health -= damage

        if self.health < 0:
            self.health = 0

        print(f'{self.name} получил {damage} урона')
        print(f'Осталось здоровья: {self.health}/{self.max_health}')

    def propose(self):
        print(f'{self.name} встал на колено')
        print(f'Дракон, выйдешь за меня?')

    def inventory(self):
        print(f'Зелья: {self.zelka}')
        print(f'Золото: {self.gold}')
        print(f'Оружие: {self.weapon}')

    def add_gold(self, gold):
        self.gold += gold
        print(f'Сегодня {self.name} башляет')


class Dragon(Character):
    def __init__(self, name, health, weapon):
        self.name = name
        self.health = health
        self.max_health = health
        self.weapon = weapon

        self.fire = 45
        self.gold = 500

    def attack(self):
        damage = random.randint(10, self.weapon)
        print(f'{self.name} атакует маникюром. Урон: {damage}')
        return damage

    def fire_attack(self):
        damage = random.randint(10, self.fire)
        print(f'{self.name} атакует огнем. Урон {damage}')
        return damage

    def roar(self):
        print('RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR МЯУ')

    def show_info(self):
        print(f'Имя - {self.name}')
        print(f'Здоровье - {self.health}/{self.max_health}')
        print(f'Урон когтей - до {self.weapon}')
        print(f'Урон огня - до {self.fire}')
        print(f'Золото - {self.gold}')


class Game:
    def __init__(self):
        self.knight = Knight('Пикми 2000', 100, 25)
        self.dragon = Dragon('Змейка', 200, 25)
        self.running = True
        self.turn = 1

    def menu(self):
        print(f'\n========== ХОД {self.turn} ==========')

        print('\nРЫЦАРЬ:')
        self.knight.show_info()

        print('\nДРАКОН:')
        self.dragon.show_info()

        print('''
    Выберите действие:

    1. Атаковать
    2. Поднять щит
    3. Выпить зельку
    4. Сделать предложение дракону
    5. Сбежать
    6. Инвентарь
    ''')

    def player_turn(self):
        choice = input('Твой выбор, герой: ')
        if choice == '1':
            damage = self.knight.attack()
            self.dragon.take_damage(damage)

            if self.dragon.health == 0:
                self.knight.add_gold(self.dragon.gold)
                print('КОНЦОВКА: УБИЙЦА ДРАКОНА')
                self.running = False

        elif choice == '2':
            self.knight.defend()

        elif choice == '3':
            if self.knight.zelka == 0:
                print('Зельки закончились')
                return False
            if self.knight.health == self.knight.max_health:
                print('ХПешка уже полная')
                return False
            self.knight.use_zelka()

        elif choice == '4':
            self.knight.propose()
            print('Дракон согласился! Они поженились!')
            print('КОНЦОВКА: ЛЮБОВЬ ПОБЕДИЛА')
            self.running = False

        elif choice == '5':
            print(f'{self.knight.name} сбежал от дракона')
            print('КОНЦОВКА: ТРУСЛИВЫЙ ПИКМИ')
            self.running = False

        elif choice == '6':
            self.knight.inventory()
            return False

        else:
            print('не правильное действие, чудило')
            return False
        return True

    def dragon_turn(self):
        action = random.randint(1, 5)
        if action == 1 or action == 3:
            damage = self.dragon.attack()
            self.knight.take_damage(damage)
        elif action == 2 or action == 4:
            damage = self.dragon.fire_attack()
            self.knight.take_damage(damage)
        else:
            self.dragon.roar()

        if self.knight.health == 0:
            print('КОНЦОВКА: ПИКМИ НЕ ВЫЖИЛ')
            self.running = False

    def start(self):
        print('ДОБРО ПОЖАЛОВАТЬ В РЫЦАРЬ И ДРАКОН')

        while self.running:
            self.menu()

            res = self.player_turn()
            if res == False:
                continue
            if self.running == False:
                break
            self.dragon_turn()
            self.turn += 1
        print('КОНЕЦ')

game = Game()
game.start()