from flask import Flask, request, jsonify
import random
import gpiozero
import random
import time
import sys
import os
os.environ['GPIOZERO_PIN_FACTORY'] = os.environ.get('GPIOZERO_PIN_FACTORY', 'native')

# Import your GPIO control and setup functions here
# from your_gpio_module import SimulatedGPIO, init_gpio_devices, setup_and_latch

app = Flask(__name__)
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
        time.sleep(0.001)
        le_device.off()
    oe_device.off()

# Initialize GPIO devices
init_gpio_devices()

# Initially, set all channels to Floating (F)
channel_state = ["F"] * 16

@app.route('/api/set_channel', methods=['GET'])
def set_channel():
    channel = int(request.args.get('channel'))-1
    signal = request.args.get('signal')
    print(f'C{channel}, S{signal}')

    # Validate the input
    if not (0 <= int(channel) < 16):
        return jsonify({f'error': '{channel} is not a valid channel'}), 400
    if signal not in ['A', 'C', 'G', 'F']:
        return jsonify({f'error': '{signal} is not a valid signal'}), 400
    # Update the channel state
    channel_state[channel] = signal
    # Apply changes
    setup_and_latch()
    return jsonify({'message': f'Channel {channel + 1} set to {signal}'}), 200

@app.route('/api/set_all', methods=['GET'])
def set_all_channels():
    signals = request.args.get('signal')
    # Validate the input
    if len(signals) != 16:
        return jsonify({f'error': 'Incorrect Number of Signals {len(signals)}'}), 400
    
    
    # Update all channels to the specified state
    for i in range(16):
        if signals[i] not in ['A', 'C', 'G', 'F']:
            return jsonify({f'error': 'Found Invalid Signal {signals[i]} @ Channel {i+1}'}), 400
        channel_state[i] = signals[i]

    # Apply changes
    setup_and_latch()
    return jsonify({'message': f'All channels set to {channel_state}'}), 200

@app.route('/api/status', methods=['GET'])
def get_status():
    # Return the current status of all channels
    return jsonify(channel_state), 200

if __name__ == '__main__':
    app.run(debug=True)