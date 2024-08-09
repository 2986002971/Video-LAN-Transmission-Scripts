# 视频内网传输脚本
## 概述
这个仓库包含两个用于视频内网传输的Python脚本。脚本使用FFmpeg和OpenCV捕获和显示本地网络上的视频流。接收器脚本监听传入的视频流，而发送器脚本捕获并发送视频。脚本针对低延迟进行了优化，您可能需要自行权衡图像质量，传输稳定性与延迟之间的关系。

-[English](README.en.md)

## 先决条件
- Python 3
- FFmpeg
- OpenCV
- NumPy
- pyautogui（用于Windows发送器脚本）
- xrandr（用于Linux发送器脚本）
## 安装
1. 从[python.org](https://www.python.org/downloads/)安装Python 3。
2. 从[ffmpeg.org](https://ffmpeg.org/download.html)安装FFmpeg。
3. 使用pip安装OpenCV和NumPy：
```
pip install opencv-python numpy
```
4. 对于Windows发送器脚本，使用pip安装pyautogui：
```
pip install pyautogui
```
5. 对于Linux发送器脚本，安装xrandr：
```
sudo apt-get install xrandr
```
## 使用方法
1. 首先运行接收器脚本：
```
python receiver.py
```
2. 在将捕获和发送视频的设备上运行发送器脚本：
```
python sender.py
```
### 多播局域网
默认情况下，脚本配置为在多播局域网上工作。如果您的内网支持多播，您可以简单地按照上述描述运行脚本。
### 单播设置
如果您的内网不支持多播，您有两个选择：
1. 在发送器的环境中设置接收器的IP地址，通过设置环境变量`DEFAULT_DST`。在执行发送器脚本之前，运行以下命令：
   ```
   export DEFAULT_DST=<receiver_ip>
   ```
   将`<receiver_ip>`替换为接收器的实际IP地址。
2. 或者，您可以开启UDP权限，通过以管理员权限运行发送器脚本。这将允许脚本发送UDP广播以发现接收器的IP地址。
## 脚本
### receiver.py
接收器脚本监听指定多播组和端口上的传入视频流。它使用FFmpeg解码视频流，并使用OpenCV显示视频帧。
### sender.py
发送器脚本捕获设备的屏幕视频，并将其传输到接收器。它使用FFmpeg编码视频流，并将其发送到指定的多播组和端口。
## 配置
脚本可以通过设置环境变量进行配置：
- `DEFAULT_DST`：为发送器脚本设置默认目标IP地址。
- `DISPLAY`：为Linux发送器脚本设置显示编号（默认为":0"）。
## 延迟与质量权衡
这些脚本针对低延迟进行了优化，可能会牺牲一些图像质量和传输稳定性。如果您有其他需求，可以调整FFmpeg设置以平衡延迟、图像质量和传输稳定性。
## 安全考虑
请注意，两个脚本之间的握手和屏幕传输是完全未加密的。如果您有安全顾虑，请谨慎使用，因为视频流可能被网络上的未授权用户截获或查看。
## 许可证
该项目在MIT许可证下授权 - 请参阅[LICENSE](LICENSE)文件以获取详细信息。
## 贡献
欢迎对此项目做出贡献。请遵循GitHub的标准贡献指南。
## 联系方式
如有任何问题或问题，请在GitHub仓库中开启一个issue。
