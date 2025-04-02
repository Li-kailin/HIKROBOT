#include <stdio.h>
#include "opencv2/core.hpp"
#include "opencv2/imgproc.hpp"
#include "opencv2/highgui.hpp"
#include <opencv2/video/video.hpp>
#include <opencv2/opencv.hpp>
#include "camera_class.h"
#include "mycamera.h"

int main()
{
    Mat img;
    int key;
    // camera cam;
    // cam.start_cam();
    // while(1)
    // {
    //     cam.get_pic(&img);
    //     imshow("test",img);
    //     key=waitKey(1);
    //     if(key==27)
    //     {
    //         cam.close_cam();
    //         break;
    //     }
    // }

    MyCanera myCam;
    myCam.connectCamera("cam1");
    myCam.startCamera();
    while(1)
    {
        myCam.ReadBuffer(img);
        imshow("test",img);
        key=waitKey(1);
        if(key==27)
        {
            myCam.closeCamera();
            break;
        }
    }

}
