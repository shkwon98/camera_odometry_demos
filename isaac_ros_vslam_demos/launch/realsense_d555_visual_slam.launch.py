from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode


def _launch_setup(context, *args, **kwargs):
    depth_profile = LaunchConfiguration("depth_profile")
    color_profile = LaunchConfiguration("color_profile")
    emitter_enabled = LaunchConfiguration("emitter_enabled")
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
                "device_type": "d555",
                "align_depth.enable": True,
                "enable_sync": True,
                "depth_module.emitter_enabled": emitter_enabled,
                "depth_module.depth_profile": depth_profile,
                "rgb_camera.color_profile": color_profile,
            }
        ],
    )

    visual_slam = ComposableNode(
        package="isaac_ros_visual_slam",
        plugin="nvidia::isaac_ros::visual_slam::VisualSlamNode",
        name="visual_slam_node",
        parameters=[
            {
                "tracking_mode": 2,
                "depth_scale_factor": 1000.0,
                "rectified_images": False,
                "image_jitter_threshold_ms": image_jitter_threshold_ms,
                "sync_matching_threshold_ms": sync_matching_threshold_ms,
                "base_frame": "camera_link",
                "camera_optical_frames": ["camera_color_optical_frame"],
                "enable_slam_visualization": False,
                "enable_landmarks_view": False,
                "enable_observations_view": False,
                "enable_localization_n_mapping": False,
                "publish_map_to_odom_tf": False,
                "publish_odom_to_base_tf": True,
                "min_num_images": 1,
                "num_cameras": 1,
                "depth_camera_id": 0,
            }
        ],
        remappings=[
            ("visual_slam/image_0", "/camera/color/image_raw"),
            ("visual_slam/camera_info_0", "/camera/color/camera_info"),
            ("visual_slam/depth_0", "/camera/aligned_depth_to_color/image_raw"),
        ],
    )

    visual_slam_container = ComposableNodeContainer(
        package="rclcpp_components",
        executable="component_container_mt",
        name="realsense_d555_visual_slam_container",
        namespace="",
        composable_node_descriptions=[visual_slam],
        output="screen",
    )

    return [realsense_camera, visual_slam_container]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("depth_profile", default_value="640,360,30"),
            DeclareLaunchArgument("color_profile", default_value="640,360,30"),
            DeclareLaunchArgument("emitter_enabled", default_value="1"),
            DeclareLaunchArgument("image_jitter_threshold_ms", default_value="34.0"),
            DeclareLaunchArgument("sync_matching_threshold_ms", default_value="10.0"),
            OpaqueFunction(function=_launch_setup),
        ]
    )
