cmake_minimum_required(VERSION 3.8)
project(rtabmap_demos)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_realsense_d405_rtabmap_rgbd_launch
                        test/test_realsense_d405_rtabmap_rgbd_launch.py)
  ament_add_pytest_test(test_realsense_d555_rtabmap_rgbd_launch
                        test/test_realsense_d555_rtabmap_rgbd_launch.py)
endif()

ament_package()
