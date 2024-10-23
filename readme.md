## 项目简介
ESP32电子墨水屏，最基础的上位机

image_conv.py 把图像转换成墨水屏能接收的数据格式
main.py 主线程，但现在只有把图像通过串口发给esp32的功能
bdf_to_carray.py 把bdf点阵字库转换成c语言数组，方便程序使用