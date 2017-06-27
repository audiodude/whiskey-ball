import sys

import pygame

pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

width, height = 1024, 600
half = width, height//2
clr_grey = pygame.Color('#DDDDDD')
clr_neon_blue = pygame.Color('#BBFFFF')
clr_neon_pink = pygame.Color('#FF69B4')
clr_neon_green = pygame.Color('#59FF3A')
fnt_default_400 = pygame.font.Font(None, 400)

area = pygame.Surface((width, height))

class GameOverDisplay(object):
  top = pygame.Surface(half)
  bottom = pygame.Surface(half)
  txt_game = fnt_default_400.render('GAME', 1, clr_neon_pink)
  txt_over = fnt_default_400.render('OVER', 1, clr_neon_pink)

  def __init__(self):
    top_color = clr_neon_blue
    bottom_color = clr_neon_green
    self.top.fill(top_color)
    self.bottom.fill(bottom_color)

  def draw(self):
    self.top.blit(self.txt_game, (80, 30))
    self.bottom.blit(self.txt_over, (110, 30))
    screen.blit(self.top, (0, 0))
    screen.blit(self.bottom, (0, height//2))

game_over = GameOverDisplay()
while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      sys.exit()
    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        sys.exit()

  screen.fill(clr_grey)
  game_over.draw()
  pygame.display.flip()
