import sys
from ctypes import *
import cv2
import numpy as np

sys.path.append("MvImport")
from MvCameraControl_class import *

class Camera(object):
    def __init__(self, camera_id=None):
        self.camera_id = camera_id
        self.camera = MvCamera()
        self.deviceList = MV_CC_DEVICE_INFO_LIST()
        self.data_buf = None

    def open_camera(self):
        # 获得设备信息
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        # ch:枚举设备 | en:Enum device
        # nTLayerType [IN] 枚举传输层 ，pstDevList [OUT] 设备列表 
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, self.deviceList)
        if ret != 0:
            print ("enum devices fail! ret[0x%x]" % ret)
            sys.exit()
    
        if self.deviceList.nDeviceNum == 0:
            print ("find no device!")
            sys.exit()
    
        print ("Find %d devices!" % self.deviceList.nDeviceNum)
        # ch:选择设备 | en:Select device
        m_Device = None
        for i in range(0, self.deviceList.nDeviceNum):
            mvcc_dev_info = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
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
                # 选择设备
                m = cast(mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName, c_char_p)
                if string_at(m).decode('gbk') == self.camera_id:
                    m_Device = mvcc_dev_info
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
        
        # 判断输入的相机用户ID的相机是否存在
        if m_Device == None:
            print ("camera_id: %s is not exist" % self.camera_id)
            sys.exit()
        # ch:选择设备并创建句柄 | en:Select device and create handle
        ret = self.camera.MV_CC_CreateHandle(m_Device)
        if ret != 0:
            print ("create handle fail! ret[0x%x]" % ret)
            sys.exit()
    
        # ch:打开设备 | en:Open device
        ret = self.camera.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print ("open device fail! ret[0x%x]" % ret)
            sys.exit()
        
        # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
        if m_Device.nTLayerType == MV_GIGE_DEVICE:
            nPacketSize = self.camera.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = self.camera.MV_CC_SetIntValue("GevSCPSPacketSize",nPacketSize)
                if ret != 0:
                    print ("Warning: Set Packet Size fail! ret[0x%x]" % ret)
            else:
                print ("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)
    
        # ch:设置触发模式为off | en:Set trigger mode as off
        ret = self.camera.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
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
        
        ret = self.camera.MV_CC_GetIntValue("PayloadSize", stParam)
        if ret != 0:
            print ("get payload size fail! ret[0x%x]" % ret)
            sys.exit()
        #关键句，官方没有这个句子，抓取的图片数据是空的，nCurValue是int64
        nPayloadSize = stParam.nCurValue
    
        # ch:开始取流 | en:Start grab image
        ret = self.camera.MV_CC_StartGrabbing()
        if ret != 0:
            print ("start grabbing fail! ret[0x%x]" % ret)
            sys.exit()
        #  关键句，官方没有这个句子，抓取的图片数据是空的，CSharp中怎么实现这句话。
        self.data_buf = (c_ubyte * nPayloadSize)()
        print("相机打开成功，开始取流！")

    def closs_camera(self):
        # ch:停止取流 | en:Stop grab image
        ret = self.camera.MV_CC_StopGrabbing()
        if ret != 0:
            print ("stop grabbing fail! ret[0x%x]" % ret)
            sys.exit()
    
        # ch:关闭设备 | en:Close device
        ret = self.camera.MV_CC_CloseDevice()
        if ret != 0:
            print ("close device fail! ret[0x%x]" % ret)
            sys.exit()
    
        # ch:销毁句柄 | en:Destroy handle
        ret = self.camera.MV_CC_DestroyHandle()
        if ret != 0:
            print ("destroy handle fail! ret[0x%x]" % ret)
            sys.exit()

    def image_control_return(self,data , stFrameInfo):
        if stFrameInfo.enPixelType == 17301505:
            image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
            return image
        elif stFrameInfo.enPixelType == 17301514:
            data = data.reshape(stFrameInfo.nHeight, stFrameInfo.nWidth, -1)
            image = cv2.cvtColor(data, cv2.COLOR_BAYER_GB2RGB)
            return image
        elif stFrameInfo.enPixelType == 35127316:
            data = data.reshape(stFrameInfo.nHeight, stFrameInfo.nWidth, -1)
            image = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
            return image
        elif stFrameInfo.enPixelType == 34603039:
            data = data.reshape(stFrameInfo.nHeight, stFrameInfo.nWidth, -1)
            image = cv2.cvtColor(data, cv2.COLOR_YUV2BGR_Y422)
            return image
        else:
            print("no data[0x%x]" % stFrameInfo.enPixelType)
            return None

    # 主动图像采集
    def access_get_image(self, active_way = "getImagebuffer"):
        """
        :param cam:     相机实例
        :active_way:主动取流方式的不同方法 分别是（getImagebuffer）（getoneframetimeout）
        :return:
        """
        if active_way == "getImagebuffer":
            stOutFrame = MV_FRAME_OUT()
            memset(byref(stOutFrame), 0, sizeof(stOutFrame))
            # while True:
            ret = self.camera.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if None != stOutFrame.pBufAddr and 0 == ret and stOutFrame.stFrameInfo.enPixelType == 17301505:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
                pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)
                data = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight),dtype=np.uint8)
                resultimage = self.image_control_return(data=data, stFrameInfo=stOutFrame.stFrameInfo)
                nRet = self.camera.MV_CC_FreeImageBuffer(stOutFrame)
                return resultimage
            elif None != stOutFrame.pBufAddr and 0 == ret and stOutFrame.stFrameInfo.enPixelType == 17301514:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
                pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)
                data = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight),dtype=np.uint8)
                resultimage = self.image_control_return(data=data, stFrameInfo=stOutFrame.stFrameInfo)
                nRet = self.camera.MV_CC_FreeImageBuffer(stOutFrame)
                return resultimage
            elif None != stOutFrame.pBufAddr and 0 == ret and stOutFrame.stFrameInfo.enPixelType == 35127316:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
                pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight*3)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight*3)
                data = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight*3),dtype=np.uint8)
                resultimage = self.image_control_return(data=data, stFrameInfo=stOutFrame.stFrameInfo)
                nRet = self.camera.MV_CC_FreeImageBuffer(stOutFrame)
                return resultimage
            elif None != stOutFrame.pBufAddr and 0 == ret and stOutFrame.stFrameInfo.enPixelType == 34603039:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
                pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 2)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 2)
                data = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 2),dtype=np.uint8)
                resultimage = self.image_control_return(data=data, stFrameInfo=stOutFrame.stFrameInfo)
                nRet = self.camera.MV_CC_FreeImageBuffer(stOutFrame)
                return resultimage
            else:
                print("no data[0x%x]" % ret)
                nRet = self.camera.MV_CC_FreeImageBuffer(stOutFrame)
                return None
    
        elif active_way == "getoneframetimeout":
            stParam = MVCC_INTVALUE_EX()
            memset(byref(stParam), 0, sizeof(MVCC_INTVALUE_EX))
            ret = self.camera.MV_CC_GetIntValueEx("PayloadSize", stParam)
            if ret != 0:
                print("get payload size fail! ret[0x%x]" % ret)
                sys.exit()
            nDataSize = stParam.nCurValue
            pData = (c_ubyte * nDataSize)()
            stFrameInfo = MV_FRAME_OUT_INFO_EX()
            memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
            # while True:
            ret = self.camera.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 1000)
            if ret == 0:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d] " % (stFrameInfo.nWidth, stFrameInfo.nHeight, stFrameInfo.nFrameNum))
                image = np.asarray(pData)
                resultimage = self.image_control_return(data=image, stFrameInfo=stFrameInfo)
                return resultimage
            else:
                print("no data[0x%x]" % ret)
                return None

