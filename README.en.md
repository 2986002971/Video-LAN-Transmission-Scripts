# Video Intranet Transmission Scripts
## Overview
This repository contains two Python scripts for video intranet transmission. The scripts utilize FFmpeg and OpenCV to capture and display video streams over a local network. The receiver script listens for incoming video streams, while the sender script captures and transmits the video. These scripts are optimized for low latency, which may result in a trade-off between picture quality and transfer stability.

-[Chinese](README.md)

## Prerequisites
- Python 3
- FFmpeg
- OpenCV
- NumPy
- pyautogui (for Windows sender script)
- xrandr (for Linux sender script)
## Installation
1. Install Python 3 from [python.org](https://www.python.org/downloads/).
2. Install FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
3. Install OpenCV and NumPy using pip:
```
pip install opencv-python numpy
```
4. For the Windows sender script, install pyautogui using pip:
```
pip install pyautogui
```
5. For the Linux sender script, install xrandr:
```
sudo apt-get install xrandr
```
## Usage
1. Run the receiver script first:
```
python receiver.py
```
2. Run the sender script on the device that will capture and transmit the video:
```
python sender.py
```
### Multicast LAN
By default, the scripts are configured to work on a multicast LAN. If your intranet supports multicast, you can simply run the scripts as described above.
### Unicast Setup
If your intranet does not support multicast, you have two options:
1. Set the receiver's IP address in the environment variable `DEFAULT_DST` on the sender's side. This can be done by running the following command before executing the sender script:
   ```
   export DEFAULT_DST=<receiver_ip>
   ```
   Replace `<receiver_ip>` with the actual IP address of the receiver.
2. Alternatively, you can turn on UDP privileges by running the sender script with administrative privileges. This allows the script to send UDP broadcasts to discover the receiver's IP address.
## Scripts
### receiver.py
The receiver script listens for incoming video streams on the specified multicast group and port. It uses FFmpeg to decode the video stream and OpenCV to display the video frames.
### sender.py
The sender script captures the video from the device's screen and transmits it to the receiver. It uses FFmpeg to encode the video stream and sends it to the specified multicast group and port.
## Configuration
The scripts can be configured by setting environment variables:
- `DEFAULT_DST`: Set the default destination IP address for the sender script.
- `DISPLAY`: Set the display number for the Linux sender script (default is ":0").
## Latency and Quality Trade-off
These scripts are optimized for low latency, which may result in a trade-off between picture quality and transfer stability. If you have different requirements, you can adjust the FFmpeg settings accordingly to balance latency, picture quality, and transfer stability.
## Security Considerations
Please note that the handshake between the two scripts and the transmission of the screen are completely unencrypted. Use caution if you have security concerns, as the video stream could potentially be intercepted or viewed by unauthorized users on the network.
## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
## Contributing
Contributions to this project are welcome. Please follow the standard GitHub contribution guidelines.
## Contact
For any questions or issues, please open an issue in the GitHub repository.
