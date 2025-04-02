# -- coding: utf-8 --
import os
import sys
import time
import termios
import threading
from ctypes import *

import cv2
import numpy as np

sys.path.append("/opt/MVS/Samples/64/Python/MvImport")
from MvCameraControl_class import *

g_bExit = False
 
# 这是官方给的线程，只能捕获帧的信息，类似于get one frame: Width[3072], Height[2048], nFrameNum[711]
# 不能得到帧的数据
def work_thread(cam=0, pData=0, nDataSize=0):
    stFrameInfo = MV_FRAME_OUT_INFO_EX()
    memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
    while True:
        ret = cam.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 1000)
        if ret == 0:
            print ("get one frame: Width[%d], Height[%d], nFrameNum[%d]"  % (stFrameInfo.nWidth, stFrameInfo.nHeight, stFrameInfo.nFrameNum))
        else:
            print ("no data[0x%x]" % ret)
        if g_bExit == True:
                break
 #设置图像采集时间
def getnowtime():
    mstime=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    print(mstime)
    return mstime

"""
以下为图像处理函数，进行图像检测
"""
# 自己在这个线程中修改，可以将相机获得的数据转换成opencv支持的格式，然后再用opencv操作
def work_thread2(cam=0, pData=0, nDataSize=0):
    # 输出帧的信息
    stFrameInfo = MV_FRAME_OUT_INFO_EX()
    # void *memset(void *s, int ch, size_t n);
    # 函数解释:将s中当前位置后面的n个字节 (typedef unsigned int size_t )用 ch 替换并返回 s 
    # memset:作用是在一段内存块中填充某个给定的值，它是对较大的结构体或数组进行清零操作的一种最快方法
    # byref(n)返回的相当于C的指针右值&n，本身没有被分配空间
    # 此处相当于将帧信息全部清空了
    memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
    
    cv2.namedWindow("binary", cv2.WINDOW_NORMAL)
    cv2.namedWindow("ori", cv2.WINDOW_NORMAL)

    while True:
        temp = np.asarray(pData)  # 将c_ubyte_Array转化成ndarray得到（3686400，）

        temp = temp.reshape((2048, 3072, 3))  # 根据自己分辨率进行转化
        
        temp = cv2.cvtColor(temp, cv2.COLOR_RGB2BGR)  # 这一步获取到的颜色不对，因为默认是BRG，要转化成RGB，颜色才正常
        gray = cv2.cvtColor(temp,cv2.COLOR_BGR2GRAY)
        ret,binary = cv2.threshold(gray,130,255,cv2.THRESH_BINARY)
        cv2.imshow('binary',binary)
        # time.sleep(2)
        cv2.imshow("ori", temp)
        
            
        # 采用超时机制获取一帧图片，SDK内部等待直到有数据时返回，成功返回0
        ret = cam.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 1000)
        if ret == 0:
            print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
            stFrameInfo.nWidth, stFrameInfo.nHeight, stFrameInfo.nFrameNum))
        else:
            print("no data[0x%x]" % ret)
        if g_bExit == True:
            break

    # cv2.namedWindow("roi", cv2.WINDOW_NORMAL)
    # r = cv2.selectROI('roi', temp, False, False )
    # img_roi = temp[int(r[1]):int(r[1]+r[3]),int(r[0]):int(r[0]+r[2])]
    # savename='data/test_data/'+str(getnowtime())+'.jpg'
    # cv2.imwrite(savename,temp)
    # cv2.waitKey()   

if __name__ == "__main__":
    # 获得设备信息
    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
    
    # ch:枚举设备 | en:Enum device
    # nTLayerType [IN] 枚举传输层 ，pstDevList [OUT] 设备列表 
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    if ret != 0:
        print ("enum devices fail! ret[0x%x]" % ret)
        sys.exit()
 
    if deviceList.nDeviceNum == 0:
        print ("find no device!")
        sys.exit()
 
    print ("Find %d devices!" % deviceList.nDeviceNum)
 
    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
            print ("\ngige device: [%d]" % i)
            # 输出设备名字
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)
            # 输出设备ID
            nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        # 输出USB接口的信息
        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            print ("\nu3v device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)
 
            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print ("user serial number: %s" % strSerialNumber)
    # 选择设备
    # nConnectionNum = input("please input the number of the device to connect:")
    nConnectionNum = 0
 
    if int(nConnectionNum) >= deviceList.nDeviceNum:
        print ("intput error!")
        sys.exit()
 
    # ch:创建相机实例 | en:Creat Camera Object
    cam = MvCamera()
    
    # ch:选择设备并创建句柄 | en:Select device and create handle
    # cast(typ, val)，这个函数是为了检查val变量是typ类型的，但是这个cast函数不做检查，直接返回val
    stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents
 
    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print ("create handle fail! ret[0x%x]" % ret)
        sys.exit()
 
    # ch:打开设备 | en:Open device
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print ("open device fail! ret[0x%x]" % ret)
        sys.exit()
    
    # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
    if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
        nPacketSize = cam.MV_CC_GetOptimalPacketSize()
        if int(nPacketSize) > 0:
            ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize",nPacketSize)
            if ret != 0:
                print ("Warning: Set Packet Size fail! ret[0x%x]" % ret)
        else:
            print ("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)
 
    # ch:设置触发模式为off | en:Set trigger mode as off
    ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
    if ret != 0:
        print ("set trigger mode fail! ret[0x%x]" % ret)
        sys.exit()

    # 从这开始，获取图片数据
    # ch:获取数据包大小 | en:Get payload size
    stParam =  MVCC_INTVALUE()
    #csharp中没有memset函数，用什么代替？
    memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
    # MV_CC_GetIntValue，获取Integer属性值，handle [IN] 设备句柄  
    # strKey [IN] 属性键值，如获取宽度信息则为"Width"  
    # pIntValue [IN][OUT] 返回给调用者有关相机属性结构体指针 
    # 得到图片尺寸，这一句很关键
    # payloadsize，为流通道上的每个图像传输的最大字节数，相机的PayloadSize的典型值是(宽x高x像素大小)，此时图像没有附加任何额外信息
    
    ret = cam.MV_CC_GetIntValue("PayloadSize", stParam)
    if ret != 0:
        print ("get payload size fail! ret[0x%x]" % ret)
        sys.exit()
    #关键句，官方没有这个句子，抓取的图片数据是空的，nCurValue是int64
    nPayloadSize = stParam.nCurValue
 
    # ch:开始取流 | en:Start grab image
    ret = cam.MV_CC_StartGrabbing()
    if ret != 0:
        print ("start grabbing fail! ret[0x%x]" % ret)
        sys.exit()
    #  关键句，官方没有这个句子，抓取的图片数据是空的，CSharp中怎么实现这句话。
    data_buf = (c_ubyte * nPayloadSize)()
    #  date_buf前面的转化不用，不然报错，因为转了是浮点型
    try:
        hThreadHandle = threading.Thread(target=work_thread2, args=(cam, data_buf, nPayloadSize))
        hThreadHandle.start()
    except:
        print ("error: unable to start thread")
        
    print ("press a key to stop grabbing.")
    msvcrt.getch()
 
    g_bExit = True
    hThreadHandle.join()
 
    # ch:停止取流 | en:Stop grab image
    ret = cam.MV_CC_StopGrabbing()
    if ret != 0:
        print ("stop grabbing fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()
 
    # ch:关闭设备 | Close device
    ret = cam.MV_CC_CloseDevice()
    if ret != 0:
        print ("close deivce fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()
 
    # ch:销毁句柄 | Destroy handle
    ret = cam.MV_CC_DestroyHandle()
    if ret != 0:
        print ("destroy handle fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()
 
    del data_buf
