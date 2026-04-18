import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import SetEnvironmentVariable

from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('my_robot_bringup')

    urdf_file = os.path.join(pkg, 'urdf', 'omni_base.urdf')
    world_file = os.path.join(pkg, 'worlds', 'hospital_full.world')
    bridge_config = os.path.join(pkg, 'config', 'bridge_config.yaml')
    controller_config = os.path.join(pkg, 'config', 'configuration.yaml')
    model_config = os.path.join(pkg, 'models')

    # Get path to config file for EKF node
    ekf_config = os.path.join(pkg, 'config', 'ekf.yaml')

    # Read URDF
    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    # Meshes
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f"{os.path.dirname(pkg)}:{model_config}"
    )
    
    # -------------------------
    # Controller YAML passed     # to gz_ros2_control
    # -------------------------
    set_ros_args = SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_ARGS',
        value=f'--ros-args --params-file {controller_config}'
    )

    # -------------------------
    # Robot State Publisher
    # -------------------------

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'robot_description': robot_description},
            {'use_sim_time': True}
        ],
        output='screen'
    )

    # -------------------------
    # Start Gazebo
    # -------------------------

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    # -------------------------
    # Spawn robot
    # -------------------------

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'omni_base',
            '-y', '10.5',
            '-z', '0.1',
            '-Y', '-1.57'
        ],
        output='screen'
    )

    delayed_spawn = TimerAction(
        period=15.0,
        actions=[spawn_robot]
    )

    # -------------------------
    # ROS <-> Gazebo Bridge
    # Uses bridge_config.yaml
    # -------------------------

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': bridge_config},
                    {'use_sim_time': True}],
        output='screen'
    )

    delayed_bridge = TimerAction(
        period=5.0,
        actions=[bridge]
    )

    # -------------------------
    # ros2_control Controllers
    # -------------------------

    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager',
            '/controller_manager'
        ],
        output='screen'
    )

    mobile_base_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'mobile_base_controller',
            '--controller-manager',
            '/controller_manager'
        ],
        output='screen'
    )

    # imu_broadcaster = Node(
    #     package='controller_manager',
    #     executable='spawner',
    #     arguments=[
    #         'imu_sensor_broadcaster',
    #         '--controller-manager',
    #         '/controller_manager'
    #     ],
    #     output='screen'
    # )

    delayed_controllers = TimerAction(
        period=8.0,
        actions=[
            joint_state_broadcaster,
            mobile_base_controller
        ]
    )



    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config,
                    {'use_sim_time': True}
        ],
        remappings=[
            # optional (only if needed)
            # ('/odometry/filtered', '/odometry/filtered')
        ]
    )

    # -------------------------
    # Launch everything
    # -------------------------

    return LaunchDescription([
        set_gz_resource_path,
        set_ros_args,
        robot_state_publisher,
        gz_sim,
        delayed_spawn,
        delayed_bridge,
        delayed_controllers,
        # imu_broadcaster,
        ekf_node,
    ])