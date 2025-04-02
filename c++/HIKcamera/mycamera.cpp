#include "mycamera.h"
// #include <QDebug>

MyCanera::MyCanera()
{
    m_hDevHandle    = NULL;
}

MyCanera::~MyCanera()
{
    if (m_hDevHandle)
    {
        MV_CC_DestroyHandle(m_hDevHandle);
        m_hDevHandle    = NULL;
    }
}

//查询设备列表
int MyCanera::EnumDevices(MV_CC_DEVICE_INFO_LIST* pstDevList)
{
    int temp= MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, pstDevList);
    if (MV_OK != temp)
    {
        return -1;
    }
    return 0;
}

//连接相机
//id:自定义相机名称
int  MyCanera::connectCamera(string id)
{
    int temp= EnumDevices(&m_stDevList);
    if(temp!=0)
        //设备更新成功接收命令的返回值为0，返回值不为0则为异常
        cout << "设备更新成功接收命令的返回值为0，返回值不为0则为异常" << endl;
        return -1;
    if(m_stDevList.nDeviceNum==0)
        //未找到任何相机
        cout << "未找到任何相机" << endl;
        return 2;
    for (unsigned int i = 0; i < m_stDevList.nDeviceNum; i++)
    {
        MV_CC_DEVICE_INFO* pDeviceInfo = m_stDevList.pDeviceInfo[i];
        if (NULL == pDeviceInfo)
        {
            // cout << "没有东西" <<endl;
            continue;
        }
        //qDebug() << (char*)pDeviceInfo->SpecialInfo.stGigEInfo.chUserDefinedName;//自定义相机名称
        cout << "......." << endl;
        //qDebug() << (char*)pDeviceInfo->SpecialInfo.stGigEInfo.chSerialNumber;//相机序列号
        if(id == (char*)pDeviceInfo->SpecialInfo.stGigEInfo.chUserDefinedName||id == (char*)pDeviceInfo->SpecialInfo.stGigEInfo.chSerialNumber)
        {
            m_Device= m_stDevList.pDeviceInfo[i];
            break;
        }else
        {
            continue;
        }
    }
    if(m_Device==NULL)
    {
        //未找到指定名称的相机
        // qDebug() << "未找到指定名称的相机";
        cout << "未找到指定名称的相机" << endl;
        return 3;
    }
    temp  = MV_CC_CreateHandle(&m_hDevHandle, m_Device);//创建句柄
    if(temp  !=0)
        return -1;

    temp  = MV_CC_OpenDevice(m_hDevHandle);//打开设备
    if (temp  !=0)
    {
        MV_CC_DestroyHandle(m_hDevHandle);
        m_hDevHandle = NULL;
        return -1;
    }else
    {
        setTriggerMode(0);//设置触发模式：1-打开触发模式 0-关闭触发模式
        return 0;
    }
    if (m_Device->nTLayerType == MV_GIGE_DEVICE)//设备类型为网络接口
    {
       std::cout<<"Gige Camera"<<std::endl;
    }
    cout << "相机连接" << endl;
}

//设置相机是否开启触发模式
int MyCanera::setTriggerMode(unsigned int TriggerModeNum)
{
    int nRet = MV_CC_SetTriggerMode(m_hDevHandle,TriggerModeNum);
    if (MV_OK != nRet)
    {
        return -1;
    }

}
//启动相机采集
int MyCanera::startCamera()
{
    int temp=MV_CC_StartGrabbing(m_hDevHandle);
    if(temp!=0)
    {
        // qDebug() << "抓图失败";
        cout << "抓图失败" << endl;
        return -1;
    }else
    {
        // qDebug() << "抓图成功";
        cout << "抓图成功" << endl;
        return 0;
    }
}
//发送软触发
int MyCanera::softTrigger()
{
    int enumValue = MV_CC_SetEnumValue(m_hDevHandle,"TriggerSource",MV_TRIGGER_SOURCE_SOFTWARE);
    if(enumValue != 0){
        // qDebug() << "设置软触发失败";
        return -1;
    }else {
        // qDebug() << "设置软触发";
    }
    int comdValue= MV_CC_SetCommandValue(m_hDevHandle, "TriggerSoftware");
    if(comdValue!=0)
    {
        // qDebug() << "软触发失败";
        return -1;
    }else
    {
        // qDebug() << "软触发一次";
        return 0;
    }
}
//读取相机中的图像
int MyCanera::ReadBuffer(Mat &image)
{
    unsigned int nBufSize = 0;//缓存大小
    MVCC_INTVALUE stIntvalue; //获取一帧数据的大小
    memset(&stIntvalue, 0, sizeof(MVCC_INTVALUE));
    int tempValue = MV_CC_GetIntValue(m_hDevHandle, "PayloadSize", &stIntvalue);
    if (tempValue != 0)
    {
        // qDebug() << "GetIntValue失败";
        cout << "GetIntValue失败" << endl;
        return -1;
    }else{
        // qDebug() << "GetIntValue成功";
        cout << "GetIntValue成功" << endl;
        }
    nBufSize = stIntvalue.nCurValue;
    m_pBufForDriver = (unsigned char *)malloc(nBufSize);
    MV_FRAME_OUT_INFO_EX stImageInfo;
    memset(&stImageInfo,0,sizeof(MV_FRAME_OUT_INFO));
    // qDebug() << MV_CC_StartGrabbing(m_hDevHandle);
    int timeout= MV_CC_GetOneFrameTimeout(m_hDevHandle, m_pBufForDriver, nBufSize, &stImageInfo, 1000);
    if(timeout!=0)
    {
        // qDebug() << "GetOneFrameTimeout失败";
        cout << "GetOneFrameTimeout失败" << endl;
        return -1;
    }
    m_nBufSizeForSaveImage = stImageInfo.nWidth * stImageInfo.nHeight * 3 + 2048;
    m_pBufForSaveImage = (unsigned char*)malloc(m_nBufSizeForSaveImage); //向系统申请M_nBufSizeForSaveImage内存空间

    bool isMono;//判断是否为黑白图像
    switch (stImageInfo.enPixelType) //像素格式
    {
    case PixelType_Gvsp_Mono8:
    case PixelType_Gvsp_Mono10:
    case PixelType_Gvsp_Mono10_Packed:
    case PixelType_Gvsp_Mono12:
    case PixelType_Gvsp_Mono12_Packed:
        isMono=true;
        break;
    default:
        isMono=false;
        break;
    }

    if(isMono)
    {
        image=Mat(stImageInfo.nHeight,stImageInfo.nWidth,CV_8UC1,m_pBufForDriver);
    }
    else
    {
        //转换图像格式为BGR8
        MV_CC_PIXEL_CONVERT_PARAM stConvertParam = {0};
        memset(&stConvertParam, 0, sizeof(MV_CC_PIXEL_CONVERT_PARAM));
        stConvertParam.nWidth = stImageInfo.nWidth;                 //ch:图像宽 | en:image width
        stConvertParam.nHeight = stImageInfo.nHeight;               //ch:图像高 | en:image height
        stConvertParam.pSrcData = m_pBufForDriver;                  //ch:输入数据缓存 | en:input data buffer
        stConvertParam.nSrcDataLen = stImageInfo.nFrameLen;         //ch:输入数据大小 | en:input data size
        stConvertParam.enSrcPixelType = stImageInfo.enPixelType;    //ch:输入像素格式 | en:input pixel format
        //stConvertParam.enDstPixelType = PixelType_Gvsp_BGR8_Packed; //ch:输出像素格式 | en:output pixel format  适用于OPENCV的图像格式
        stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed; //ch:输出像素格式 | en:output pixel format
        stConvertParam.pDstBuffer = m_pBufForSaveImage;                    //ch:输出数据缓存 | en:output data buffer
        stConvertParam.nDstBufferSize = m_nBufSizeForSaveImage;            //ch:输出缓存大小 | en:output buffer size
        MV_CC_ConvertPixelType(m_hDevHandle, &stConvertParam);
        image=Mat(stImageInfo.nHeight,stImageInfo.nWidth,CV_8UC3,m_pBufForSaveImage);
    }
    return 0;
}
//设置心跳时间
int MyCanera::setHeartBeatTime(unsigned int time)
{
    //心跳时间最小为500ms
    if(time<500)
        time=500;
    int temp=MV_CC_SetIntValue(m_hDevHandle, "GevHeartbeatTimeout", time);
    if(temp!=0)
    {
        return -1;
    }
    else
    {
        return 0;
    }
}
//设置曝光时间
int MyCanera::setExposureTime(float ExposureTimeNum)
{
    int temp= MV_CC_SetFloatValue(m_hDevHandle, "ExposureTime",ExposureTimeNum );
    if(temp!=0)
        return -1;
    return 0;
}
//关闭相机
int MyCanera::closeCamera()
{
    int nRet = MV_OK;
    if (NULL == m_hDevHandle)
    {
        // qDebug() << "没有句柄，不用关闭";
        return -1;
    }
    MV_CC_CloseDevice(m_hDevHandle);
    nRet = MV_CC_DestroyHandle(m_hDevHandle);
    m_hDevHandle = NULL;
    return nRet;
}