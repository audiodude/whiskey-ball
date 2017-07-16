import time

from gpiozero import LED

tier_to_switch = {
  0: (LED(0), LED(5))
  1: (LED(6), LED(13))
  2: (LED(19),)
}

for idx, switches in tier_to_switch.items():
  for switch in switches:
    switch.on()

time.sleep(30)

for idx, switches in tier_to_switch.items():
  for switch in switches:
    switch.off()

