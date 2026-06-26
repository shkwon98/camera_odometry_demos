from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("realsense2_camera"),
                    "launch",
                    "rs_launch.py",
                ]
            )
        ),
        launch_arguments={
            "device_type": "d405",
            "align_depth.enable": "true",
            "enable_sync": "true",
            "rgb_camera.color_profile": "640x480x60",
            "depth_module.depth_profile": "640x480x60",
        }.items(),
    )

    rgbd_remappings = [
        ("rgb/image", "/camera/camera/color/image_raw"),
        ("depth/image", "/camera/camera/aligned_depth_to_color/image_raw"),
        ("rgb/camera_info", "/camera/camera/color/camera_info"),
        ("odom", "/odom"),
    ]

    rgbd_odometry = Node(
        package="rtabmap_odom",
        executable="rgbd_odometry",
        output="screen",
        parameters=[
            {
                "frame_id": "camera_link",
                "odom_frame_id": "odom",
                "publish_tf": True,
                "approx_sync": True,
                "subscribe_depth": True,
            }
        ],
        remappings=rgbd_remappings,
    )

    rtabmap_slam = Node(
        package="rtabmap_slam",
        executable="rtabmap",
        output="screen",
        arguments=["-d"],
        parameters=[
            {
                "frame_id": "camera_link",
                "map_frame_id": "map",
                "publish_tf": True,
                "approx_sync": True,
                "subscribe_depth": True,
                "subscribe_odom_info": True,
            }
        ],
        remappings=rgbd_remappings,
    )

    return LaunchDescription(
        [
            realsense_launch,
            rgbd_odometry,
            rtabmap_slam,
        ]
    )
