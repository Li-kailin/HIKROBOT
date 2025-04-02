# cmake needs this line
cmake_minimum_required(VERSION 3.1)
set(PROJECT_NAME1 "camera_class_project")
# Define project name
#set(CMAKE_BUILD_TYPE "Debug")
set(CMAKE_BUILD_TYPE "Release")
set(PROJ_DIR "/home/lkl/A-LKL/gig-e_camera")

project(${PROJECT_NAME1})
find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})
message(STATUS "OpenCV library status:")
message(STATUS "    config: ${OpenCV_DIR}")
message(STATUS "    version: ${OpenCV_VERSION}")
message(STATUS "    libraries: ${OpenCV_LIBS}")
message(STATUS "    include path: ${OpenCV_INCLUDE_DIRS}")

link_directories("${PROJ_DIR}/lib/64")
include_directories("${PROJ_DIR}/include" "/usr/include/X11" "/usr/include")
link_libraries("${PROJ_DIR}/lib/64/libMvCameraControl.so")
add_compile_options(-std=c++11)
add_executable(${PROJECT_NAME1} main.cpp)
add_library(camera_class SHARED camera_class.cpp mycamera.cpp)
# add_library(camera_class SHARED mycamera.cpp)
#target_link_libraries(${PROJECT_NAME1} PUBLIC )

# Link your application with OpenCV libraries
target_link_libraries(${PROJECT_NAME1} ${OpenCV_LIBS} )
target_link_libraries(${PROJECT_NAME1}  -lX11)
target_link_libraries(${PROJECT_NAME1} libMvCameraControl.so)
target_link_libraries(${PROJECT_NAME1} camera_class)
