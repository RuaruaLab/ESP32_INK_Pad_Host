import time
import serial
import os
from image_conv import ImageToEPaperBuffer

def send_message(ser, cmd_id, data):
    # 帧头和帧尾
    frame_start = 0x5C
    frame_end = 0x7A
    
    data_length = len(data) + 2

    # 构建消息
    message = bytearray([frame_start, data_length, cmd_id]) + bytearray(data) + bytearray([frame_end])
    
    print("Complete message:", message.hex())
    # 发送消息
    ser.write(message)

# -------------------图片转换----------------------
converter = ImageToEPaperBuffer("test6.jpg")
converter.load_image()
converter.resize_with_letterbox()
converter.image_to_rgb_matrix()
img_buffer = converter.process_image_to_buffer()
converter.convert_image_to_4_colors()   #显示预览


# ------------------------串口发送-----------------------------
# 创建串口对象但不自动打开
ser = serial.Serial()
ser.port = 'COM4'
ser.baudrate = 115200
ser.timeout = 1

# 禁用DTR和RTS
ser.dtr = False
ser.rts = False

# 手动打开串口
ser.open()

# 发送图像数据
cmd_id = 0x01  # 命令ID

packet_size = 64
total_packets = len(img_buffer) // packet_size

for i in range(total_packets):
    # 计算每个包的起始和结束索引
    start_index = i * packet_size
    end_index = start_index + packet_size
    
    # 提取数据段并添加包编号
    packet_data = img_buffer[start_index:end_index]
    packet = bytearray([i % 256]) + bytearray(packet_data)  # 包编号加数据

    # 发送数据包
    send_message(ser, 0x01, packet)  # CMD_ID设置为0x01
    time.sleep(0.1)

# 处理最后一个包（如果有剩余的数据）
remaining_data = len(img_buffer) % packet_size
if remaining_data > 0:
    last_packet_data = img_buffer[-remaining_data:]
    last_packet = bytearray([total_packets % 256]) + bytearray(last_packet_data)
    send_message(ser, 0x01, last_packet)

# ser.write(bytearray([0x5c, 0x01, 0x7a]))
# 关闭串口
ser.close()