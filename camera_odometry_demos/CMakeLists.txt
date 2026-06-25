cmake_minimum_required(VERSION 3.8)
project(camera_odometry_demos)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_package_collection_layout
                        test/test_package_collection_layout.py)
endif()

ament_package()
