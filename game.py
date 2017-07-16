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
import os
import sys

import pygame

pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

# Should be 60
GAME_DURATION_SECS = 5
# Should be True
USE_MUSIC = True
# Should be 60 * 1000
POUR_TIME_MS = 20 * 1000
# Should be 10 * 1000
LIGHT_TIME_MS = 1 * 1000

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

class BaseRobot(object):
  TIER_TO_EVENT = {
    0: pygame.USEREVENT,
    1: pygame.USEREVENT + 1,
    2: pygame.USEREVENT + 2,
  }
  EVENT_TO_TIER = dict((value, key) for key, value in TIER_TO_EVENT.items())
  LIGHT_EVENT = pygame.USEREVENT + 3

  def __init__(self):
    self.tier_to_drink = dict((i, drink) for i, drink in enumerate(drinks))
    self.pouring_tier = None

  def is_pouring_drink(self):
    return self.pouring_tier != None

  def pour_drink(self, tier):
    if self.is_pouring_drink():
      raise ValueError('Refusing to pour drink while drink is already pouring')

    self.pouring_tier = tier
    drink = self.tier_to_drink[tier]
    print('Pouring %s' % drink)
    event = self.TIER_TO_EVENT[tier]
    pygame.time.set_timer(event, POUR_TIME_MS)

  def handle_event_type(self, event_type):
    pygame.time.set_timer(event_type, 0)
    if event_type == self.LIGHT_EVENT:
      return
    if self.EVENT_TO_TIER[event_type] != self.pouring_tier:
      raise ValueError('Got back pour END event that did not match currently '
                       'pouring drink')
    print('Done pouring %s' % self.tier_to_drink[self.pouring_tier])
    self.pouring_tier = None
    pygame.time.set_timer(self.LIGHT_EVENT, LIGHT_TIME_MS)

class Robot(BaseRobot):
  def __init__(self):
    super().__init__()
    self.tier_to_switch = {
      0: (LED(0), LED(5)),
      1: (LED(6), LED(13)),
      2: (LED(19),),
    }
    self.light_switch = LED(26)

  def pour_drink(self, tier):
    super().pour_drink(tier)
    switches = self.tier_to_switch[tier]
    for switch in switches:
      switch.on()

  def handle_event_type(self, event_type):
    if event_type == self.LIGHT_EVENT:
      self.light_switch.off()
      super().handle_event_type(event_type)
      return
    else:
      switches = self.tier_to_switch[self.pouring_tier]
      for switch in switches:
        switch.off()
      self.light_switch.on()
      super().handle_event_type(event_type)

# If we have the gpiozero library, we're on the Pi so use the real robot.
# Otherwise use the base/fake robot.
try:
  from gpiozero import LED
  robot = Robot()
except ImportError:
  robot = BaseRobot()

ARCADE_FONT_NAME = 'Gameplay.ttf'
MONO_FONT_NAME = 'DejaVuSansMono.ttf'

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
clr_neon_yellow = pygame.Color('#F3F360')
fnt_arcade_50 = pygame.font.Font(ARCADE_FONT_NAME, 50)
fnt_arcade_80 = pygame.font.Font(ARCADE_FONT_NAME, 80)
fnt_arcade_150 = pygame.font.Font(ARCADE_FONT_NAME, 150)
fnt_arcade_100 = pygame.font.Font(ARCADE_FONT_NAME, 100)
fnt_arcade_140 = pygame.font.Font(ARCADE_FONT_NAME, 140)
fnt_arcade_260 = pygame.font.Font(ARCADE_FONT_NAME, 260)
fnt_mono_200 = pygame.font.Font(MONO_FONT_NAME, 200)
fnt_mono_120 = pygame.font.Font(MONO_FONT_NAME, 120)
fnt_mono_100 = pygame.font.Font(MONO_FONT_NAME, 100)
NAME_OFFSET_Y = 40

snd_target_hit = pygame.mixer.Sound(file='sound_fx/trolley-bell-1.wav')
snd_start_game = pygame.mixer.Sound(file='sound_fx/click-sweeper-bright-1.wav')
snd_forward = pygame.mixer.Sound(file='sound_fx/click-synth-shimmer.wav')
snd_accepted = pygame.mixer.Sound(file='sound_fx/click-synth-flutter.wav')
snd_backward = pygame.mixer.Sound(file='sound_fx/click-soft-digital.wav')
snd_denied = pygame.mixer.Sound(file='sound_fx/click-double-digital.wav')

title_surfaces = []
for i in range(50):
  filename = 'title/title%02d.jpg' % i
  s = pygame.image.load(filename)
  title_surfaces.append(s.convert())

spinner_surfaces = []
for i in range(50):
  filename = 'spinner/spinner%02d.jpg' % i
  s = pygame.image.load(filename)
  spinner_surfaces.append(s.convert())

class TitleDisplay(object):
  def __init__(self, game):
    self.game = game
    self.elapsed = 0
    self.total_time = 0
    self.idx = 0

  def draw(self):
    screen.blit(title_surfaces[self.idx], (0, 0))

  def update(self, tick):
    self.elapsed += tick
    self.total_time += tick
    if self.total_time > 8000:
      self.game.goto_high_scores()
      return
    if self.elapsed > 30:
      self.elapsed = 0
      self.idx += 1
      if self.idx == len(title_surfaces):
        self.idx = 0

  def handle_key(self, keycode):
    if keycode == pygame.K_SPACE:
      self.game.goto_main()

class GameOverDisplay(object):
  def __init__(self, game):
    self.game = game
    self.top = pygame.Surface(half)
    self.bottom = pygame.Surface(half)
    self.txt_game = fnt_arcade_260.render('GAME', 1, clr_neon_pink)
    self.txt_over = fnt_arcade_260.render('OVER', 1, clr_neon_pink)
    self.elapsed = 0
    self.total_time = 0

    self.colors = [clr_neon_blue, clr_neon_green, clr_neon_pink]
    self.top_idx = 0
    self.bottom_idx = 1
    if USE_MUSIC and not pygame.mixer.music.get_busy():
      pygame.mixer.music.load('sound_fx/bass-z.wav')
      pygame.mixer.music.play(-1)

  def draw(self):
    self.top.fill(self.colors[self.top_idx])
    self.bottom.fill(self.colors[self.bottom_idx])
    game_x = (width - self.txt_game.get_width()) // 2
    game_y = (height//2 - self.txt_game.get_height()) // 2
    self.top.blit(self.txt_game, (game_x, game_y))
    over_x = (width - self.txt_over.get_width()) // 2
    over_y = (height//2 - self.txt_over.get_height()) // 2
    self.bottom.blit(self.txt_over, (over_x, over_y))
    screen.blit(self.top, (0, 0))
    screen.blit(self.bottom, (0, height//2))

  def update(self, tick):
    self.total_time += tick
    if self.total_time > 6000:
      self.game.goto_title()
      return
    self.elapsed += tick
    if self.elapsed > 150:
      self.elapsed = 0
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
      txt_scored = fnt_arcade_260.render(score_str, 1, clr_neon_green)
      score_x = (width - txt_scored.get_width()) // 2
      score_y = (height // 2 - txt_scored.get_height()) // 2
      self.surface.blit(txt_scored, (score_x, score_y))
    else:
      self.surface.fill(self.fill_color)

  def update(self, tick):
    if self.cycles >= 18:
      self.showing = False
      return

    self.elapsed += tick
    if (self.cycles >= 1 and self.elapsed > 50) or self.elapsed > 600:
      self.elapsed = 0
      self.cycles += 1
      self.showing = not self.showing

class GetReadyDisplay(object):
  def __init__(self, game, display_player=None):
    self.game = game
    self.display_player = display_player
    self.showing = True
    self.blink_elapsed = 0
    self.elapsed = 0
    self.countdown = 5

  def draw(self):
    screen.fill(clr_neon_blue)
    if self.display_player:
      player_string = 'Player %s' % self.display_player
      txt_player = fnt_arcade_100.render(player_string, 1, clr_neon_pink)
      player_x = (width - txt_player.get_width()) // 2
      screen.blit(txt_player, (player_x, 100))

    if self.showing:
      txt_ready = fnt_arcade_100.render('Get ready!', 1, clr_neon_pink)
      ready_x = (width - txt_ready.get_width()) // 2
      screen.blit(txt_ready, (ready_x, 225))

    txt_countdown = fnt_arcade_140.render(str(self.countdown), 1, clr_black)
    countdown_x = (width - txt_countdown.get_width()) // 2
    screen.blit(txt_countdown, (countdown_x, 400))

  def update(self, tick):
    self.blink_elapsed += tick
    self.elapsed += tick

    if self.blink_elapsed > 50:
      self.blink_elapsed = 0
      self.showing = not self.showing

    if self.elapsed >= 1000:
      self.elapsed = 0
      self.countdown -= 1
      if self.countdown == 0:
        self.game.start_game()

  def handle_key(self, keycode):
    pass

class MainDisplay(object):
  def __init__(self, game):
    self.game = game
    self.top = pygame.Surface(half)
    self.bottom = pygame.Surface(half)
    self.txt_score_header = fnt_arcade_100.render('SCORE:', 1, clr_neon_pink)
    self.txt_time_header = fnt_arcade_100.render('TIME:', 1, clr_black)
    self.animate_score = None

    self.rem_secs = GAME_DURATION_SECS
    self.elapsed = 0
    if USE_MUSIC:
      pygame.mixer.music.load('game_loop.wav')
      pygame.mixer.music.play(-1)

  def draw(self):
    txt_score = fnt_arcade_140.render(str(game.score), 1, clr_neon_pink)
    txt_time = fnt_arcade_140.render(str(self.rem_secs), 1, clr_black)
    self.top.fill(clr_neon_blue)
    if self.animate_score:
      self.animate_score.draw()
    else:
      self.bottom.fill(clr_black)

    self.top.blit(self.txt_score_header, (10, -5))
    self.top.blit(self.txt_time_header, (640, -5))
    self.top.blit(txt_score, (40, 110))
    self.top.blit(txt_time, (680, 110))
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
      snd_target_hit.play()
      self.game.score += plus_score
      if self.animate_score:
        self.animate_score.showing = False
        self.animate_score.draw()
      self.animate_score = ScoreAnimation(self.bottom, plus_score)

class PlayerSelect(object):
  def __init__(self, game):
    self.game = game
    self.elapsed = 0
    self.top = pygame.Surface(quarter)
    self.bottom = pygame.Surface(three_quarters)
    self.selection_showing = True
    self.left_arrow = Arrow('<', self)
    self.right_arrow = Arrow('>', self)
    self.focus = 'left'
    self.players = 1

  def draw(self):
    self.top.fill(clr_black)
    self.bottom.fill(clr_neon_yellow)
    txt_many = fnt_arcade_80.render('How many players?', 1, clr_white)
    many_x = (width - txt_many.get_width()) // 2
    many_y = (height // 4 - txt_many.get_height()) // 2
    self.top.blit(txt_many, (many_x, many_y))

    self.left_arrow.draw(self.bottom, (10, 150))
    self.right_arrow.draw(self.bottom, (900, 150))

    if self.selection_showing:
      players_string = '%s players' % self.players
      if self.players == 1:
        players_string = '1 player'
      txt_players = fnt_arcade_100.render(players_string, 1, clr_neon_pink)
      players_x = (width - txt_players.get_width()) // 2
      players_y = ((height * 3 // 4 - txt_players.get_height()) // 2 +
                   NAME_OFFSET_Y // 2)
      self.bottom.blit(txt_players, (players_x, players_y))

    screen.blit(self.top, (0, 0))
    screen.blit(self.bottom, (0, height//4))

  def update(self, tick):
    self.left_arrow.update(tick)
    self.right_arrow.update(tick)
    self.elapsed += tick
    if self.elapsed > 150:
      self.elapsed = 0
      self.selection_showing = not self.selection_showing

  def handle_key(self, keycode):
    if keycode == pygame.K_COMMA:
      self.dec_players()
    elif keycode == pygame.K_PERIOD:
      self.inc_players()
    elif keycode == pygame.K_SPACE:
      self.game.set_players(self.players)
      snd_start_game.play()
      self.game.goto_get_ready()

  def dec_players(self):
    self.left_arrow.animating = True
    self.next_players = self.players - 1
    if self.next_players == 0:
      self.next_players = 4

  def inc_players(self):
    self.right_arrow.animating = True
    self.next_players = self.players + 1
    if self.next_players == 5:
      self.next_players = 1

  def animation_done(self):
    self.players = self.next_players

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
    txt = fnt_mono_200.render(self.text, 1, color)
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
        self.state.animation_done()

class DrinkDisplay(object):
  def __init__(self, game, display_player=None):
    self.game = game
    self.display_player = display_player
    self.elapsed = 0
    self.top = pygame.Surface(quarter)
    self.bottom = pygame.Surface(three_quarters)
    self.drink_showing = True
    self.left_arrow = Arrow('<', self)
    self.right_arrow = Arrow('>', self)
    self.focus = 'left'
    self.init_tier()
    if USE_MUSIC:
      pygame.mixer.music.load('sound_fx/bass-z.wav')
      pygame.mixer.music.play(-1)

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
    score_string = 'Score: %s pts' % self.game.score
    if self.display_player:
      score_string = 'Player %s: %s pts' % (
        self.display_player, self.game.score)
    txt_score = fnt_arcade_80.render(score_string, 1, clr_white)
    score_x = (width - txt_score.get_width()) // 2
    self.top.blit(txt_score, (score_x, 20))

    self.left_arrow.draw(self.bottom, (10, 150))
    self.right_arrow.draw(self.bottom, (900, 150))

    pts_string = str(self.current_tier['score'])
    while len(pts_string) < 3:
      pts_string = ' ' + pts_string
    tier_string = 'Tier %s: %s pts' % (self.current_tier['tier'], pts_string)
    txt_tier = fnt_arcade_80.render(tier_string, 1, clr_black)
    self.bottom.blit(txt_tier, (score_x, 10))

    drink_color = clr_black if self.current_tier['locked'] else clr_neon_pink
    if self.current_tier['locked'] or self.drink_showing:
      if self.current_tier['tier'] == 1:
        txt_drink_1 = fnt_arcade_80.render(
          self.current_tier['drink'].split(' ')[0], 1, drink_color)
        txt_drink_2 = fnt_arcade_80.render(
          self.current_tier['drink'].split(' ')[1], 1, drink_color)
        drink_1_x = (width - txt_drink_1.get_width()) // 2
        drink_2_x = (width - txt_drink_2.get_width()) // 2
        drink_1_y = ((height * 3 // 4 - txt_drink_1.get_height()) // 2 +
                     NAME_OFFSET_Y // 2)
        drink_2_y = drink_1_y + txt_drink_1.get_height() + 5
        self.bottom.blit(txt_drink_1, (drink_1_x, drink_1_y))
        self.bottom.blit(txt_drink_2, (drink_2_x, drink_2_y))
      else:
        txt_drink = fnt_arcade_80.render(
          self.current_tier['drink'], 1, drink_color)
        drink_x = (width - txt_drink.get_width()) // 2
        drink_y = ((height * 3 // 4 - txt_drink.get_height()) // 2 +
                   NAME_OFFSET_Y)
        self.bottom.blit(txt_drink, (drink_x, drink_y))

    if self.current_tier['locked'] and self.drink_showing:
      txt_locked = fnt_arcade_50.render('-LOCKED-', 1, clr_neon_pink)
      locked_x = (width - txt_locked.get_width()) // 2
      locked_y = (height * 3 // 4 - txt_locked.get_height() - 20)
      self.bottom.blit(txt_locked, (locked_x, locked_y))

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
    snd_backward.play()
    self.left_arrow.animating = True
    next_tier_idx = self.current_tier['tier'] - 1 - 1
    if next_tier_idx == -1:
      next_tier_idx = len(self.tiers) - 1
    self.next_tier = self.tiers[next_tier_idx]

  def up_tier(self):
    snd_backward.play()
    self.right_arrow.animating = True
    next_tier_idx = self.current_tier['tier'] - 1 + 1
    if next_tier_idx == len(self.tiers):
      next_tier_idx = 0
    self.next_tier = self.tiers[next_tier_idx]

  def animation_done(self):
    self.current_tier = self.next_tier

  def pour_drink(self):
    if self.current_tier['locked']:
      snd_denied.play()
    else:
      snd_accepted.play()
      self.game.set_drink_to_pour(self.current_tier['tier'] - 1)
      self.game.try_to_pour_drink()
      self.game.goto_enter_score()

class Initials(object):
  delete = '⌫'
  space = '␣'
  checkmark = '✓'
  alphabet = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
    'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3',
    '4', '5', '6', '7', '8', '9', '!', '@', '#', '-', '$', '&', '*', '(', ')',
    space, delete,
  ]
  last_spot = [checkmark, delete]

  def __init__(self, state):
    self.state = state
    self.elapsed = 0
    self.cur_showing = True
    self.top_idx = 0
    self.ltr_indices = [0, -1, -1, -1]

  def draw(self, surface):
    text = []
    positions = ((260, 40), (400, 40), (540, 40), (680, 40))
    for i in range(4):
      ltr = self.get_letter(i, show_space=self.top_idx == i)
      txt = fnt_mono_200.render(ltr, 1, clr_neon_pink)
      if self.top_idx != i or self.cur_showing:
        surface.blit(txt, positions[i])

  def update(self, tick):
    self.elapsed += tick
    if self.elapsed > 150:
      self.elapsed = 0
      self.cur_showing = not self.cur_showing

  def go_up(self):
    self.ltr_indices[self.top_idx] -= 1
    if self.ltr_indices[self.top_idx] == -1:
      if self.top_idx == 3:
        self.ltr_indices[self.top_idx] = len(self.last_spot) - 1
      else:
        self.ltr_indices[self.top_idx] = len(self.alphabet) - 1

  def go_down(self):
    self.ltr_indices[self.top_idx] += 1
    if ((self.top_idx == 3 and
         self.ltr_indices[self.top_idx] == len(self.last_spot)) or
        self.ltr_indices[self.top_idx] == len(self.alphabet)):
      self.ltr_indices[self.top_idx] = 0

  def get_letter(self, idx=None, show_space=False):
    if idx is None:
      idx = self.top_idx
    if self.ltr_indices[idx] == -1:
      return ' '
    elif idx == 3:
      return self.last_spot[self.ltr_indices[idx]]
    else:
      ltr = self.alphabet[self.ltr_indices[idx]]
      return ' ' if ltr == self.space and not show_space else ltr

  def enter(self):
    ltr = self.get_letter()
    if ltr == self.checkmark:
      snd_accepted.play()
      name = ''
      for i in range(3):
        name += self.get_letter(i)
      self.state.record_score(name)
    elif ltr == self.delete:
      snd_backward.play()
      if self.top_idx != 0:
        self.ltr_indices[self.top_idx] = -1
        self.top_idx -= 1
    else:
      snd_forward.play()
      self.top_idx += 1
      self.ltr_indices[self.top_idx] = 0

class EnterScoreDisplay(object):
  def __init__(self, game, display_player=None):
    self.game = game
    self.display_player = display_player
    self.elapsed = 0
    self.top = pygame.Surface(quarter)
    self.middle = pygame.Surface(quarter)
    self.bottom = pygame.Surface(half)
    self.initials = Initials(self)

  def draw(self):
    self.top.fill(clr_black)
    self.middle.fill(clr_neon_green)
    self.bottom.fill(clr_neon_green)

    score_string = 'Score: %s pts' % self.game.score
    if self.display_player:
      score_string = 'Player %s: %s pts' % (
        self.display_player, self.game.score)
    txt_score = fnt_arcade_80.render(score_string, 1, clr_white)
    score_x = (width - txt_score.get_width()) // 2
    self.top.blit(txt_score, (score_x, 20))

    txt_enter = fnt_arcade_80.render(
      'Enter your initials', 1, clr_black)
    enter_x = (width - txt_enter.get_width()) // 2
    self.middle.blit(txt_enter, (enter_x, 20))

    self.initials.draw(self.bottom)

    screen.blit(self.top, (0, 0))
    screen.blit(self.middle, (0, height//4))
    screen.blit(self.bottom, (0, height//2))

  def update(self, tick):
    self.initials.update(tick)

  def handle_key(self, keycode):
    if keycode == pygame.K_COMMA:
      self.initials.go_up()
    elif keycode == pygame.K_PERIOD:
      self.initials.go_down()
    elif keycode == pygame.K_SPACE:
      self.initials.enter()

  def record_score(self, name):
    if os.path.isfile('scores.json'):
      scores = json.load(open('scores.json'))
    else:
      scores = []
    idx = len(scores)
    for i, (_, score) in enumerate(scores):
      if game.score > score:
        idx = i
        break

    scores.insert(idx, [name, game.score])
    json.dump(scores, open('scores.json', 'w'))
    self.game.set_cur_player_initials(name)
    self.game.next_cycle()

class WinnerDisplay(object):
  def __init__(self, game):
    self.game = game
    self.elapsed = 0
    self.top = pygame.Surface(quarter)
    self.bottoms = []
    for i in range(4):
      self.bottoms.append(pygame.Surface((width // 2, height * 3 // 8)))
    self.showing = True

  def draw(self):
    self.top.fill(clr_black)

    winner_string = self.get_winners()
    if len(winner_string) > 20:
      txt_winner = fnt_arcade_50.render(winner_string, 1, clr_white)
    else:
      txt_winner = fnt_arcade_80.render(winner_string, 1, clr_white)
    winner_x = (width - txt_winner.get_width()) // 2
    winner_y = (height // 4 - txt_winner.get_height()) // 2
    self.top.blit(txt_winner, (winner_x, winner_y))

    coords = (
      (0, self.top.get_height()),
      (width // 2, self.top.get_height()),
      (0, (height + self.top.get_height()) // 2),
      (width // 2, (height + self.top.get_height()) // 2)
    )
    for i, (disp, coord) in enumerate(zip(self.bottoms, coords)):
      disp.fill(clr_neon_yellow)
      if i < self.game.total_players:
        color = clr_black
        if i + 1 in self.winning_players:
          color = clr_neon_pink

        if i + 1 not in self.winning_players or self.showing:
          txt_initials = fnt_arcade_80.render(self.game.scores[i][1], 1, color)
          initials_x = (disp.get_width() - txt_initials.get_width()) // 2
          initials_y = (disp.get_height() - txt_initials.get_height() * 2) // 2
          disp.blit(txt_initials, (initials_x, initials_y))
          txt_score = fnt_arcade_80.render(
            str(self.game.scores[i][0]), 1, color)
          score_x = (disp.get_width() - txt_score.get_width()) // 2
          score_y = initials_y + txt_initials.get_height()
          disp.blit(txt_score, (score_x, score_y))
      screen.blit(disp, coord)
    screen.blit(self.top, (0,0))

  def update(self, tick):
    self.elapsed += tick
    if self.elapsed > 50:
      self.elapsed = 0
      self.showing = not self.showing

  def handle_key(self, keycode):
    if keycode == pygame.K_SPACE:
      self.game.goto_game_over()

  def get_winners(self):
    winning_players = []
    winning_score = -1
    for i, score in enumerate(self.game.scores):
      if score[0] > winning_score:
        winning_players = [i + 1]
        winning_score = score[0]
      elif score[0] == winning_score:
        winning_players.append(i + 1)
    self.winning_players = winning_players

    if len(winning_players) > 1:
      return 'Players %s and %s tie!' % (
        ', '.join(str(s) for s in winning_players[0:-1]), winning_players[-1])
    else:
      return 'Player %s wins!' % winning_players[0]

class HighScoresDisplay(object):
  def __init__(self, game):
    self.game = game
    if os.path.isfile('scores.json'):
      self.scores = json.load(open('scores.json'))
    else:
      # Skip showing the scores if there are none.
      self.scores = []
    self.cur_top = None
    self.start_top = None
    self.elapsed = 0
    self.total_elapsed = 0
    self.show_top = True
    self.distance = 0
    self.velocity = 2
    self.accel = 1
    self.started_pos = False

  def draw(self):
    bg = pygame.Surface((width, height))

    score_surfaces = []
    total_height = 0
    total_width = 0
    for i, (name, score) in enumerate(self.scores):
      score_str = str(score)
      while len(score_str) < 4:
        score_str = ' ' + score_str
      if i < 3:
        score_line = '%s. %s %s' % (i+1, name, score_str)
        if i == 0 and not self.show_top:
          score_line = ' '
        txt = fnt_mono_120.render(score_line, 1, clr_neon_blue)
      else:
        txt = fnt_mono_100.render(
          '%s. %s %s' % (i+1, name, score_str), 1, clr_neon_blue)
      score_surfaces.append(txt)
      total_height += txt.get_height()
      if txt.get_width() > total_width:
        total_width = txt.get_width()

    scroll = pygame.Surface((total_width, total_height))
    scroll.fill(clr_neon_pink)
    cur_height = 0
    for txt in score_surfaces:
      scroll.blit(txt, ((total_width - txt.get_width())/2, cur_height))
      cur_height += txt.get_height()

    bg.fill(clr_neon_pink)
    if self.cur_top is None:
      self.start_top = self.cur_top = height - total_height
      mod = self.cur_top % 3
      if mod != 0:
        if self.cur_top < 0:
          self.cur_top -= mod
        else:
          self.cur_top += mod
    bg.blit(scroll, ((width - total_width)//2, self.cur_top))
    screen.blit(bg, (0, 0))

  def update(self, tick):
    self.elapsed += tick
    if len(self.scores) <= 0:
      self.game.goto_game_over()
      return
    if ((self.cur_top <= 0 and self.start_top > 0) or 
        (self.cur_top >= 0 and self.start_top < 0)):
      self.cur_top = 0
      self.total_elapsed += tick
      if self.elapsed > 80:
        self.show_top = not self.show_top
        self.elapsed = 0
      if self.total_elapsed > 6000:
        self.game.goto_game_over()
        return
    elif self.cur_top > 0:
      self.cur_top -= self.velocity
    elif self.cur_top < 0:
      self.cur_top += self.velocity

    if self.elapsed > 150:
      self.elapsed = 0
      self.velocity += self.accel

  def handle_key(self, keycode):
    if keycode == pygame.K_SPACE:
      self.game.goto_main()

class PleaseWaitDisplay(object):
  def __init__(self, game):
    self.game = game
    self.elapsed = 0
    self.elapsed_poll = 0
    self.idx = 0
    self.drink_for = game.drink_for
    self.done_pouring = False

  def draw(self):
    screen.fill(clr_neon_blue)
    screen.blit(spinner_surfaces[self.idx], (0, 0))

    pouring_string = 'Pouring drink for %s' % self.drink_for
    txt_pouring = fnt_arcade_50.render(pouring_string, 1, clr_neon_pink)
    pouring_x = (width - txt_pouring.get_width()) // 2
    screen.blit(txt_pouring, (pouring_x, 100))

    wait_string = 'Done pouring' if self.done_pouring else 'Please Wait'
    txt_wait = fnt_arcade_50.render(wait_string, 1, clr_neon_pink)
    wait_x = (width - txt_wait.get_width()) // 2
    screen.blit(txt_wait, (wait_x, 100 + txt_pouring.get_height()))

  def update(self, tick):
    self.elapsed += tick
    self.elapsed_poll += tick
    if self.elapsed > 30:
      self.elapsed = 0
      self.idx += 1
      if self.idx == len(spinner_surfaces):
        self.idx = 0
    if self.elapsed_poll > 6000:
      self.elapsed_poll = 0
      if not robot.is_pouring_drink():
        self.done_pouring = True

  def handle_key(self, keycode):
    if keycode == pygame.K_SPACE and self.done_pouring:
      self.game.next_cycle()

class Game(object):
  def __init__(self):
    self.clock = pygame.time.Clock()
    self.current_state = GameOverDisplay(self)
    self.score = 0
    self.scores = []
    self.total_players = 1
    self.drink_for = None

  def handle_key(self, keycode):
    self.current_state.handle_key(keycode)

  def draw(self):
    self.current_state.draw()

  def update(self):
    tick = self.clock.tick(30)
    result = self.current_state.update(tick)

  def start_game(self):
    self.score = 0
    self.poured_drink = False
    self.current_state = MainDisplay(self)

  def next_cycle(self):
    cur_player = self._get_cur_player()
    if not self.poured_drink:
      poured = self.try_to_pour_drink(blocking=True)
      if not poured:
        return
      else:
        self.drink_for = self.scores[self._get_cur_player() - 1][1]
    if cur_player == self.total_players:
      if cur_player != 1:
        self.goto_winner_display()
      else:
        self.goto_game_over()
    else:
      self.score = 0
      self.poured_drink = False
      self.goto_get_ready()

  def goto_get_ready(self):
    self.current_state = GetReadyDisplay(
      self, display_player=self._get_cur_player() + 1)

  def goto_main(self):
    self.scores = []
    self.total_players = 1
    self.current_state = PlayerSelect(self)

  def goto_game_over(self):
    self.current_state = GameOverDisplay(self)

  def goto_title(self):
    self.current_state = TitleDisplay(self)

  def goto_high_scores(self):
    self.current_state = HighScoresDisplay(self)

  def goto_drink(self):
    self.scores.append([self.score])
    self.current_state = DrinkDisplay(
      self, display_player=self._get_cur_player())

  def goto_enter_score(self):
    self.current_state = EnterScoreDisplay(
      self, display_player=self._get_cur_player())

  def goto_winner_display(self):
    self.current_state = WinnerDisplay(self)

  def set_cur_player_initials(self, initials):
    if not self.drink_for:
      self.drink_for = initials
    self.scores[self._get_cur_player() - 1].append(initials)

  def set_drink_to_pour(self, tier):
    self.drink_to_pour_tier = tier

  def set_players(self, players):
    self.total_players = players

  def try_to_pour_drink(self, blocking=False):
    if robot.is_pouring_drink():
      if blocking:
        self.current_state = PleaseWaitDisplay(self)
      return False
    robot.pour_drink(self.drink_to_pour_tier)
    self.poured_drink = True
    return True

  def _get_cur_player(self):
    return len(self.scores)

game = Game()

mask = pygame.Surface((width, height))
mask.fill(clr_white)
for y in range(height):
  if y % 5 == 0:
    pygame.draw.line(mask, clr_black, (0, y), (width, y))
mask.set_colorkey(clr_white)

while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      sys.exit()
    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        sys.exit()
      else:
        game.handle_key(event.key)
    elif event.type >= pygame.USEREVENT:
      robot.handle_event_type(event.type)

  screen.fill(clr_grey)
  game.update()
  game.draw()
  screen.blit(mask, (0, 0))
  pygame.display.flip()
