
import cv2 as cv

# 显示图像
def show(title, image):
    cv.namedWindow(title, cv.WINDOW_NORMAL)
    cv.imshow(zh_ch(title), image)

# 解决中文乱码问题
def zh_ch(string):
    return string.encode("gbk").decode(errors="ignore")