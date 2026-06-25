cmake_minimum_required(VERSION 3.8)
project(camera_odometry_isaac_ros_demos)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_zed2i_visual_slam_launch
                        test/test_zed2i_visual_slam_launch.py)
endif()

ament_package()
