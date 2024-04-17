import serial
import time

serial_port = '/dev/cu.usbmodem143401'
baud_rate = 115200 
arduino = serial.Serial(serial_port, baud_rate, timeout=1)

def precise_sleep(delay):
    target = time.perf_counter_ns() + delay * 1000000
    while time.perf_counter_ns() < target:
        pass

def send_command(command, delay):
    """Send a command to the Arduino and wait for a specified delay."""
    arduino.write(command.encode())
    precise_sleep(delay)

try:
    for _ in range(20):  # Loop 20 times
        # Send commands as specified, with the respective delays
        send_command('[0G1G2G3G4G5G6G7G8G9GAGBGCGDGEGFG]', 50)
        send_command('[0C1A2G3G4G5G6G7G8G9GAGBGCGDGEGFG]', 50)
        send_command('[0G1G2G3G4C5A6G7G8G9GAGBGCGDGEGFG]', 50)
        send_command('[0G1G2G3G4G5G6G7G8G9GAGBGCGDGEGFG]', 50)
        precise_sleep(500)
finally:
    arduino.close()  # Ensure the serial connection is closed on completion
