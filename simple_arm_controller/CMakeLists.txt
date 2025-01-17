cmake_minimum_required(VERSION 3.5.0)
project(simple_arm_control)

# Default to C11
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 11)
endif()
# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(NOT WIN32)
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_BUILD_TYPE Debug)

find_package(ament_cmake REQUIRED)
find_package(control_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(std_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(sim_action_server REQUIRED)
find_package(ignition-transport9 REQUIRED)
find_package(gazebo_msgs REQUIRED)
install(DIRECTORY
  DESTINATION share/${PROJECT_NAME}/
)
include_directories(include)

add_executable(moveit_controller src/moveit_controller.cpp include/moveit.hpp)
ament_target_dependencies(moveit_controller
  rclcpp
  rclcpp_action
  control_msgs
  moveit_ros_planning_interface
  sim_action_server
  gazebo_msgs
)
add_executable(throw_moveit src/throw_moveit.cpp include/moveit.hpp)
ament_target_dependencies(throw_moveit
  rclcpp
  rclcpp_action
  control_msgs
  moveit_ros_planning_interface
  sim_action_server
  gazebo_msgs
)
add_executable(throw_ign src/throw_ign.cpp include/moveit.hpp)
ament_target_dependencies(throw_ign
  rclcpp
  rclcpp_action
  control_msgs
  moveit_ros_planning_interface
  sim_action_server
  gazebo_msgs
)
add_executable(moveit_ign src/moveit_ign.cpp include/moveit.hpp)
ament_target_dependencies(moveit_ign
  rclcpp
  rclcpp_action
  control_msgs
  moveit_ros_planning_interface
  sim_action_server
  gazebo_msgs
)
add_executable(moveit_collision src/moveit_collision.cpp include/moveit.hpp)
ament_target_dependencies(moveit_collision
  rclcpp
  rclcpp_action
  control_msgs
  moveit_ros_planning_interface
  sim_action_server
  gazebo_msgs
)
add_executable(vr_controller src/vr_controller.cpp)
ament_target_dependencies(vr_controller
  rclcpp
  rclcpp_action
  control_msgs
  moveit_ros_planning_interface
  sim_action_server
)
add_executable(republisher src/republisher.cpp)
ament_target_dependencies(republisher
  rclcpp 
  std_msgs
  sensor_msgs
  control_msgs
  ignition-transport9
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(ament_lint_auto REQUIRED)

  ament_lint_auto_find_test_dependencies()
endif()

## Install
install(TARGETS moveit_controller throw_ign vr_controller moveit_collision throw_moveit republisher moveit_ign
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include
  DESTINATION include/${PROJECT_NAME}/)
  

ament_package()
