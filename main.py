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
                screen.blit(resized_snail_1, obstacle_rect)
            else:
                screen.blit(resized_fly_1, obstacle_rect)

        obstacle_list = [obstacle for obstacle in obstacle_list if obstacle.x > -100]
        return obstacle_list
    else:
        return []

def collisions(player, obstacles):
    for obstacle_rect in obstacles:
        if player.colliderect(obstacle_rect):
            return False
    return True

def player_animation():
    global player_surface , player_index

    
    if player_rect.bottom < 300 :
        player_surface = player_jump
    else: 
        player_index += 0.1
        if player_index >= len(player_walk): player_index = 0
        player_surface = player_walk[int(player_index)]


    # player walking animation if the player is on the floor
    # display the jump surface when player is not on floor


# -------------------- INIT --------------------

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("PIXEL ERA")
clock = pygame.time.Clock()

test_font = pygame.font.Font('fonts/Pixeltype.ttf', 30)
small_text = pygame.font.Font('fonts/Pixeltype.ttf', 25)

game_active = False
start_time = 0
score = 0

# audio 

jump_sound = pygame.mixer.Sound('audio/jump.mp3') # jump sounds
pygame.mixer.music.load('audio/music.wav')  # bg music
pygame.mixer.music.play(-1)  # loop forever


# Background
sky_surface = pygame.image.load('graphics/Sky.png').convert()
ground_surface = pygame.image.load('graphics/ground.png').convert()

# Title
name_surface = small_text.render('PIXEL ERA', False, 'Black')
name_rect = name_surface.get_rect(topleft=(30, 10))

# Player
player__walk_1 = pygame.image.load('graphics/player_walk_1.png').convert_alpha()
player__walk_2 = pygame.image.load('graphics/player_walk_2.png').convert_alpha()
player_walk = [player__walk_1 , player__walk_2]
player_index = 0
player_jump = pygame.image.load('graphics/jump.png').convert_alpha()

player_surface = player_walk[player_index]
player_rect = player_surface.get_rect(midbottom = (80,300))

player_gravity = 0
player_stand = pygame.image.load('graphics/player_stand.png').convert_alpha()

# SNAIL
snail_surface_1 = pygame.image.load('graphics/snail1.png').convert_alpha()
resized_snail_1 = pygame.transform.scale(snail_surface_1, (70, 35))
snail_surface_2 = pygame.image.load('graphics/snail2.png').convert_alpha()
resized_snail_2 = pygame.transform.scale(snail_surface_2, (70,35))
snail_frames = [resized_snail_1 , resized_snail_2]
snail_frame_index = 0
snail_surface = snail_frames[snail_frame_index]

# FLY
fly_surface_1 = pygame.image.load('graphics/Fly1.png').convert_alpha()
resized_fly_1 = pygame.transform.scale(fly_surface_1, (50, 25))
fly_surface_2 = pygame.image.load('graphics/Fly2.png').convert_alpha()
resized_fly_2 = pygame.transform.scale(fly_surface_2, (50, 25))
fly_frames = [resized_fly_1 , resized_fly_2]
fly_frame_index = 0
fly_surface = fly_frames[fly_frame_index]

obstacle_rect_list = []

# Timer
obstacle_timer = pygame.USEREVENT + 1
pygame.time.set_timer(obstacle_timer, 1500)

snail_animation_timer = pygame.USEREVENT+2
pygame.time.set_timer(snail_animation_timer,700)

fly_animation_timer = pygame.USEREVENT+3
pygame.time.set_timer(fly_animation_timer,1000)

# -------------------- GAME LOOP --------------------

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if game_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player_rect.bottom >= 300:
                    player_gravity = -21.5
                    jump_sound.play()
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                start_time = int(pygame.time.get_ticks() / 500)
                obstacle_rect_list.clear()
                player_rect.midbottom = (80, 300)
                player_gravity = 0

        # ✅ Obstacle spawning MUST be outside of the else:
        if game_active:
         if event.type == obstacle_timer :
            if randint(0, 2) == 0 :
                obstacle_rect_list.append(resized_snail_1.get_rect(midbottom=(randint(900, 1100), 300)))
            else:
                obstacle_rect_list.append(resized_fly_1.get_rect(midbottom=(randint(900, 1100), 240)))

            if event.type == snail_animation_timer :
                if snail_frame_index == 0 : snail_frame_index = 1
                else : snail_frame_index = 0
                snail_surface = snail_frames[snail_frame_index]

            if event.type == fly_animation_timer:
                if fly_frame_index == 0 : fly_frame_index = 1
                else: fly_frame_index = 0 
                fly_surface = fly_frames[fly_frame_index]


        

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
        player_animation()
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
