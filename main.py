import pygame 
from sys import exit
from random import randint 

# -------------------- FUNCTIONS --------------------

def display_score():
    current_time = int(pygame.time.get_ticks() / 500) - start_time
    score_surface = test_font.render(f'SCORE : {current_time}', False, 'Black')
    score_rect = score_surface.get_rect(center=(400, 50))
    screen.blit(score_surface, score_rect)
    return current_time

def obstacle_movement(obstacle_list):
    if obstacle_list:
        for obstacle_rect in obstacle_list:
            obstacle_rect.x -= 5

            if obstacle_rect.bottom == 300:
                screen.blit(resized_snail, obstacle_rect)
            else:
                screen.blit(resized_fly, obstacle_rect)

        obstacle_list = [obstacle for obstacle in obstacle_list if obstacle.x > -100]
        return obstacle_list
    else:
        return []

def collisions(player, obstacles):
    for obstacle_rect in obstacles:
        if player.colliderect(obstacle_rect):
            return False
    return True

# -------------------- INIT --------------------

pygame.init()
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("PIXEL ERA")
clock = pygame.time.Clock()

test_font = pygame.font.Font('fonts/Pixeltype.ttf', 30)
small_text = pygame.font.Font('fonts/Pixeltype.ttf', 25)

game_active = False
start_time = 0
score = 0

# Background
sky_surface = pygame.image.load('graphics/Sky.png').convert()
ground_surface = pygame.image.load('graphics/ground.png').convert()

# Title
name_surface = small_text.render('PIXEL ERA', False, 'Black')
name_rect = name_surface.get_rect(topleft=(30, 10))

# Player
player_surface = pygame.image.load('graphics/player_walk_1.png').convert_alpha()
player_rect = player_surface.get_rect(midbottom=(80, 300))
player_gravity = 0
player_stand = pygame.image.load('graphics/player_stand.png').convert_alpha()

# Obstacles
snail_surface = pygame.image.load('graphics/snail1.png').convert_alpha()
resized_snail = pygame.transform.scale(snail_surface, (70, 35))
fly_surface = pygame.image.load('graphics/fly1.png').convert_alpha()
resized_fly = pygame.transform.scale(fly_surface, (50, 25))
obstacle_rect_list = []

# Timer
obstacle_timer = pygame.USEREVENT + 1
pygame.time.set_timer(obstacle_timer, 1500)

# -------------------- GAME LOOP --------------------

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if game_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player_rect.bottom >= 300:
                    player_gravity = -20
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                start_time = int(pygame.time.get_ticks() / 500)
                obstacle_rect_list.clear()
                player_rect.midbottom = (80, 300)
                player_gravity = 0

        # ✅ Obstacle spawning MUST be outside of the else:
        if event.type == obstacle_timer and game_active:
            if randint(0, 2):
                obstacle_rect_list.append(resized_snail.get_rect(midbottom=(randint(900, 1100), 300)))
            else:
                obstacle_rect_list.append(resized_fly.get_rect(midbottom=(randint(900, 1100), 230)))

    # -------------------- GAME ACTIVE --------------------
    if game_active:
        screen.blit(sky_surface, (0, 0))
        screen.blit(ground_surface, (0, 300))
        score = display_score()

        # Player movement
        player_gravity += 1
        player_rect.y += player_gravity
        if player_rect.bottom >= 300:
            player_rect.bottom = 300
        screen.blit(player_surface, player_rect)
        screen.blit(name_surface, name_rect)

        # Obstacles
        obstacle_rect_list = obstacle_movement(obstacle_rect_list)

        # Collision detection
        game_active = collisions(player_rect, obstacle_rect_list)

    # -------------------- GAME INACTIVE (Start / Restart) --------------------
    else:
        screen.fill((94, 129, 162))
        resized_player = pygame.transform.scale(player_stand, (150, 200))
        score_surface = small_text.render(f'SCORE: {score}', False, 'Black')
        big_font = pygame.font.Font('fonts/Pixeltype.ttf', 50)
        game_name = big_font.render('PIXEL ERA', True, 'Black')
        restart_text = test_font.render('PRESS SPACE TO START', True, 'Black')

        screen.blit(game_name, (300, 30))
        screen.blit(restart_text, (270, 350))
        screen.blit(resized_player, (300, 100))
        screen.blit(score_surface, (10, 50))

    pygame.display.update()
    clock.tick(60)
