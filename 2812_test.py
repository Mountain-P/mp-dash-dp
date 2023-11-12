import json
import paho.mqtt.client as mqtt
import time
from numpy import interp
import board
import neopixel
import os
import re
from datetime import datetime
import threading
import subprocess
import socket

#####################
dashboard_id = socket.gethostname()
dashboard_web_url = "http://192.168.31.82:3000/dashboard/?_id="+dashboard_id
broker = "192.168.0.37"
broker_username = "rong"
broker_password = "00008888"

subprocess.Popen(
    ['chromium-browser', '--kiosk', '--display=:0', '--noerrdialogs', '--window-position=0,0', '--no-sandbox', dashboard_web_url])

#####################


def get_wlan0_ip():
    try:
        output = os.popen('ip addr show wlan0').read()
        ip = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', output).group(1)
        return ip
    except AttributeError:
        return "No IP Address found for wlan0"


length = 100
pixels = neopixel.NeoPixel(
    board.D10, length, brightness=0.8, auto_write=False, pixel_order=neopixel.RGB)
strip = neopixel.NeoPixel(
    board.D10, length, brightness=0.8, auto_write=False, pixel_order=neopixel.RGB)

# MQTT client setting
client = mqtt.Client(client_id=dashboard_id)
port = 1883
topic = "ledstrip"
client.username_pw_set(broker_username, broker_password)
client.connect(broker, port, 60)
client.keep_alive = 60

# MQTT client loop
client.loop_start()


def mqtt_heartbeat():
    topicOnline = "mountainp/team_dash/" + \
        dashboard_id + "/online"
    client.publish(topicOnline, "online : " +
                   datetime.now().strftime("%Y/%d/%m %H:%M:%S"))
    topicIp = "mountainp/team_dash/" + dashboard_id + "/ip"
    client.publish(topicIp, get_wlan0_ip())


mqtt_heartbeat()
# MQTT client subscribe


topicLed = "mountainp/team_dash/" + dashboard_id + "/ledstrip"
topicAllGetInfo = "mountainp/team_dash/all/getInfo"
topicWebDashbaord = "mountainp/team_dash/all/web_dashboard"
topicALLWebDashbaord = "mountainp/team_dash/" + dashboard_id + "/web_dashboard"
topicReloadBoot = "mountainp/team_dash/all/reload_boot"
topicReloadBootID = "mountainp/team_dash/" + dashboard_id + "/reload_boot"
topicMouse = "mountainp/team_dash/all/mouse"

client.subscribe(topicLed)
client.subscribe(topicAllGetInfo)
client.subscribe(topicWebDashbaord)
client.subscribe(topicALLWebDashbaord)
client.subscribe(topicReloadBoot)
client.subscribe(topicReloadBootID)
client.subscribe(topicMouse)

mqttbreak = False


def set_led_brightness(index, brightness):
    """Set the brightness of an individual LED."""
    if 0 <= index < length:
        brightness = max(0, min(255, int(255 * brightness))
                         )  # Clamp brightness to 0-255
        strip[index] = (brightness, brightness, brightness)


def white_flow(wait, tail_length=70):
    """Create a flowing white light effect with a fading tail and gradual entry."""
    global mqttbreak
    for i in range(length + tail_length):
        # Turn off all LEDs

        if mqttbreak:
            break
        for j in range(length):
            set_led_brightness(j, 0)

        # Gradually increase the brightness of the main LED
        main_led_brightness = 1.0 if i >= tail_length else i / tail_length

        # Set main LED
        set_led_brightness(i, main_led_brightness)

        # Set tail LEDs with decreasing brightness
        for k in range(1, tail_length):
            if i - k >= 0:
                set_led_brightness(
                    i - k, main_led_brightness * (1 - k/tail_length))

        strip.show()
        time.sleep(wait)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)


def rainbow_cycle(wait):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    global mqttbreak
    for j in range(255):
        if mqttbreak:
            break
        for i in range(length):
            pixel_index = (i * 256 // (length//2)) + j
            strip[i] = wheel(pixel_index & 255)
        strip.show()
        time.sleep(wait)


def fade_in_red(duration):
    """Fade in all LEDs over the specified duration."""
    steps = 10  # Number of steps in the fade
    step_duration = duration / steps  # Time each step takes
    global mqttbreak
    for step in range(steps):
        if mqttbreak:
            break
        brightness = step / steps
        for i in range(length):
            strip[i] = (int(0 * brightness), int(255 * brightness),
                        int(0 * brightness))  # White color
        strip.show()
        time.sleep(step_duration)


def fade_in_green(duration):
    """Fade in all LEDs over the specified duration."""
    steps = 20  # Number of steps in the fade
    step_duration = duration / steps  # Time each step takes
    global mqttbreak

    for step in range(steps):
        if mqttbreak:
            break
        brightness = step / steps
        for i in range(length):
            strip[i] = (int(0 * brightness), int(0 * brightness),
                        int(255 * brightness))  # White color
        strip.show()
        time.sleep(step_duration)


def fade_in_blue(duration):
    """Fade in all LEDs over the specified duration."""
    steps = 40  # Number of steps in the fade
    step_duration = duration / steps  # Time each step takes
    global mqttbreak
    for step in range(steps):
        if mqttbreak:
            break
        brightness = step / steps
        for i in range(length):
            strip[i] = (int(255 * brightness), int(0 * brightness),
                        int(0 * brightness))  # White color
        strip.show()
        time.sleep(step_duration)


def all_off():
    """Turn off all LEDs."""
    for i in range(length):
        strip[i] = (0, 0, 0)
    strip.show()


last_time = time.time()


def on_message(client, userdata, msg):
    global mqttbreak
    if (msg.topic == topicLed):
        mqttbreak = True
        data = json.loads(msg.payload)
        print(data)
        global strip_status
        global last_time
        try:
            data["set"]
        except KeyError:
            data["set"] = ""
        if (data["set"] == "white_flow"):
            strip_status = "white_flow"
        elif (data["set"] == "rainbow_cycle"):
            strip_status = "rainbow_cycle"
        elif (data["set"] == "fade_in_red"):
            strip_status = "fade_in_red"
        elif (data["set"] == "fade_in_green"):
            strip_status = "fade_in_green"
        elif (data["set"] == "fade_in_blue"):
            strip_status = "fade_in_blue"
        elif (data["set"] == "all_off"):
            strip_status = "all_off"
        last_time = time.time()
        time.sleep(0.1)
        mqttbreak = False
    if (msg.topic == topicAllGetInfo):
        print(msg.payload)
        mqtt_heartbeat()
    if (msg.topic == topicWebDashbaord or msg.topic == topicALLWebDashbaord):
        data = json.loads(msg.payload)
        try:
            data["set"]
        except KeyError:
            data["set"] = ""
        if (data["set"] == "on"):
            try:
                data["url"]
            except KeyError:
                data["url"] = dashboard_web_url
            subprocess.Popen(
                ['chromium-browser', '--kiosk', '--noerrdialogs', '--window-position=0,0', '--no-sandbox', dashboard_web_url])
        elif (data["set"] == "off"):
            subprocess.Popen(['killall', 'chromium-browser'])
    if (msg.topic == topicReloadBoot or msg.topic == topicReloadBootID):
        subprocess.Popen(['sudo', 'systemctl', 'restart', 'boot.service'])
    if (msg.topic == topicMouse):
        data = json.loads(msg.payload)
        try:
            data["set"]
        except KeyError:
            data["set"] = ""
        if (data["set"] == "on"):
            subprocess.Popen(['unclutter', '-display', ':0'])
        elif (data["set"] == "off"):
            subprocess.Popen(['killall', 'unclutter'])


client.on_message = on_message
client.loop_start()

strip_status = "white_flow"


# Main program loop:
while True:
    current_time = time.time()

    if strip_status == "white_flow":
        white_flow(0.01)
        if (current_time - last_time > 2):
            strip_status = "white_flow"
    elif strip_status == "rainbow_cycle":
        rainbow_cycle(0.001)
        if (current_time - last_time > 2):
            strip_status = "white_flow"
    elif strip_status == "fade_in_red":
        fade_in_red(0.1)
        if (current_time - last_time > 2):
            strip_status = "white_flow"
    elif strip_status == "fade_in_green":
        fade_in_green(0.5)
        if (current_time - last_time > 1.2):
            strip_status = "white_flow"
    elif strip_status == "fade_in_blue":
        fade_in_blue(0.24)
        if (current_time - last_time > 2):
            strip_status = "white_flow"
    elif strip_status == "all_off":
        all_off()

    # rainbow_cycle(0.001)  # rainbow cycle with 1ms delay per step

    # fade_in_red(0.24)  # Fade in over 0.8 seconds
    # all_off()     # Turn off LEDs
    # time.sleep(0.01)
    # fade_in_green(0.24)  # Fade in over 0.8 seconds
    # all_off()     # Turn off LEDs
    # time.sleep(0.01)
    # fade_in_blue(0.24)  # Fade in over 0.8 seconds
    # all_off()     # Turn off LEDs
    # time.sleep(0.01)

    # white_flow(0.01)  # Flow with 0.1ms delay per step


##############################################
# counter = 0

# # 初始化燈條陣列回黑色

# for i in range(length):
#     pixels[i] = (0, 0, 0)

# while True:
#     counter += 1
#     counter %= length
#     light_range = int(length/2)

#     # 先預設所有燈為黑色
#     for i in range(length):
#         pixels[i] = (20, 20, 20)

#     # 跑三分之一長的燈 設定顏色
#     for i in range(light_range):
#         c = int(interp(i, [0, light_range], [0, 255]))
#         if (counter-i) < 0:
#             break
#         pixels[counter-i] = (c, c, c)

#     pixels.show()
#     time.sleep(0.005)


# def gradient(color1, color2, steps):

#     r1, g1, b1 = color1
#     r2, g2, b2 = color2
#     step_r = (r2 - r1) / steps
#     step_g = (g2 - g1) / steps
#     step_b = (b2 - b1) / steps

#     for i in range(steps):
#         r = int(r1 + (i * step_r))
#         g = int(g1 + (i * step_g))
#         b = int(b1 + (i * step_b))
#         yield (r, g, b)


# NUM_LEDS = 100
# BRIGHTNESS = 1
# np = neopixel.NeoPixel(
#     board.D10, length, brightness=0.8, auto_write=False, pixel_order=neopixel.RGB)
# # 渐变循环
# while True:
#     # 渐变从红色到绿色
#     for color in gradient((255, 0, 0), (0, 255, 0), NUM_LEDS):
#         np.fill((int(color[0]*BRIGHTNESS), int(color[1]
#                 * BRIGHTNESS), int(color[2]*BRIGHTNESS)))
#         np.write()
#         time.sleep(0.01)
#     # 渐变从绿色到蓝色
#     for color in gradient((0, 255, 0), (0, 0, 255), NUM_LEDS):
#         np.fill((int(color[0]*BRIGHTNESS), int(color[1]
#                 * BRIGHTNESS), int(color[2]*BRIGHTNESS)))
#         np.write()
#         time.sleep(0.01)
#     # 渐变从蓝色到红色
#     for color in gradient((0, 0, 255), (255, 0, 0), NUM_LEDS):
#         np.fill((int(color[0]*BRIGHTNESS), int(color[1]
#                 * BRIGHTNESS), int(color[2]*BRIGHTNESS)))
#         np.write()
#         time.sleep(0.01)
