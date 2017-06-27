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
clr_neon_green = pygame.Color('#9AFF87')
fnt_default_400 = pygame.font.Font(None, 400)

area = pygame.Surface((width, height))

class GameOverDisplay(object):
  def __init__(self):
    self.top = pygame.Surface(half)
    self.bottom = pygame.Surface(half)
    self.txt_game = fnt_default_400.render('GAME', 1, clr_neon_pink)
    self.txt_over = fnt_default_400.render('OVER', 1, clr_neon_pink)
    self.elapsed = 0
    self.clock = pygame.time.Clock()

    self.colors = [clr_neon_blue, clr_neon_green, clr_neon_pink]
    self.top_idx = 0
    self.bottom_idx = 1

  def draw(self):
    self.top.fill(self.colors[self.top_idx])
    self.bottom.fill(self.colors[self.bottom_idx])
    self.top.blit(self.txt_game, (80, 30))
    self.bottom.blit(self.txt_over, (110, 30))
    screen.blit(self.top, (0, 0))
    screen.blit(self.bottom, (0, height//2))

  def update(self):
    self.elapsed += self.clock.tick()
    if self.elapsed > 150:
      self.elapsed = 0
      self.top_idx += 1
      self.bottom_idx += 1
      if self.top_idx > len(self.colors) - 1:
        self.top_idx = 0
      if self.bottom_idx > len(self.colors) - 1:
        self.bottom_idx = 0

game_over = GameOverDisplay()
while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      sys.exit()
    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        sys.exit()

  screen.fill(clr_grey)
  game_over.update()
  game_over.draw()
  pygame.display.flip()
