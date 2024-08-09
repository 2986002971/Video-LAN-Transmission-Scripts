#!/usr/bin/env python3

import socket
import subprocess
import os
import platform
import time


MULTICAST_GROUP = "224.0.0.1"
MULTICAST_PORT = 12345
BROADCAST_PORT = MULTICAST_PORT
DISCOVERY_TIMEOUT = 2  # seconds
DESTINATION_IP = os.environ.get("DEFAULT_DST", None)
# you can set DEFAULT_DST environment variable to the default destination IP


def discover_receiver():
    global DESTINATION_IP

    # Check if the DEFAULT_DST is set and pingable
    if DESTINATION_IP:
        print(f"Checking if default destination IP is reachable: {DESTINATION_IP}")
        try:
            subprocess.check_call(
                ["ping", "-c", "1", DESTINATION_IP],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            print(f"Using default destination IP: {DESTINATION_IP}")
            return
        except subprocess.CalledProcessError:
            print(f"your DEFAULT_DST {DESTINATION_IP} is unreachable")

    # Create a socket for multicast discovery
    print("Discovering receiver...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(DISCOVERY_TIMEOUT)

    # Try to discover the receiver using multicast
    try:
        sock.sendto(b"DISCOVER", (MULTICAST_GROUP, MULTICAST_PORT))
        data, addr = sock.recvfrom(1024)
        DESTINATION_IP = addr[0]
        print(f"Receiver found via multicast: {DESTINATION_IP}")
        return
    except socket.timeout:
        pass

    for _ in range(10):
        print(
            "About to UDP broadcast, please make sure you have sufficient permission."
        )
    time.sleep(1)

    # Fallback to broadcast discovery
    try:
        sock.sendto(b"DISCOVER", ("255.255.255.255", BROADCAST_PORT))
        data, addr = sock.recvfrom(1024)
        DESTINATION_IP = addr[0]
        print(f"Receiver found via broadcast: {DESTINATION_IP}")
        return
    except socket.timeout:
        print("Failed to discover receiver.")
        return
    finally:
        sock.close()


def check_encoder(encoder):
    try:
        # Run a quick encoding job with the desired encoder
        test_command = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=1920x1080:duration=1",
            "-c:v",
            encoder,
            "-f",
            "null",
            "-",
        ]
        output = subprocess.run(
            test_command, check=True, capture_output=True
        ).stderr.decode()

        # Look for the string indicating that the encoder is not available
        if "Cannot load" in output:
            return False
        else:
            return True
    except subprocess.CalledProcessError:
        return False


def get_screen_resolution_and_platform():
    system = platform.system()

    if system == "Windows":
        import pyautogui

        resolution = f"{pyautogui.size().width}x{pyautogui.size().height}"
        # return resolution like "1920x1080"
    elif system == "Linux":
        output = subprocess.run(
            ["xrandr"], check=True, capture_output=True
        ).stdout.decode()

        lines = output.splitlines()
        for line in lines:
            if " connected " in line:  # Find the line with the connected display
                resolution = line.split(" ")[3].split("+")[0]
                # return resolution like "1920x1080" from "1920x1080+0+0"
                break
        else:
            raise Exception("No connected displays found.")
    else:
        raise Exception("Unsupported operating system.")

    return resolution, system


def build_ffmpeg_command(resolution, system, encoder):
    ffmpeg_command = [
        "ffmpeg",
        "-video_size",
        resolution,
        "-framerate",
        "30",
        "-c:v",
        encoder,
        "-bufsize",
        "100",  # Set buffer size to a very small value (e.g., 100 bytes)
        "-max_delay",
        "0",  # Disable buffering
        "-f",
        "hevc",  # Output format
        f"udp://{DESTINATION_IP}:1234",  # Destination IP and port
    ]

    if system == "Windows":
        # Use gdigrab for Windows
        input_format = [
            "-f",
            "gdigrab",
            "-i",
            "desktop",
        ]
    elif system == "Linux":
        # Use x11grab for Linux
        display = os.environ.get("DISPLAY", ":0")
        input_format = [
            "-f",
            "x11grab",
            "-i",
            display,
        ]

    ffmpeg_command = ffmpeg_command[:5] + input_format + ffmpeg_command[5:]

    return ffmpeg_command


def start_streaming():
    discover_receiver()

    if DESTINATION_IP is None:
        print("Could not find a receiver. Exiting.")
        return

    # Check if hevc_nvenc is available
    if check_encoder("hevc_nvenc"):
        encoder = "hevc_nvenc"
    elif check_encoder("libx265"):
        encoder = "libx265"
    else:
        raise Exception("Neither hevc_nvenc nor libx265 is available.")

    resolution, system = get_screen_resolution_and_platform()
    ffmpeg_command = build_ffmpeg_command(resolution, system, encoder)
    process = subprocess.Popen(ffmpeg_command)
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()


if __name__ == "__main__":
    start_streaming()
