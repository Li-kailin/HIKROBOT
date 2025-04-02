#include "camera_class.h"
camera::camera()
{
    nRet = MV_OK;
    handle = NULL;
    g_bExit = false;
    g_nPayloadSize = 0;
    pDataForRGB  = (unsigned char*)malloc(3072 *2048 * 3 + 2048);
    memset(&stParam, 0, sizeof(MVCC_INTVALUE));
    CvtParam={0};
    stOutFrame = {0};
    memset(&stOutFrame, 0, sizeof(MV_FRAME_OUT));
}
void camera::start_cam()
{

    memset(&stDeviceList, 0, sizeof(MV_CC_DEVICE_INFO_LIST));
    nRet = MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, &stDeviceList);
    if (stDeviceList.nDeviceNum > 0)
    {
        for (unsigned int i = 0; i < stDeviceList.nDeviceNum; i++)
        {
            pDeviceInfo = stDeviceList.pDeviceInfo[i];
            if (NULL == pDeviceInfo)
            {
                break;
            }
            PrintDeviceInfo();
        }
    }else{
        cout<<"Find no Device"<<endl;
    }
    unsigned int nIndex = 0;
    MV_CC_CreateHandle(&handle, stDeviceList.pDeviceInfo[nIndex]);
    MV_CC_OpenDevice(handle);
    if (stDeviceList.pDeviceInfo[nIndex]->nTLayerType == MV_GIGE_DEVICE)
    {
        int nPacketSize = MV_CC_GetOptimalPacketSize(handle);
        if (nPacketSize > 0)
        {
            MV_CC_SetIntValue(handle,"GevSCPSPacketSize",nPacketSize);
        }else{
            cout<<"Warning: Get Packet Size fail"<<endl;
        }
    }
    MVCC_ENUMVALUE  p={0};
    MVCC_STRINGVALUE st;
    MV_CC_GetStringValue(handle,"DeviceModelName",&st);
    cout<<"DeviceModelName: "<<st.chCurValue<<endl;
    MV_CC_GetStringValue(handle,"DeviceVersion",&st);
    cout<<"DeviceVersion:\t"<<st.chCurValue<<endl;
    MV_CC_GetEnumValue(handle,"DeviceScanType",&p);
    if(p.nCurValue==0)
    {
        cout<<"DeviceScanType:\t"<<"Areascan"<<endl;

    }else{
        cout<<"DeviceScanType:\t"<<"Linescan"<<endl;
    }
    // MV_CC_SetEnumValue(handle, "TriggerMode", 0);
    // MV_CC_SetEnumValue(handle, "PixelFormat", 0x0210001F);
    // MV_CC_SetEnumValue(handle, "GainAuto", 1);
    // MV_CC_SetFloatValue(handle, "Gamma", 0.8);
    // MV_CC_SetBoolValue(handle, "GammaEnable", 1);
    // MV_CC_SetEnumValue(handle, "BalanceWhiteAuto", 2);
    // MV_CC_SetEnumValue(handle, "ExposureAuto", 1);
    // MV_CC_GetIntValue(handle, "PayloadSize", &stParam);
    g_nPayloadSize = stParam.nCurValue;
    nRet = MV_CC_StartGrabbing(handle);
    if (MV_OK == nRet)
        cout<<"Start Grabbing !"<<endl;
    cout<<"\nPress ESC to exit.\n";
}
void camera::PrintDeviceInfo()
{
    if (NULL == pDeviceInfo)
    {
        cout<<"null point"<<endl;
    }
    if (pDeviceInfo->nTLayerType == MV_GIGE_DEVICE)
    {
        int nIp1 = ((pDeviceInfo->SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24);
        int nIp2 = ((pDeviceInfo->SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16);
        int nIp3 = ((pDeviceInfo->SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8);
        int nIp4 = (pDeviceInfo->SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff);
        cout<<"IP:"<<nIp1<<"."<<nIp2<<"."<<nIp3<<"."<<nIp4<<endl;
    }
}
void camera::close_cam()
{
    int nRet = MV_CC_StopGrabbing(handle);
    if (MV_OK == nRet)
        cout<<"Stopped Grabbing !"<<endl;
}
void camera::get_pic(cv::Mat* srcimg)
{
    cout << "开始取图显示" << endl;
    // MV_CC_GetImageBuffer(handle, &stOutFrame, 400);
    CvtParam.enSrcPixelType=stOutFrame.stFrameInfo.enPixelType;
    CvtParam.enDstPixelType=PixelType_Gvsp_RGB8_Packed;
    CvtParam.nHeight=stOutFrame.stFrameInfo.nHeight;
    CvtParam.nWidth=stOutFrame.stFrameInfo.nWidth;
    CvtParam.nDstBufferSize=stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight *  3 + 2048;
    CvtParam.pSrcData=stOutFrame.pBufAddr;
    CvtParam.pDstBuffer=pDataForRGB;
    CvtParam.nSrcDataLen=stOutFrame.stFrameInfo.nFrameLen;
    MV_CC_ConvertPixelType(handle,&CvtParam);
    *srcimg=Mat(stOutFrame.stFrameInfo.nHeight,stOutFrame.stFrameInfo.nWidth,CV_8UC3,pDataForRGB);
    cvtColor(*srcimg,*srcimg,COLOR_RGB2BGR);
    if(NULL != stOutFrame.pBufAddr)
    {
        MV_CC_FreeImageBuffer(handle, &stOutFrame);
    }
}
void camera::re_iso()
{
    MV_CC_SetEnumValue(handle, "BalanceWhiteAuto", 2);
    MV_CC_SetEnumValue(handle, "ExposureAuto", 1);
}

