import time

from gpiozero import LED

tier_to_switch = {
  0: (LED(0), LED(5)),
  1: (LED(6), LED(13)),
  2: (LED(19),),
}

print('Writing high to pins, turning them on')
for idx, switches in tier_to_switch.items():
  for switch in switches:
    switch.on()

sleep = 30
print('Sleeping for %s seconds' % sleep)
time.sleep(sleep)

print('Writing low to pins, turning them off')
for idx, switches in tier_to_switch.items():
  for switch in switches:
    switch.off()

