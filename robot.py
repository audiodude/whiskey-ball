import pygame

from values import *

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
    pour_time = BASE_POUR_TIME_MS // 2
    if hasattr(self, 'tier_to_switch'):
      pour_time = BASE_POUR_TIME_MS // len(self.tier_to_switch[tier])
    pygame.time.set_timer(event, pour_time)

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
