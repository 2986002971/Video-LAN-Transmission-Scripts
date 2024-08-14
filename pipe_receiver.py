#!/usr/bin/env python3

import socket
import subprocess
import cv2
import numpy as np
from multiprocessing import Process, Pipe


MULTICAST_GROUP = "224.0.0.1"
MULTICAST_PORT = 12345
DISCOVERY_TIMEOUT = 2  # seconds


def start_receiving(conn_write, port, decoder):
    # Define the FFmpeg command
    ffmpeg_command = [
        "ffmpeg",
        "-vcodec",
        decoder,
        "-f",
        "hevc",
        "-i",
        f"udp://0.0.0.0:{port}",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-fflags",
        "+genpts+nobuffer",  # Disable buffering
        "-flush_packets",
        "1",  # Force flushing packets
        "-",
        "-y",
    ]

    # Start the FFmpeg process
    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)

    try:
        # Write the output of FFmpeg to the pipe
        while True:
            chunk = ffmpeg_process.stdout.read(1920 * 1080 * 3)  # Read a frame
            if not chunk:
                break
            conn_write.send(chunk)
    finally:
        ffmpeg_process.terminate()
        conn_write.close()


def start_playing(conn_read):
    # Keep reading frames from the pipe
    while True:
        frame_data = conn_read.recv()
        if not frame_data:
            break

        # Convert the byte data to a NumPy array
        frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((1080, 1920, 3))
        cv2.imshow("UDP Stream", frame)

        # Check for the 'q' key to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Cleanup
    cv2.destroyAllWindows()
    conn_read.close()


def check_cuvid():
    try:
        # Use hevc_nvenc to test if the nvidia codec is available
        test_command = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=1920x1080:duration=1",
            "-c:v",
            "hevc_nvenc",
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


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Don't actually connect to anything, just need to create a socket
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = None
    finally:
        s.close()
    return IP


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def handle_discovery_request():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MULTICAST_PORT))
    mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            if data == b"DISCOVER":
                # Get the non-loopback IP address
                local_ip = get_local_ip()
                port = find_free_port()
                if local_ip:
                    sock.sendto(f"{local_ip}:{port}".encode(), addr)

                    # Check if the hevc_cuvid decoder is available
                    if check_cuvid():
                        decoder = "hevc_cuvid"
                    else:
                        decoder = "hevc"

                    # Create a pipe for communication between processes
                    parent_conn, child_conn = Pipe(duplex=False)

                    # Start the receiving process
                    receiving_process = Process(
                        target=start_receiving,
                        args=(
                            child_conn,
                            port,
                            decoder,
                        ),
                    )
                    receiving_process.start()

                    # Start the playing process
                    playing_process = Process(target=start_playing, args=(parent_conn,))
                    playing_process.start()

                    # Wait for the playing process to finish (it will exit when 'q' is pressed)
                    playing_process.join()
                    receiving_process.terminate()

                    # Close connections
                    parent_conn.close()
    finally:
        sock.close()


if __name__ == "__main__":
    handle_discovery_request()
