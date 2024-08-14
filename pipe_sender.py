#!/usr/bin/env python3

import socket
import subprocess
import os
import platform


MULTICAST_GROUP = "224.0.0.1"
MULTICAST_PORT = 12345
BROADCAST_PORT = MULTICAST_PORT
DISCOVERY_TIMEOUT = 2  # seconds


class Network:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.sock.settimeout(DISCOVERY_TIMEOUT)
        self.destination_ip = os.environ.get("DEFAULT_DST", None)
        # you can set DEFAULT_DST environment variable to the default destination IP
        self.destination_port = None
        self.discover_receiver()

    def discover_receiver(self):
        # Check if the DEFAULT_DST is set and pingable
        if self.destination_ip:
            print(
                f"Checking if default destination IP is reachable: {self.destination_ip}"
            )
            try:
                subprocess.check_call(
                    ["ping", "-c", "1", self.destination_ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )
                print(f"Using default destination IP: {self.destination_ip}")
                return
            except subprocess.CalledProcessError:
                print(f"your DEFAULT_DST {self.destination_ip} is unreachable")

        # Create a socket for multicast discovery
        print("Discovering receiver...")

        # Try to discover the receiver using multicast
        try:
            self.sock.sendto(b"DISCOVER", (MULTICAST_GROUP, MULTICAST_PORT))
            data, addr = self.sock.recvfrom(1024)
            self.destination_ip, self.destination_port = data.decode().split(":")
            print(f"Receiver found: {self.destination_ip}:{self.destination_port}")
            return
        except socket.timeout:
            print("Failed to discover receiver via multicast.")

        for _ in range(10):
            print(
                "About to UDP broadcast, please make sure you have sufficient permission."
            )

        # Fallback to broadcast discovery
        try:
            self.sock.sendto(b"DISCOVER", ("255.255.255.255", BROADCAST_PORT))
            data, addr = self.sock.recvfrom(1024)
            self.destination_ip, self.destination_port = data.decode().split(":")
            print(
                f"Receiver found via broadcast: {self.destination_ip}:{self.destination_port}"
            )
            return
        except socket.timeout:
            print("Failed to discover receiver.")
            return

    def build_ffmpeg_command(self, resolution, system, encoder):
        # Use the port obtained from the receiver
        ffmpeg_command = [
            "ffmpeg",
            "-video_size",
            resolution,
            "-framerate",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            encoder,
            "-bufsize",
            "100",  # Set buffer size to a very small value (e.g., 100 bytes)
            "-max_delay",
            "0",  # Disable buffering
            "-f",
            "hevc",  # Output format
            f"udp://{self.destination_ip}:{self.destination_port}",  # Destination IP and port
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

    def close(self):
        self.sock.close()


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


def start_streaming():
    network = Network()

    if network.destination_ip is None:
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
    ffmpeg_command = network.build_ffmpeg_command(resolution, system, encoder)
    process = subprocess.Popen(ffmpeg_command)
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
    finally:
        network.close()  # Make sure to close the network socket when done


if __name__ == "__main__":
    start_streaming()
