# Neobotix GmbH

import launch
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import ThisLaunchFileDir, LaunchConfiguration
from launch_ros.actions import Node
import os
from pathlib import Path
from launch.launch_context import LaunchContext
from launch.conditions import IfCondition
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    neo_mpo_700 = get_package_share_directory('neo_mpo_700-2')
    robot_namespace = LaunchConfiguration('robot_namespace', default='')
    imu_enable = LaunchConfiguration('imu_enable', default='False')
    context = LaunchContext()

    urdf = os.path.join(get_package_share_directory('neo_mpo_700-2'), 'robot_model/mpo_700', 'mpo_700.urdf')

    with open(urdf, 'r') as infp:  
        robot_desc = infp.read()

    phidgets_drivers_file_dir = os.path.join(get_package_share_directory('phidgets_spatial'), 'launch')

    start_robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        namespace=robot_namespace,
        parameters=[{'robot_description': robot_desc, 'frame_prefix': robot_namespace}],
		arguments=[urdf])

    # Note: imu_link needs to be manually uncommented in the URDF
    start_imu_driver = ComposableNodeContainer(
            name='phidget_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                ComposableNode(
                    package='phidgets_spatial',
                    plugin='phidgets::SpatialRosI',
                    name='phidgets_spatial'),
            ],
            output='both',
            condition=IfCondition(imu_enable),
            parameters=[{'frame_id': robot_namespace.perform(context) + "imu_link"}],
    )
	
	# Launch can be set just once, does not matter if you set it for other launch files. 
	# The arguments should certainly have different meaning if there is a bigger launch file
	# Leaving this comment here for a clarity thereof and thereforth. 
	# https://answers.ros.org/question/306935/ros2-include-a-launch-file-from-a-launch-file/

    relayboard = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(neo_mpo_700, 'configs/relayboard_v2', 'relayboard_v2.launch.py')
            ),
            launch_arguments={
                'namespace': robot_namespace
            }.items()
        )

    kinematics = IncludeLaunchDescription(
             PythonLaunchDescriptionSource(
                 os.path.join(neo_mpo_700, 'configs/kinematics', 'kinematics.launch.py')
             )
         )

    teleop = IncludeLaunchDescription(
             PythonLaunchDescriptionSource(
                 os.path.join(neo_mpo_700, 'configs/teleop', 'teleop.launch.py')
             )
         )

    laser = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(neo_mpo_700, 'configs/lidar/sick/s300', 'sick_s300.launch.py')
            )
        )

    relay_topic_lidar1 = Node(
            package='topic_tools',
            executable = 'relay',
            name='relay',
			namespace =  robot_namespace,
            output='screen',
            parameters=[{'input_topic': robot_namespace.perform(context) + "lidar_1/scan_filtered",'output_topic': robot_namespace.perform(context) + "scan"}])

    relay_topic_lidar2 = Node(
            package='topic_tools',
            executable = 'relay',
            name='relay',
			namespace =  robot_namespace,
            output='screen',
            parameters=[{'input_topic': robot_namespace.perform(context) + "lidar_2/scan_filtered",'output_topic': robot_namespace.perform(context) + "scan"}])

    return LaunchDescription([relayboard,
        start_imu_driver,
        start_robot_state_publisher_cmd,
        laser,
        kinematics,
        teleop,
        relay_topic_lidar1,
        relay_topic_lidar2])