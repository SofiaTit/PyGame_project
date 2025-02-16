import pygame
import sys
import random
import time

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAVITY = 0.8
JUMP_HEIGHT = -17

# Настройка экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Coin Runner")
clock = pygame.time.Clock()

# Загрузка изображений
fon = pygame.image.load("data/fon.png").convert()
fon1 = pygame.image.load("data/fon1.png").convert()
fon2 = pygame.image.load("data/fon2.png").convert()
fon3 = pygame.image.load("data/fon3.png").convert()
fon4 = pygame.image.load("data/fon4.png").convert()
fon_game = [fon1, fon2, fon3, fon4]

player1_img = pygame.image.load("data/game1.png").convert_alpha()
player2_img = pygame.image.load("data/game2.png").convert_alpha()
player3_img = pygame.image.load("data/game3.png").convert_alpha()

coin_img = pygame.image.load("data/coin.png").convert_alpha()
explosion_img = pygame.image.load("data/explosion.png").convert_alpha()
bonus_life_img = pygame.image.load("data/bonus_life.png").convert_alpha()
bonus_shield_img = pygame.image.load("data/bonus_shield.png").convert_alpha()

obstacles = {
    "tree": pygame.image.load("data/tree.png").convert_alpha(),
    "tree2": pygame.image.load("data/tree_2.png").convert_alpha(),
    "tree3": pygame.image.load("data/tree_3.png").convert_alpha(),
    "tree4": pygame.image.load("data/tree_4.png").convert_alpha(),

    "rock": pygame.image.load("data/rock.png").convert_alpha(),
    "rock2": pygame.image.load("data/rock_2.png").convert_alpha(),

    "bush": pygame.image.load("data/stone.png").convert_alpha(),
    "bush2": pygame.image.load("data/stone_2.png").convert_alpha(),
    "bush3": pygame.image.load("data/stone_3.png").convert_alpha(),

}

# Загрузка звуков
pygame.mixer.music.load("data/background_music.mp3")
jump_sound = pygame.mixer.Sound("data/jump.wav")
coin_sound = pygame.mixer.Sound("data/coin.wav")
collision_sound = pygame.mixer.Sound("data/collision.wav")
level_up_sound = pygame.mixer.Sound("data/level_up.wav")


# Класс анимированного спрайта
class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, animation_speed=5):
        super().__init__()
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect().move(x, y)
        self.animation_speed = animation_speed
        self.frame_counter = 0

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self):
        self.frame_counter += 1
        if self.frame_counter >= self.animation_speed:
            self.frame_counter = 0
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]


# Класс игрока
class Player(pygame.sprite.Sprite):
    def __init__(self, animations, x, y):
        super().__init__()
        self.animations = animations
        self.current_animation = "run"
        self.image = self.animations[self.current_animation].frames[0]
        self.rect = self.image.get_rect().move(x, HEIGHT - 100 - self.image.get_height())
        self.vel_y = 0
        self.is_jumping = False
        self.is_ducking = False
        self.is_dead = False
        self.lives = 3
        self.shield = False
        self.shield_end_time = 0
        self.is_colliding = False
        self.shield_effect = False

    def update(self):
        if not self.is_dead:
            if self.shield and time.time() > self.shield_end_time:
                self.shield = False
                self.current_animation = "run"
                self.shield_effect = False

            self.animations[self.current_animation].update()
            self.image = self.animations[self.current_animation].image
            self.rect = self.image.get_rect(center=self.rect.center)

            if self.is_jumping:
                self.vel_y += GRAVITY
                self.rect.y += self.vel_y
                if self.rect.bottom >= HEIGHT - 100:
                    self.rect.bottom = HEIGHT - 100
                    self.is_jumping = False
                    self.current_animation = "run"

    def jump(self):
        if not self.is_jumping and not self.is_ducking and not self.is_dead:
            self.is_jumping = True
            self.vel_y = JUMP_HEIGHT
            self.current_animation = "jump"
            jump_sound.play()

    def stand(self):
        self.is_ducking = False
        self.current_animation = "run"

    def lose_life(self):
        if not self.is_dead and not self.is_colliding and not self.shield:
            self.lives -= 1
            if self.lives <= 0:
                self.is_dead = True
            else:
                self.current_animation = "hit"  # Проигрываем анимацию поражения
                self.is_colliding = True
                pygame.time.set_timer(pygame.USEREVENT, 500)
            collision_sound.play()

    def activate_shield(self):
        self.shield = True
        self.shield_end_time = time.time() + 5
        self.shield_effect = True

    def add_life(self):
        self.lives += 1


# Класс препятствия
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, image, speed):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH
        self.rect.y = HEIGHT - 100 - self.rect.height
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


# Класс монеты
class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = coin_img
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH
        self.rect.y = random.choice([HEIGHT - 150, HEIGHT - 200, HEIGHT - 250])
        self.speed = 5

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


# Класс бонуса
class Bonus(pygame.sprite.Sprite):
    def __init__(self, image, effect):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH
        self.rect.y = random.choice([HEIGHT - 150, HEIGHT - 200, HEIGHT - 250])
        self.speed = 5
        self.effect = effect

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


# Класс частиц для перехода на следующий уровень
class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, dx, dy):
        super().__init__()
        self.image = explosion_img
        self.rect = self.image.get_rect(center=pos)
        self.velocity = [dx, dy]
        self.gravity = 0.1

    def update(self):
        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect(pygame.Rect(0, 0, WIDTH, HEIGHT)):
            self.kill()


# Класс дождя на четным уровнях
class Rain(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((2, 10))
        self.image.fill((100, 100, 255))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH)
        self.rect.y = random.randint(-HEIGHT, 0)
        self.speed = random.randint(5, 10)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()


# Функция создания взрыва
def create_particles(position, particles_group):
    particle_count = 20
    numbers = range(-5, 6)
    for _ in range(particle_count):
        particle = Particle(position, random.choice(numbers), random.choice(numbers))
        particles_group.add(particle)


# Функция защиты игрока
def draw_shield_effect(screen, player):
    if player.shield_effect:
        shield_radius = 50
        shield_color = (0, 255, 255)
        shield_alpha = 128

        shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(shield_surface, (*shield_color, shield_alpha), (shield_radius, shield_radius), shield_radius)

        shield_pos = (player.rect.centerx - shield_radius, player.rect.centery - shield_radius)
        screen.blit(shield_surface, shield_pos)


# Функция выбора игрока
def choose_player():
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 60)
    text = font.render("Выбери игрока", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, 100))
    screen.blit(text, text_rect)

    # Описание игры
    font_desc = pygame.font.Font(None, 30)
    desc_text = font_desc.render("Перепрыгивай через препятствия и собирай монеты", True, WHITE)
    desc_rect = desc_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
    screen.blit(desc_text, desc_rect)

    desc_text_2 = font_desc.render("Не пропускай бонусы - жизнь и защитный щит на 5 секунд", True, WHITE)
    desc_rect_2 = desc_text_2.get_rect(center=(WIDTH // 2, HEIGHT - 20))
    screen.blit(desc_text_2, desc_rect_2)

    screen.blit(player1_img, (150, 200))
    screen.blit(player2_img, (350, 200))
    screen.blit(player3_img, (550, 200))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if 150 <= x <= 350 and 200 <= y <= 400:
                    return "hero1"

                elif 350 <= x <= 550 and 200 <= y <= 400:
                    return "hero2"

                elif 550 <= x <= 750 and 200 <= y <= 400:
                    return "hero3"


# Загрузка и сохранение максимального счета
def load_max_score(hero_type):
    try:
        with open("data/results.txt", "r") as file:
            for line in file:
                if line.startswith(hero_type):
                    return int(line.split(":")[1].strip())
    except FileNotFoundError:
        pass
    return 0


def save_max_score(hero_type, score):
    scores = {}
    try:
        with open("data/results.txt", "r") as file:
            for line in file:
                if ":" in line:
                    key, value = line.strip().split(":")
                    scores[key] = int(value)
    except FileNotFoundError:
        pass

    scores[hero_type] = max(scores.get(hero_type, 0), score)

    with open("data/results.txt", "w") as file:
        for key, value in scores.items():
            file.write(f"{key}:{value}\n")


# Основная игра
def main_game(hero_type, start_level=1):
    # Загрузка анимаций для выбранного героя
    animations = {
        "run": AnimatedSprite(pygame.image.load(f"data/{hero_type}_run.png").convert_alpha(),
                              6, 1, 100, HEIGHT - 100),
        "stand": AnimatedSprite(pygame.image.load(f"data/{hero_type}_stand.png").convert_alpha(),
                                1, 1, 100, HEIGHT - 100),
        "jump": AnimatedSprite(pygame.image.load(f"data/{hero_type}_jump.png").convert_alpha(),
                               8, 1, 100, HEIGHT - 100),
        "hit": AnimatedSprite(pygame.image.load(f"data/{hero_type}_hit.png").convert_alpha(),
                              4, 1, 100, HEIGHT - 100),
    }

    player = Player(animations, 100, HEIGHT - 100)
    all_sprites = pygame.sprite.Group(player)
    obstacles_group = pygame.sprite.Group()
    coins_group = pygame.sprite.Group()
    bonuses_group = pygame.sprite.Group()
    particles_group = pygame.sprite.Group()
    rain_group = pygame.sprite.Group()

    # Список бонусов: (жизнь, защитный щит на 5 секунд)
    bonus_types = [
        (bonus_life_img, "life"),
        (bonus_shield_img, "shield")
    ]

    score = 0
    level = start_level
    obstacle_spawn_delay = 0
    running = True
    max_score = load_max_score(hero_type)
    start_time = time.time()
    pygame.mixer.music.play(-1)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                    player.jump()
                if event.key == pygame.K_p:
                    paused = True
                    while paused:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_p:
                                    paused = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    player.stand()
            if event.type == pygame.USEREVENT:  # Обработка таймера
                if player.current_animation == "hit":
                    player.current_animation = "run"  # Возвращаемся к обычной анимации
                    player.is_colliding = False

        # Генерация препятствий и монет
        if obstacle_spawn_delay <= 0:
            obstacle = Obstacle(random.choice(list(obstacles.values())), 5 + level)
            if not any(obstacle.rect.colliderect(o.rect) for o in obstacles_group):
                obstacles_group.add(obstacle)
                all_sprites.add(obstacle)
                obstacle_spawn_delay = random.randint(50, 100)
        else:
            obstacle_spawn_delay -= 1

        if random.randint(1, 50) == 1 and len(coins_group) < 3:
            coin = Coin()
            if not any(coin.rect.colliderect(c.rect) for c in coins_group):
                coins_group.add(coin)
                all_sprites.add(coin)

        all_sprites.update()
        particles_group.update()
        rain_group.update()

        # Проверка столкновений с препятствиями
        collisions = pygame.sprite.spritecollide(player, obstacles_group, False)
        if collisions:
            player.lose_life()
            if player.is_dead:
                collision_sound.play()
                running = False
        else:
            player.is_colliding = False

        # Проверка столкновений с монетами
        if pygame.sprite.spritecollide(player, coins_group, True):
            score += 1
            coin_sound.play()
            if score % 10 == 0:
                level += 1
                level_up_sound.play()
                create_particles((WIDTH // 2, HEIGHT // 2), particles_group)
                if level % 2 == 0:  # На четных уровнях добавляем дождь
                    for _ in range(100):
                        rain = Rain()
                        rain_group.add(rain)

        # Генерация бонусов
        if random.randint(1, 500) == 1 and len(bonuses_group) < 1:
            bonus_image, bonus_effect = random.choice(bonus_types)
            bonus = Bonus(bonus_image, bonus_effect)
            bonuses_group.add(bonus)
            all_sprites.add(bonus)

        # Проверка столкновений с бонусами
        bonuses = pygame.sprite.spritecollide(player, bonuses_group, True)
        if bonuses:
            bonus = bonuses[0]
            if bonus.effect == "life":
                player.add_life()
            elif bonus.effect == "shield":
                player.activate_shield()

        # Отрисовка
        screen.blit(fon_game[(level - 1) % 4], (0, 0))
        all_sprites.draw(screen)
        particles_group.draw(screen)
        if level % 2 == 0:  # На четных уровнях отображаем дождь
            rain_group.draw(screen)

        draw_shield_effect(screen, player)

        # Отображение счета, уровня и жизней
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Монет: {score}", True, BLACK)
        level_text = font.render(f"Уровень: {level}", True, BLACK)
        lives_text = font.render(f"Жизни: {player.lives}", True, BLACK)
        max_score_text = font.render(f"Максимальный счет: {max_score}", True, BLACK)

        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 50))
        screen.blit(lives_text, (10, 90))
        screen.blit(max_score_text, (10, 130))

        pygame.display.flip()
        clock.tick(FPS)

    # Остановка музыки
    pygame.mixer.music.stop()

    # Сохранение максимального счета
    if score > max_score:
        save_max_score(hero_type, score)

    # Окно завершения
    game_over(score, max_score, level, hero_type)


# Окно завершения игры
def game_over(score, max_score, level, hero_type):
    screen.blit(fon, (0, 0))  # Добавляем фон
    font = pygame.font.Font(None, 50)

    text = font.render(f"Игра окончена, собрано монет: {score}", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

    font2 = pygame.font.Font(None, 40)
    if score > max_score:
        record_text = font2.render(f"Победа, новый рекорд. Новый максимум: {score}", True, BLACK)
    else:
        record_text = font2.render(f"Максимум остался без изменений: {max_score}", True, BLACK)
    record_rect = record_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))

    font3 = pygame.font.Font(None, 40)
    text2 = font3.render("Нажми ПРОБЕЛ, чтобы начать заново", True, BLACK)
    text_rect2 = text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

    text3 = font3.render("Нажми R, чтобы вернуться к выбору игроков", True, BLACK)
    text_rect3 = text3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))

    screen.blit(text, text_rect)
    screen.blit(record_text, record_rect)
    screen.blit(text2, text_rect2)
    screen.blit(text3, text_rect3)

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                    main_game(hero_type)
                if event.key == pygame.K_r:
                    waiting = False
                    return


# Запуск игры
if __name__ == "__main__":
    while True:
        hero_type = choose_player()
        main_game(hero_type)
