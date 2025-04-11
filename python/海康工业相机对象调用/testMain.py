import cv2
import camera_class

if __name__ == "__main__":
    # 实例化相机对象，传入连接相机名称（相机用户自定义name）
    camera = camera_class.Camera("2号")
    # 打开相机并开始取流
    camera.open_camera()
    # 图像展示窗口
    cv2.namedWindow("image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("image", 640, 480)

    while True:
        # 获取图像
        # 方式一：getImagebuffer 方式获取图像，返回值为图像数据
        # 方式二：getoneframetimeout 方式获取图像，返回值为图像数据
        image = camera.access_get_image(active_way="getoneframetimeout")  # getImagebuffer  or  getoneframetimeout
        # 图像展示
        cv2.imshow("image", image)
        # 键盘按下 q 退出程序
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # 销毁所有窗口
            cv2.destroyAllWindows()
            # 关闭相机
            camera.closs_camera()
            break

   