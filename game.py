import json
import sys

import pygame

pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

width, height = 1024, 600
half = width, height//2
clr_grey = pygame.Color('#DDDDDD')
clr_black = pygame.Color('#000000')
clr_white = pygame.Color('#FFFFFF')
clr_neon_blue = pygame.Color('#BBFFFF')
clr_neon_pink = pygame.Color('#FF69B4')
clr_neon_green = pygame.Color('#9AFF87')
fnt_default_200 = pygame.font.Font(None, 200)
fnt_default_300 = pygame.font.Font(None, 300)
fnt_default_400 = pygame.font.Font(None, 400)

scoremap = json.load(open('scoremap.json'))
scorekey_to_string = {
  pygame.K_1: '1',
  pygame.K_2: '2',
  pygame.K_3: '3',
  pygame.K_4: '4',
  pygame.K_5: '5',
  pygame.K_6: '6',
}

class GameOverDisplay(object):
  def __init__(self, game):
    self.game = game
    self.top = pygame.Surface(half)
    self.bottom = pygame.Surface(half)
    self.txt_game = fnt_default_400.render('GAME', 1, clr_neon_pink)
    self.txt_over = fnt_default_400.render('OVER', 1, clr_neon_pink)
    self.elapsed = 0
    self.cycles = 0

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

  def update(self, tick):
    self.elapsed += tick
    if self.elapsed > 150:
      self.elapsed = 0
      self.cycles += 1
      self.top_idx += 1
      self.bottom_idx += 1
      if self.top_idx > len(self.colors) - 1:
        self.top_idx = 0
      if self.bottom_idx > len(self.colors) - 1:
        self.bottom_idx = 0

  def handle_key(self, keycode):
    if keycode == pygame.K_SPACE:
      self.game.goto_main()

class MainDisplay(object):
  def __init__(self, game):
    self.game = game
    self.top = pygame.Surface(half)
    self.bottom = pygame.Surface(half)
    self.txt_score_header = fnt_default_200.render('score:', 1, clr_neon_pink)
    self.txt_time_header = fnt_default_200.render('time:', 1, clr_white)
    self.animate_score = 0

  def reset(self, total_time=40):
    self.rem_secs = total_time
    self.elapsed = 0

  def draw(self):
    txt_score = fnt_default_300.render(str(game.score), 1, clr_neon_pink)
    txt_time = fnt_default_300.render(str(self.rem_secs), 1, clr_white)
    self.top.fill(clr_neon_blue)
    self.bottom.fill(clr_black)
    if self.animate_score:
      txt_scored = fnt_default_300.render(
        str(self.animate_score), 1, clr_neon_blue)
      self.bottom.blit(txt_scored, (40, 20))

    self.top.blit(self.txt_score_header, (10, 0))
    self.top.blit(self.txt_time_header, (640, 0))
    self.top.blit(txt_score, (40, 120))
    self.top.blit(txt_time, (680, 120))
    screen.blit(self.top, (0, 0))
    screen.blit(self.bottom, (0, height//2))

  def update(self, tick):
    self.elapsed += tick
    if self.elapsed > 1000:
      self.elapsed = 0
      self.rem_secs -= 1
      if self.rem_secs < 0:
        self.game.goto_game_over()

  def handle_key(self, keycode):
    string = scorekey_to_string.get(keycode, '0')
    plus_score = scoremap.get(string, 0)
    if plus_score:
      self.game.score += plus_score
      self.animate_score = plus_score

class Game(object):
  def __init__(self):
    self.clock = pygame.time.Clock()
    self.game_over = GameOverDisplay(self)
    self.main_display = MainDisplay(self)
    self.current_state = self.game_over
    self.score = 0

  def handle_key(self, keycode):
    self.current_state.handle_key(keycode)

  def draw(self):
    self.current_state.draw()

  def update(self):
    tick = self.clock.tick()
    result = self.current_state.update(tick)

  def goto_main(self):
    self.score = 0
    self.main_display.reset()
    self.current_state = self.main_display    

  def goto_game_over(self):
    self.current_state = self.game_over

game = Game()

while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      sys.exit()
    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        sys.exit()
      else:
        game.handle_key(event.key)

  screen.fill(clr_grey)
  game.update()
  game.draw()
  pygame.display.flip()
