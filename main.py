import pygame 
from sys import exit


pygame.init()
screen = pygame.display.set_mode((800,400))
pygame.display.set_caption("Runner")
clock = pygame.time.Clock()

test_font = pygame.font.Font('fonts/Pixeltype.ttf' , 30)  # Font(font type , font size)

# the images that will be displayed on the screen
sky_surface = pygame.image.load('graphics/Sky.png').convert()
ground_surface = pygame.image.load('graphics/ground.png').convert()
text_surface = test_font.render('My game' , False , 'Black').convert() # render(text , AA , color)
snail_surface = pygame.image.load('graphics/snail1.png').convert_alpha()
snail_rect = snail_surface.get_rect(midbottom = (600,300))

player_surface = pygame.image.load('graphics/player_walk_1.png').convert_alpha()
player_rect = player_surface.get_rect(midbottom = (80,300)) #Rect(left,top,width,height)

# the game loop which will always run untill we quit the game
while True :
      
      for event in pygame.event.get():  # iterates over each and every event
            if event.type == pygame.QUIT:
                  pygame.quit() # the quit function will quit the game
                  exit() #this will exit the loop 

    # draw all our elements and update everything
      screen.blit(sky_surface,(0,0))
      screen.blit(ground_surface,(0,300))
      screen.blit(text_surface  , (50 , 30))
      snail_rect.x -= 4
      if snail_rect.right <= 0: snail_rect.left = 800
      screen.blit(snail_surface , snail_rect)
      screen.blit(player_surface , player_rect)

      
            

      pygame.display.update()
      clock.tick(60)



