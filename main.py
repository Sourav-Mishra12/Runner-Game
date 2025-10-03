import pygame 
import sys
from random import randint 
import os 

# saving the highscore in APPDATA/PIXELERA/HIGHSCORE.TXT

appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'),'PixelEra')
os.makedirs(appdata_dir,exist_ok = True)
HIGH_SCORE_FILE = os.path.join(appdata_dir , 'highscore.txt')



# -------------------- FUNCTIONS --------------------

def resource_path(relative_path):
    try :
        base_path = sys._MEIPASS
    except Exception :
        base_path = os.path.abspath(".")

    return os.path.join(base_path,relative_path)



def load_highscore():   # function to load the highscore used at line 306
    if os.path.exists(HIGH_SCORE_FILE):
        with open(HIGH_SCORE_FILE,"r") as f :
            try :
                return int(f.read())
            except ValueError:
                return 0
            
    else :
        return 0
    

def save_highscore(score):    # function to save the highscore
    with open(HIGH_SCORE_FILE,"w") as f:
        f.write(str(score))



def display_score():   # function to display score
    if show_collision_text:
        current_time = final_score
    else:
     current_time = int(pygame.time.get_ticks() / 500) - start_time

    score_surface = test_font.render(f'SCORE : {current_time}', False, 'Black')
    score_rect = score_surface.get_rect(center=(400, 50))
    screen.blit(score_surface, score_rect)
    return current_time

def obstacle_movement(obstacle_list):     # making the obstacle move
    if obstacle_list:
        for obstacle_rect in obstacle_list:
            obstacle_rect.x -= object_speed

            if obstacle_rect.bottom == 300:
                screen.blit(snail_surface, obstacle_rect)
            else:
                screen.blit(fly_surface, obstacle_rect)

        obstacle_list = [obstacle for obstacle in obstacle_list if obstacle.x > -100]
        return obstacle_list
    else:
        return []

def collisions(player, obstacles):   # for the collisions
    for obstacle_rect in obstacles:
        if player.colliderect(obstacle_rect):
            return True
    return False

def player_animation():   # animating the player walk and jump
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
icon = pygame.image.load(resource_path('graphics/my_icon.png'))
pygame.display.set_icon(icon) 
clock = pygame.time.Clock()

test_font = pygame.font.Font(resource_path('fonts/Pixeltype.ttf'), 30)  # initialising fonts in the game
small_text = pygame.font.Font(resource_path('fonts/Pixeltype.ttf'), 25)  # initialising another font in the game

game_active = False  # if the game is active or not
start_time = 0  # the initialising the start time
score = 0   # initialising the score
object_speed = 5  # variable used in object movement function
spawn_object = 1500  # variable for spawning objects
current_spawn_delay = spawn_object # further usage in the main game loop
final_score = 0  # in order to freeze score count when collision message shows up , ussing in displayscore function
highscore = load_highscore() # used to load high score


# everytime the speed increases there will be a message shown for that purpose we created these variables , more in the game loop

last_level_speed = 0   
show_speed_message = False
new_level_speed = 0


# variables for collision fallback

collision_time = 0
show_collision_text = False

# audio 

collison_sound = pygame.mixer.Sound(resource_path('audio/collision.mp3')) 
collison_sound.set_volume(1.0)  # collision sound
jump_sound = pygame.mixer.Sound(resource_path('audio/jump.mp3')) # jump sounds
pygame.mixer.music.load(resource_path('audio/music.wav')) 
pygame.mixer.music.set_volume(0.3)# bg music
pygame.mixer.music.play(-1)  # loop forever


# Background
sky_surface = pygame.image.load(resource_path('graphics/Sky.png')).convert()
ground_surface = pygame.image.load(resource_path('graphics/ground.png')).convert()

# Title
name_surface = small_text.render('PIXEL ERA', False, 'Black')
name_rect = name_surface.get_rect(topleft=(30, 10))

# Player
player__walk_1 = pygame.image.load(resource_path('graphics/player_walk_1.png')).convert_alpha()
player__walk_2 = pygame.image.load(resource_path('graphics/player_walk_2.png')).convert_alpha()
player_walk = [player__walk_1 , player__walk_2]
player_index = 0    # index is used to create animations e.g. at index 0 walk_1 and at index 1 walk_2 this will go to and fro and create effects
player_jump = pygame.image.load(resource_path('graphics/jump.png')).convert_alpha()

player_surface = player_walk[player_index]  # just to play with indexes and create animations
player_rect = player_surface.get_rect(midbottom = (80,300))   

player_gravity = 0
player_stand = pygame.image.load(resource_path('graphics/player_stand.png')).convert_alpha()

# SNAIL
snail_surface_1 = pygame.image.load(resource_path('graphics/snail1.png')).convert_alpha()
resized_snail_1 = pygame.transform.scale(snail_surface_1, (70, 35))

snail_surface_2 = pygame.image.load(resource_path('graphics/snail2.png')).convert_alpha()
resized_snail_2 = pygame.transform.scale(snail_surface_2, (70,35))

snail_frames = [resized_snail_1 , resized_snail_2]   # same as the walk_1 and walk_2
snail_frame_index = 0
snail_surface = snail_frames[snail_frame_index]

# FLY
fly_surface_1 = pygame.image.load(resource_path('graphics/Fly1.png')).convert_alpha()
resized_fly_1 = pygame.transform.scale(fly_surface_1, (50, 25))
fly_surface_2 = pygame.image.load(resource_path('graphics/Fly2.png')).convert_alpha()
resized_fly_2 = pygame.transform.scale(fly_surface_2, (50, 25))
fly_frames = [resized_fly_1 , resized_fly_2]
fly_frame_index = 0
fly_surface = fly_frames[fly_frame_index]

obstacle_rect_list = []

# pause state

game_paused = False 
pause_surface = pygame.image.load(resource_path('graphics/pause-button.png')).convert_alpha()
paused_surface_scaled = pygame.transform.scale(pause_surface , (50,50))
pause_surface_rect = paused_surface_scaled.get_rect(topright = (780,30))


# Timer
obstacle_timer = pygame.USEREVENT + 1
pygame.time.set_timer(obstacle_timer, spawn_object)

snail_animation_timer = pygame.USEREVENT+2
pygame.time.set_timer(snail_animation_timer,700)

fly_animation_timer = pygame.USEREVENT+3
pygame.time.set_timer(fly_animation_timer,300)

# -------------------- GAME LOOP --------------------

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN :
            if pause_surface_rect.collidepoint(event.pos):
                game_paused = not game_paused
                if game_paused :
                    pygame.mixer.music.pause()
                    pygame.time.set_timer(obstacle_timer , 0)
                    pygame.time.set_timer(snail_animation_timer ,0)
                    pygame.time.set_timer(fly_animation_timer,0)

                else:
                    pygame.mixer.music.unpause()
                    pygame.time.set_timer(obstacle_timer, spawn_object)
                    pygame.time.set_timer(snail_animation_timer,700)
                    pygame.time.set_timer(fly_animation_timer,300)



        if game_active:      # jump logic if game is active
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player_rect.bottom >= 300:
                    player_gravity = -21.5
                    jump_sound.play()
        else:      # if the game is not active then clear each and every object to avoid overlap
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                start_time = int(pygame.time.get_ticks() / 500)
                obstacle_rect_list.clear()
                player_rect.midbottom = (80, 300)
                player_gravity = 0

        # ✅ Obstacle spawning MUST be outside of the else:
        if game_active:
         if event.type == obstacle_timer :    # in what pace the objects will spawn 
            if randint(0, 2) == 0 :
                obstacle_rect_list.append(resized_snail_1.get_rect(midbottom=(randint(900, 1100), 300)))
            else:
                obstacle_rect_list.append(resized_fly_1.get_rect(midbottom=(randint(900, 1100), 240)))

         if event.type == snail_animation_timer :  # movement animation of the snail
                 snail_frame_index = 1 - snail_frame_index
                 snail_surface = snail_frames[snail_frame_index]

         if event.type == fly_animation_timer:   # movement animation of the fly
                 fly_frame_index = 1 - fly_frame_index
                 fly_surface = fly_frames[fly_frame_index]



    # -------------------- GAME ACTIVE --------------------
    if game_active and not game_paused :   # if the game is not paused and is active 
        screen.blit(sky_surface, (0, 0))
        screen.blit(ground_surface, (0, 300))
        screen.blit(paused_surface_scaled , pause_surface_rect)
        score = display_score()

        if show_speed_message:
            if pygame.time.get_ticks() - show_message_time < 1500 :
                speed_text = test_font.render('SPEED INCREASED !! ' , True , 'Red')
                speed_text_rect = speed_text.get_rect(center = (400,200))
                screen.blit(speed_text , speed_text_rect)
        else :
            show_speed_message = False


        # scaling the speed of obstacles spawning
        # speed of spawning obstacles

        if score >= 100 :
            new_level_speed = 4
            object_speed = 10
            spawn_object = 800
        elif score > 70 :
            new_level_speed = 3
            object_speed = 8
            spawn_object = 1000
        elif  score > 40 :
            new_level_speed = 2
            object_speed = 6
            spawn_object = 1200
        else :
            new_level_speed = 0
            object_speed = 5
            spawn_object = 1500

        if new_level_speed > last_level_speed :
         show_speed_message = True
         show_message_time = pygame.time.get_ticks()
         last_level_speed = new_level_speed

        
        # runs only if the spawn time changed 

        if spawn_object != current_spawn_delay :
            pygame.time.set_timer(obstacle_timer,spawn_object)
            current_spawn_delay = spawn_object


        # Player movement
        player_gravity += 1
        player_rect.y += player_gravity
        if player_rect.bottom >= 300:
            player_rect.bottom = 300


        if show_collision_text :   # after collision how and what text will be shown
            default_font = pygame.font.SysFont(None,50)
            collided_surface = default_font.render('!! COLLIDED !!',True,'Red')
            collided_rect = collided_surface.get_rect(center = (400,200))
            screen.blit(collided_surface,collided_rect)

            if pygame.time.get_ticks() - collision_time >= 1000: 
                if final_score > highscore :
                    highscore = final_score
                    save_highscore(highscore)
                game_active = False
                show_collision_text = False


        else:   # if there is no collision then this block will be executed 
           player_animation()
           screen.blit(player_surface, player_rect)
           screen.blit(name_surface, name_rect)
        
        # Obstacles
           obstacle_rect_list = obstacle_movement(obstacle_rect_list)

            # Collision detection

           if collisions(player_rect , obstacle_rect_list):  # if collision happens then this will happen
               collison_sound.play()  # collision sound 
               show_collision_text = True
               collision_time = pygame.time.get_ticks()
               final_score = score

    elif game_paused :   # if the game is paused then this will happen
        
        pause = pygame.font.Font(resource_path('fonts/Pixeltype.ttf'), 60)
        paused_text = pause.render('PAUSED !! ',False,'Red')
        paused_rect = paused_text.get_rect(center = (400,100))
        screen.blit(paused_text , paused_rect)
    

    # -------------------- GAME INACTIVE (Start / Restart) --------------------
    else:
        screen.fill((94, 129, 162))
        resized_player = pygame.transform.scale(player_stand, (150, 200))
        score_surface = small_text.render(f'SCORE: {score} --- HIGH SCORE : {highscore}', False, 'Black')
        big_font = pygame.font.Font(resource_path('fonts/Pixeltype.ttf'), 50)
        game_name = big_font.render('PIXEL ERA', True, 'Black')
        restart_text = test_font.render('PRESS SPACE TO START', True, 'Black')

        instruction_font = pygame.font.Font(resource_path('fonts/Pixeltype.ttf'), 25)
        instruction_text = instruction_font.render('PRESS SPACE TO JUMP - AVOID ENEMIES TO SURVIVE!', True, 'Black')
        instruction_rect = instruction_text.get_rect(center=(400, 330))


        screen.blit(game_name, (300, 30))
        screen.blit(restart_text, (270, 350))
        screen.blit(resized_player, (300, 100))
        screen.blit(score_surface, (10, 50))
        screen.blit(instruction_text,instruction_rect)

    pygame.display.update()
    clock.tick(60)
