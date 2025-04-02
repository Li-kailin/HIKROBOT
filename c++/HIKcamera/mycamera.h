#ifndef MYCANERA_H
#define MYCANERA_H
#include "MvCameraControl.h"
#pragma execution_character_set("utf-8")   //设置当前文件为UTF-8编码
#pragma warning( disable : 4819 )    //解决SDK中包含中文问题；忽略C4819错误
#include <stdio.h>
#include <iostream>
#include "opencv2/core/core.hpp"
#include "opencv2/opencv.hpp"
#include "opencv2/highgui/highgui.hpp"
#include <string>
// #include <QDebug>

using namespace std;
using namespace cv;
class MyCanera
{
public:
    MyCanera();
   ~MyCanera();
    //声明相关变量及函数等
    //枚举相机设备列表
  static int EnumDevices(MV_CC_DEVICE_INFO_LIST* pstDevList);

  // ch:连接相机
  int connectCamera(string id);

  //设置相机触发模式
  int setTriggerMode(unsigned int TriggerModeNum);

  //开启相机采集
  int startCamera();

  //发送软触发
  int softTrigger();

  //读取buffer
  int ReadBuffer(Mat &image);

  //设置心跳时间
  int setHeartBeatTime(unsigned int time);

  //设置曝光时间
  int setExposureTime(float ExposureTimeNum);

//关闭相机
  int closeCamera();

private: 
  void* m_hDevHandle; 
public: 
  unsigned char* m_pBufForSaveImage; // 用于保存图像的缓存 
  unsigned int m_nBufSizeForSaveImage; 
  unsigned char* m_pBufForDriver; // 用于从驱动获取图像的缓存 
  unsigned int m_nBufSizeForDriver; 
  MV_CC_DEVICE_INFO_LIST m_stDevList; // ch:设备信息列表结构体变量，用来存储设备列表 
  MV_CC_DEVICE_INFO *m_Device = NULL; //设备对象 
};
#endif // MYCANERA_H

