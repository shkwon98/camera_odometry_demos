from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    infra_profile = LaunchConfiguration("infra_profile")
    image_jitter_threshold_ms = LaunchConfiguration("image_jitter_threshold_ms")
    sync_matching_threshold_ms = LaunchConfiguration("sync_matching_threshold_ms")

    realsense_camera = Node(
        name="camera",
        namespace="",
        package="realsense2_camera",
        executable="realsense2_camera_node",
        output="screen",
        parameters=[
            {
                "device_type": "d405",
                "enable_infra1": True,
                "enable_infra2": True,
                "enable_color": False,
                "enable_depth": False,
                "enable_sync": True,
                "depth_module.emitter_enabled": False,
                "depth_module.infra_profile": infra_profile,
                "depth_module.profile": infra_profile,
                "enable_gyro": False,
                "enable_accel": False,
                "gyro_fps": 200,
                "accel_fps": 200,
                "unite_imu_method": 0,
            }
        ],
    )

    visual_slam = ComposableNode(
        package="isaac_ros_visual_slam",
        plugin="nvidia::isaac_ros::visual_slam::VisualSlamNode",
        name="visual_slam_node",
        parameters=[
            {
                "tracking_mode": 0,
                "rectified_images": True,
                "image_jitter_threshold_ms": image_jitter_threshold_ms,
                "sync_matching_threshold_ms": sync_matching_threshold_ms,
                "base_frame": "camera_link",
                "camera_optical_frames": [
                    "camera_infra1_optical_frame",
                    "camera_infra2_optical_frame",
                ],
                "enable_slam_visualization": False,
                "enable_landmarks_view": False,
                "enable_observations_view": False,
                "enable_localization_n_mapping": False,
                "publish_map_to_odom_tf": False,
                "publish_odom_to_base_tf": True,
                "min_num_images": 2,
                "num_cameras": 2,
            }
        ],
        remappings=[
            ("visual_slam/image_0", "/camera/infra1/image_rect_raw"),
            ("visual_slam/camera_info_0", "/camera/infra1/camera_info"),
            ("visual_slam/image_1", "/camera/infra2/image_rect_raw"),
            ("visual_slam/camera_info_1", "/camera/infra2/camera_info"),
        ],
    )

    visual_slam_container = ComposableNodeContainer(
        package="rclcpp_components",
        executable="component_container_mt",
        name="realsense_d405_vslam_stereo_container",
        namespace="",
        composable_node_descriptions=[visual_slam],
        output="screen",
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=[
            "-d",
            PathJoinSubstitution(
                [
                    FindPackageShare("camera_odom_isaac_ros_examples"),
                    "rviz",
                    "realsense_d405_vslam_stereo.rviz",
                ]
            ),
        ],
        condition=IfCondition(LaunchConfiguration("launch_rviz")),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("infra_profile", default_value="640,360,60"),
            DeclareLaunchArgument("image_jitter_threshold_ms", default_value="19.0"),
            DeclareLaunchArgument("sync_matching_threshold_ms", default_value="5.0"),
            DeclareLaunchArgument("launch_rviz", default_value="true"),
            realsense_camera,
            visual_slam_container,
            rviz,
        ]
    )
