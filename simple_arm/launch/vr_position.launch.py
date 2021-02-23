import os
import yaml
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, 'r') as file:
            return file.read()
    except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
        return None

def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, 'r') as file:
            return yaml.safe_load(file)
    except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
        return None


def generate_launch_description():
    # Get URDF and SRDF
    robot_description_config = load_file(
        'moveit_resources_panda_description', 'urdf/panda.urdf')
    robot_description = {'robot_description': robot_description_config}

    robot_description_semantic_config = load_file(
        'moveit_resources_panda_moveit_config', 'config/panda.srdf')
    robot_description_semantic = {
        'robot_description_semantic': robot_description_semantic_config}

    kinematics_yaml = load_yaml(
        'moveit_resources_panda_moveit_config', 'config/kinematics.yaml')

    # Get parameters for the Pose Tracking node
    pose_tracking_yaml = load_yaml('ur_configs', 'configs/pose_tracking_settings.yaml')
    pose_tracking_params = { 'moveit_servo' : pose_tracking_yaml }

    # Get parameters for the Servo node
    servo_yaml = load_yaml('ur_configs', 'configs/panda_simulated_config_pose_tracking.yaml')
    servo_params = { 'moveit_servo' : servo_yaml }
    
    pose_tracking_node = Node(
        package='simple_arm_control',
        executable='vr_controller',
        #prefix=['xterm -e gdb -ex run --args'],
        output='screen',
        parameters=[robot_description, robot_description_semantic, kinematics_yaml, pose_tracking_params, servo_params]
    )

    return LaunchDescription([pose_tracking_node])
