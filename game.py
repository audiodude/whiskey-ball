## Whiskey Ball
#
# Controls:
# 
# SPC  Start game, select drink
# 1-6  Score points during gameplay
# ,    Move left in menus
# .    Move right in menus
# ESC  Quit at any time

import json
import sys

import pygame

pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

GAME_DURATION_SECS = 40
USE_MUSIC = False

width, height = 1024, 600
half = width, height//2
quarter = width, height//4
three_quarters = width, height//4 * 3
clr_grey = pygame.Color('#DDDDDD')
clr_black = pygame.Color('#000000')
clr_white = pygame.Color('#FFFFFF')
clr_neon_blue = pygame.Color('#BBFFFF')
clr_neon_pink = pygame.Color('#FF69B4')
clr_neon_green = pygame.Color('#9AFF87')
fnt_default_100 = pygame.font.Font(None, 100)
fnt_default_160 = pygame.font.Font(None, 160)
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
rewardmap = json.load(open('rewardmap.json'))
drinks = rewardmap['drinks']
tiers = rewardmap['tiers']
assert len(drinks) == len(tiers), ('Tiers and drinks do not match, check '
                                   'rewardmap.json')
tier_to_coords = {
  2: (130, 220),
  3: (240, 220),
  4: (210, 220),
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

class ScoreAnimation(object):
  def __init__(self, surface, score, fill_color=clr_black):
    self.surface = surface
    self.fill_color = fill_color
    self.elapsed = 0
    self.cycles = 0
    self.score = score
    self.showing = True

  def draw(self):
    if self.showing:
      score_str = str(self.score)
      x = 340
      if len(score_str) == 3:
        x = 260
      txt_scored = fnt_default_400.render(score_str, 1, clr_neon_green)
      self.surface.blit(txt_scored, (x, 20))
    else:
      self.surface.fill(self.fill_color)

  def update(self, tick):
    if self.cycles >= 10:
      self.showing = False
      return

    self.elapsed += tick
    if (self.cycles > 1 and self.elapsed > 100) or self.elapsed > 500:
      self.elapsed = 0
      self.cycles += 1
      self.showing = not self.showing

class MainDisplay(object):
  def __init__(self, game):
    self.game = game
    self.top = pygame.Surface(half)
    self.bottom = pygame.Surface(half)
    self.txt_score_header = fnt_default_200.render('score:', 1, clr_neon_pink)
    self.txt_time_header = fnt_default_200.render('time:', 1, clr_black)
    self.animate_score = None

  def reset(self):
    self.rem_secs = GAME_DURATION_SECS
    self.elapsed = 0
    if USE_MUSIC:
      pygame.mixer.music.load('game_loop.wav')
      pygame.mixer.music.play(-1)

  def draw(self):
    txt_score = fnt_default_300.render(str(game.score), 1, clr_neon_pink)
    txt_time = fnt_default_300.render(str(self.rem_secs), 1, clr_black)
    self.top.fill(clr_neon_blue)
    if self.animate_score:
      self.animate_score.draw()
    else:
      self.bottom.fill(clr_black)

    self.top.blit(self.txt_score_header, (10, 0))
    self.top.blit(self.txt_time_header, (640, 0))
    self.top.blit(txt_score, (40, 120))
    self.top.blit(txt_time, (680, 120))
    screen.blit(self.top, (0, 0))
    screen.blit(self.bottom, (0, height//2))

  def update(self, tick):
    if self.animate_score:
      self.animate_score.update(tick)

    self.elapsed += tick
    if self.elapsed > 1000:
      self.elapsed = 0
      self.rem_secs -= 1
      if self.rem_secs == GAME_DURATION_SECS//3:
        if USE_MUSIC:
          pygame.mixer.music.load('game_loop_hurry.wav')
          pygame.mixer.music.play(-1)
      if self.rem_secs < 0:
        if USE_MUSIC:
          pygame.mixer.music.stop()
        self.game.goto_drink()

  def handle_key(self, keycode):
    string = scorekey_to_string.get(keycode, '0')
    plus_score = scoremap.get(string, 0)
    if plus_score:
      self.game.score += plus_score
      if self.animate_score:
        self.animate_score.showing = False
        self.animate_score.draw()
      self.animate_score = ScoreAnimation(self.bottom, plus_score)

class Arrow(object):
  def __init__(self, text, state):
    self.text = text
    self.state = state
    self.animating = False
    self.active = False
    self.elapsed = 0
    self.cycles = 0

  def draw(self, surface, coords):
    color = clr_neon_pink if self.active else clr_black
    txt = fnt_default_300.render(self.text, 1, color)
    surface.blit(txt, coords)

  def update(self, tick):
    if not self.animating:
      return
    self.elapsed += tick
    if self.elapsed > 60:
      self.elapsed = 0
      self.active = not self.active
      self.cycles += 1
      if self.cycles > 5:
        self.cycles = 0
        self.active = False
        self.animating = False
        self.state.update_tier()

class DrinkDisplay(object):
  def __init__(self, game):
    self.game = game
    self.elapsed = 0
    self.top = pygame.Surface(quarter)
    self.bottom = pygame.Surface(three_quarters)
    self.drink_showing = True
    self.left_arrow = Arrow('<', self)
    self.right_arrow = Arrow('>', self)
    self.focus = 'left'

  def init_tier(self):
    self.tiers = []
    first_locked = False
    for i, (score_tier, drink) in enumerate(zip(tiers, drinks)):
      current_tier = {'tier': i+1, 'score': score_tier, 'drink': drink}
      locked = True
      if self.game.score >= score_tier:
        locked = False
      elif not first_locked:
        first_locked = True
        self.current_tier = self.tiers[-1]
      current_tier['locked'] = locked
      self.tiers.append(current_tier)
    if not first_locked:
      self.current_tier = self.tiers[-1]
    
  def draw(self):
    self.top.fill(clr_black)
    self.bottom.fill(clr_neon_blue)
    txt_score = fnt_default_160.render(
      'Your score: %s' % self.game.score, 1, clr_white)
    self.top.blit(txt_score, (110, 20))

    self.left_arrow.draw(self.bottom, (10, 150))
    self.right_arrow.draw(self.bottom, (900, 150))

    pts_string = str(self.current_tier['score'])
    while len(pts_string) < 3:
      pts_string = ' ' + pts_string
    tier_string = 'Tier %s: %s pts' % (self.current_tier['tier'], pts_string)
    txt_tier = fnt_default_160.render(tier_string, 1, clr_black)
    self.bottom.blit(txt_tier, (110, 10))

    drink_color = clr_black if self.current_tier['locked'] else clr_neon_pink
    if self.current_tier['locked'] or self.drink_showing:
      if self.current_tier['tier'] == 1:
        txt_drink_1 = fnt_default_160.render(
          self.current_tier['drink'].split(' ')[0], 1, drink_color)
        txt_drink_2 = fnt_default_160.render(
          self.current_tier['drink'].split(' ')[1], 1, drink_color)
        self.bottom.blit(txt_drink_1, (160, 140))
        self.bottom.blit(txt_drink_2, (350, 280))
      else:
        coords = tier_to_coords[self.current_tier['tier']]
        txt_drink = fnt_default_160.render(
          self.current_tier['drink'], 1, drink_color)
        self.bottom.blit(txt_drink, coords)

    if self.current_tier['locked'] and self.drink_showing:
      txt_locked = fnt_default_100.render('[LOCKED]', 1, clr_neon_pink)
      self.bottom.blit(txt_locked, (340, 360))

    screen.blit(self.top, (0, 0))
    screen.blit(self.bottom, (0, height//4))

  def update(self, tick):
    self.left_arrow.update(tick)
    self.right_arrow.update(tick)
    self.elapsed += tick
    if self.elapsed > 150:
      self.elapsed = 0
      self.drink_showing = not self.drink_showing

  def handle_key(self, keycode):
    if keycode == pygame.K_COMMA:
      self.down_tier()
    elif keycode == pygame.K_PERIOD:
      self.up_tier()
    elif keycode == pygame.K_SPACE:
      self.pour_drink()

  def down_tier(self):
    self.left_arrow.animating = True
    next_tier_idx = self.current_tier['tier'] - 1 - 1
    if next_tier_idx == -1:
      next_tier_idx = len(self.tiers) - 1
    self.next_tier = self.tiers[next_tier_idx]

  def up_tier(self):
    self.right_arrow.animating = True
    next_tier_idx = self.current_tier['tier'] - 1 + 1
    if next_tier_idx == len(self.tiers):
      next_tier_idx = 0
    self.next_tier = self.tiers[next_tier_idx]

  def update_tier(self):
    self.current_tier = self.next_tier

  def pour_drink(self):
    self.game.goto_game_over()

class Game(object):
  def __init__(self):
    self.clock = pygame.time.Clock()
    self.game_over = GameOverDisplay(self)
    self.main_display = MainDisplay(self)
    self.drink_display = DrinkDisplay(self)
    self.current_state = self.game_over
    self.score = 0

  def handle_key(self, keycode):
    self.current_state.handle_key(keycode)

  def draw(self):
    self.current_state.draw()

  def update(self):
    tick = self.clock.tick(30)
    result = self.current_state.update(tick)

  def goto_main(self):
    self.score = 0
    self.main_display.reset()
    self.current_state = self.main_display    

  def goto_game_over(self):
    self.current_state = self.game_over

  def goto_drink(self):
    self.current_state = self.drink_display
    self.drink_display.init_tier()

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
