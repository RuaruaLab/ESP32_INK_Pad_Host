import time
import serial
import os
from image_conv import ImageToEPaperBuffer

def send_message(ser, cmd_id, data):
    frame_start = 0x5C
    frame_end = 0x7A
    
    data_length = len(data) + 2

    message = bytearray([frame_start, data_length, cmd_id]) + bytearray(data) + bytearray([frame_end])
    
    print("Complete message:", message.hex())
    ser.write(message)

def send_image(path):
    # -------------------图片转换----------------------
    converter = ImageToEPaperBuffer(path)
    converter.load_image()
    converter.resize_with_letterbox()
    converter.image_to_rgb_matrix()
    img_buffer = converter.process_image_to_buffer()
    converter.convert_image_to_4_colors()   #显示预览

    # 发送名片
    cmd_id = 0x01  # 命令ID

    packet_size = 64
    total_packets = len(img_buffer) // packet_size

    for i in range(total_packets):
        start_index = i * packet_size
        end_index = start_index + packet_size

        packet_data = img_buffer[start_index:end_index]
        packet = bytearray([i % 256]) + bytearray(packet_data)  # 包编号&数据

        send_message(ser, cmd_id, packet)  # CMD_ID = 0x01
        time.sleep(0.0001)

    remaining_data = len(img_buffer) % packet_size
    if remaining_data > 0:
        last_packet_data = img_buffer[-remaining_data:]
        last_packet = bytearray([total_packets % 256]) + bytearray(last_packet_data)
        send_message(ser, cmd_id, last_packet)


def send_wifi_credentials(ssid, password):
    ssid_length = len(ssid)
    password_length = len(password)

    if ssid_length > 32 or password_length > 64:
        raise ValueError("SSID or password length exceeds the limit")

    data = bytearray([ssid_length, password_length]) + ssid.encode() + password.encode()
    send_message(ser, 0x02, data)


def main():
    ser.open()

    print("Welcome! OMAMORI Project Configure Tool v1.0:")
    print("Copyright: SK DESIGNED 2024\n")
    print("Choose an option:")
    print("1. Set business card image")
    print("2. Set WiFi credentials")

    choice = input()

    if choice == '1':
        image_path = input("Enter the path to the image: ")
        if not os.path.isfile(image_path):
            print("File not found. Please enter a valid path.")
            return
        send_image(image_path)
    elif choice == '2':
        ssid = input("Enter the SSID: ")
        password = input("Enter the password: ")
        if len(ssid) > 32 or len(password) > 64:
            print("SSID or password length exceeds the limit")
            return
        if not ssid:
            print("SSID or password is empty or blank")
            return
        send_wifi_credentials(ssid, password)
    else:
        print("Invalid choice. Please enter '1' or '2'.")

    # send_image("test_img/test4.jpg")
    # send_wifi_credentials("ssid", "password")

    ser.close()

if __name__ == "__main__":
    ser = serial.Serial()
    ser.port = 'COM47'
    ser.baudrate = 115200
    ser.timeout = 1
    ser.dtr = False
    ser.rts = False

    main()