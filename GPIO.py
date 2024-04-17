import panel as pn
from panel.widgets import CheckButtonGroup, Button
import gpiozero
import random
import time
import sys

class SimulatedGPIO:
    @staticmethod
    def setup(pin, mode):
        print(f"Setting up {pin} as {mode}")

    @staticmethod
    def output(pin, state):
        print(f"Setting {pin} to {state}")

GPIO = SimulatedGPIO
# Define the mappings for the electrode pins
channel_state = [None] * 16

oe_pin = 22
oe_device = None

le_gpio_pins = [ 23, 24, 25, 27 ]
le_gpio_devices = [ ]

def chan_to_le(chan):
    return (chan-1)%4


state2pin_logic_map = {
    "C" : [ 1, 0 ],
    "A" : [ 0, 1 ],
    "G" : [ 1, 1 ],
    "F" : [ 0, 0 ]
}


sp3t_selector_gpio_pins = [
    [5, 6],
    [12, 13],
    [16, 17],
    [19, 26]
]

sp3t_selector_gpio_devices = []



def chan_to_sp3t(chan):
    return int((chan-1)/4)

# UI sets channel_state array values to A/C/G#thencalls the folllwing routine
def precise_sleep(delay):
    target = time.perf_counter_ns() + delay * 1000
    while time.perf_counter_ns() < target:
        pass
def init_gpio_devices():
    global oe_device
    oe_device= gpiozero.DigitalOutputDevice(oe_pin)
    for inx in range(4):
        pins = sp3t_selector_gpio_pins[inx]
        sp3t_selector_gpio_devices.append([
            gpiozero.DigitalOutputDevice(pins[0]),
            gpiozero.DigitalOutputDevice(pins[1])
        ])
        le_gpio_devices.append(
            gpiozero.DigitalOutputDevice(le_gpio_pins[inx])
        )

def setup_and_latch():
    oe_device.on()
    for cgroup in range(0,4):
        le_pin = le_gpio_pins[cgroup]
        le_device=le_gpio_devices[cgroup]
        for rch in range(0, 4):
            channel = cgroup * 4 + rch
            state = channel_state[channel]
            sp3t_logic_values = state2pin_logic_map[state]
            print(f'{state= } {sp3t_logic_values= }')
            sp3t = ""
            #print("SP3T selector devies: ", sp3t_selector_gpio_devices[rch])
            for inx, device in enumerate(sp3t_selector_gpio_devices[rch]):
                sp3t_pins = sp3t_selector_gpio_pins[rch]
                logic = sp3t_logic_values
                #print(sp3t_pins, logic)
                sp3t += f' GPIO{sp3t_pins} = {logic}'
                if logic[inx] == 1:
                    device.on()
                else:
                    device.off()
                print(f'Setting {channel = }  {state = }, {cgroup = } {le_pin = } {sp3t}')
            
       
        le_device.on()
        precise_sleep(1000)
        le_device.off()
    oe_device.off()

def main():
    init_gpio_devices()
    #if len(sys.argv) == 2:
    #    ch_val=sys.argv[1]
    #else:
    #    ch_val = None
    #for i in range(16):
    #    channel_state[i] = ch_val if ch_val is not None else random.choice(["A", "C","G","F"])
    for i in range(20):
        channel_state = ["G","G","G","G","G","G","G","G","G","G","G","G","G","G","G","G"]
        print(f'{channel_state = }')
        precise_sleep(500000)
        channel_state = ["C","A","G","G","G","G","G","G","G","G","G","G","G","G","G","G"]
        print(f'{channel_state = }')
        setup_and_latch()
        precise_sleep(i*1000)
        channel_state = ["G","G","C","A","G","G","G","G","G","G","G","G","G","G","G","G"]
        print(f'{channel_state = }')
        setup_and_latch()
        precise_sleep(i*1000)
        channel_state = ["G","G","G","G","G","G","G","G","G","G","G","G","G","G","G","G"]
        print(f'{channel_state = }')
        precise_sleep(500000)


if __name__ == "__main__":
    main()
    time.sleep(100)