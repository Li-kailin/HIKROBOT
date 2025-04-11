import sys
import threading
import time
from ctypes import POINTER, sizeof, byref, memset, c_ubyte, cdll, cast, c_bool

import cv2 as cv
import numpy as np

from org.venus.tools.src.hk.MVCE20010UC.api.CameraParams_const import MV_GIGE_DEVICE, MV_USB_DEVICE, MV_ACCESS_Exclusive
from org.venus.tools.src.hk.MVCE20010UC.api.CameraParams_header import MV_CC_DEVICE_INFO_LIST, MV_CC_DEVICE_INFO, \
    MV_TRIGGER_MODE_OFF, MV_FRAME_OUT, MV_EXPOSURE_AUTO_MODE_CONTINUOUS, MV_GAIN_MODE_CONTINUOUS
from org.venus.tools.src.hk.MVCE20010UC.api.MvCameraControl_class import MvCamera
from org.venus.tools.src.hk.MVCE20010UC.api.PixelType_header import PixelType_Gvsp_YUV422_Packed
from org.venus.tools.src.hk.MVCE20010UC.config import ConstantsCommon
from org.venus.tools.src.hk.MVCE20010UC.utils import u


class Preview:
    flag = True

    def __init__(self):
        pass

    # 启动预览
    def startPreview(self):
        self.findDevices()

    # 查找设备
    def findDevices(self):
        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE

        # ch:枚举设备 | en:Enum device
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        if ret != 0:
            print("enum devices fail! ret[0x%x]" % ret)
            sys.exit()

        if deviceList.nDeviceNum == 0:
            print("find no device!")
            sys.exit()

        print("Find %d devices!" % deviceList.nDeviceNum)

        for i in range(0, deviceList.nDeviceNum):
            mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print("\ngige device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nu3v device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)

        if int(ConstantsCommon.ConnectionCameraNum) >= deviceList.nDeviceNum:
            print("请在配置文件中确定你将连接哪个设备")
            sys.exit()

        self.connDevice(deviceList, ConstantsCommon.ConnectionCameraNum)
        pass

    # 连接设备
    def connDevice(self, deviceList, ConnectionCameraNum):
        # ch:创建相机实例 | en:Creat Camera Object
        cam = MvCamera()

        # ch:选择设备并创建句柄 | en:Select device and create handle
        stDeviceList = cast(deviceList.pDeviceInfo[int(ConnectionCameraNum)],
                            POINTER(MV_CC_DEVICE_INFO)).contents

        ret = cam.MV_CC_CreateHandle(stDeviceList)
        if ret != 0:
            print("create handle fail! ret[0x%x]" % ret)
            sys.exit()

        self.openDevice(stDeviceList, cam, ConnectionCameraNum)
        pass

    # 打开设备
    def openDevice(self, stDeviceList, cam, ConnectionCameraNum):
        # ch:打开设备 | en:Open device
        ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, ConnectionCameraNum)
        if ret != 0:
            print("open device fail! ret[0x%x]" % ret)
            sys.exit()

        # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
        if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
            nPacketSize = cam.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                if ret != 0:
                    print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
            else:
                print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

        stBool = c_bool(False)
        ret = cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
        if ret != 0:
            print("get AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)
            sys.exit()
        self.configurationDevice(cam)
        pass

    # 配置设备参数
    def configurationDevice(self, cam):
        # ch:设置触发模式为off | en:Set trigger mode as off
        ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            print("set trigger mode fail! ret[0x%x]" % ret)
            sys.exit()

        '''
        设置一些属性:
        自动曝光:连续
        亮度:100
        自动增益:连续
        像素格式:YUV 422 Packed
        '''

        # ch:设置自动曝光为连续
        ret = cam.MV_CC_SetEnumValue("ExposureAuto", MV_EXPOSURE_AUTO_MODE_CONTINUOUS)
        if ret != 0:
            print("设置自动曝光为连续 失败! ret[0x%x]" % ret)
            sys.exit()

        # ch:设置自动增益为连续
        ret = cam.MV_CC_SetEnumValue("GainAuto", MV_GAIN_MODE_CONTINUOUS)
        if ret != 0:
            print("设置自动增益为连续 失败! ret[0x%x]" % ret)
            sys.exit()

        # ch:设置亮度为100
        ret = cam.MV_CC_SetIntValue("Brightness", ConstantsCommon.Brightness)
        if ret != 0:
            print("设置亮度为100 失败! ret[0x%x]" % ret)
            sys.exit()

        # ch:设置像素格式为PixelType_Gvsp_YUV422_Packed
        ret = cam.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_YUV422_Packed)
        if ret != 0:
            print("设置像素格式为PixelType_Gvsp_YUV422_Packed 失败! ret[0x%x]" % ret)
            sys.exit()

        self.readData(cam)
        pass

    # 读取相机数据
    def readData(self, cam):
        # ch:开始取流 | en:Start grab image
        ret = cam.MV_CC_StartGrabbing()
        if ret != 0:
            print("start grabbing fail! ret[0x%x]" % ret)
            sys.exit()

        try:
            hThreadHandle = threading.Thread(target=self.handleData, args=(cam, None, None))
            hThreadHandle.start()
        except:
            print("error: unable to start thread")

        print("press a key to stop grabbing.")

        # 执行下面代码线程就会阻塞
        # 但是我们不需要在这里阻塞,而是在子线程中去阻塞,所以这里的代码注释掉
        # msvcrt.getch()
        #
        # g_bExit = True
        # hThreadHandle.join()
        pass

    # 停止预览
    def stopPreview(self, cam):
        # ch:停止取流 | en:Stop grab image
        ret = cam.MV_CC_StopGrabbing()
        if ret != 0:
            print("stop grabbing fail! ret[0x%x]" % ret)
            sys.exit()

        # ch:关闭设备 | Close device
        ret = cam.MV_CC_CloseDevice()
        if ret != 0:
            print("close deivce fail! ret[0x%x]" % ret)
            sys.exit()

        # ch:销毁句柄 | Destroy handle
        ret = cam.MV_CC_DestroyHandle()
        if ret != 0:
            print("destroy handle fail! ret[0x%x]" % ret)
            sys.exit()

    # 处理数据,子线程函数
    def handleData(self, cam=0, pData=0, nDataSize=0):
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))
        while self.flag:
            startFrame = time.perf_counter()
            ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            # print("相机像素格式(PixelType_header.py文件中根据编码找到对应的格式)",stOutFrame.stFrameInfo.enPixelType)
            if None != stOutFrame.pBufAddr and 0 == ret and stOutFrame.stFrameInfo.enPixelType == 17301505:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
                    stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
                pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,
                                   stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)
                data = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight),
                                     dtype=np.uint8)
                self.imageConvert(data=data, stFrameInfo=stOutFrame.stFrameInfo)
            elif None != stOutFrame.pBufAddr and 0 == ret and stOutFrame.stFrameInfo.enPixelType == 17301514:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
                    stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
                pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,
                                   stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)
                data = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight),
                                     dtype=np.uint8)
                self.imageConvert(data=data, stFrameInfo=stOutFrame.stFrameInfo)
            elif None != stOutFrame.pBufAddr and 0 == ret and stOutFrame.stFrameInfo.enPixelType == 35127316:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
                    stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
                pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 3)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,
                                   stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 3)
                data = np.frombuffer(pData,
                                     count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 3),
                                     dtype=np.uint8)
                self.imageConvert(data=data, stFrameInfo=stOutFrame.stFrameInfo)
            elif None != stOutFrame.pBufAddr and 0 == ret and stOutFrame.stFrameInfo.enPixelType == 34603039:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
                    stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
                pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 2)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,
                                   stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 2)
                data = np.frombuffer(pData,
                                     count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 2),
                                     dtype=np.uint8)
                self.imageConvert(data=data, stFrameInfo=stOutFrame.stFrameInfo)
            else:
                print("no data[0x%x]" % ret)
            nRet = cam.MV_CC_FreeImageBuffer(stOutFrame)

            endFrame = time.perf_counter()
            print("相机一帧时间", str(endFrame - startFrame))
            pass
        self.stopPreview(cam)
        pass

    # 图像转换
    def imageConvert(self, data, stFrameInfo):
        if stFrameInfo.enPixelType == 17301505:
            image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
            self.imageResult(image=image)
        elif stFrameInfo.enPixelType == 17301514:
            data = data.reshape(stFrameInfo.nHeight, stFrameInfo.nWidth, -1)
            image = cv.cvtColor(data, cv.COLOR_BAYER_GB2RGB)
            self.imageResult(image=image)
        elif stFrameInfo.enPixelType == 35127316:
            data = data.reshape(stFrameInfo.nHeight, stFrameInfo.nWidth, -1)
            image = cv.cvtColor(data, cv.COLOR_RGB2BGR)
            self.imageResult(image=image)
        elif stFrameInfo.enPixelType == 34603039:
            data = data.reshape(stFrameInfo.nHeight, stFrameInfo.nWidth, -1)
            image = cv.cvtColor(data, cv.COLOR_YUV2BGR_Y422)
            self.imageResult(image=image)
        pass

    def imageResult(self, image):
        u.show("preview", image)
        if ConstantsCommon.WaitNextFrame:
            key = cv.waitKey()
            cv.destroyAllWindows()
            print(self, threading.currentThread())
            if (key == 27) | (key == 113):
                self.flag = False
                pass

        pass
