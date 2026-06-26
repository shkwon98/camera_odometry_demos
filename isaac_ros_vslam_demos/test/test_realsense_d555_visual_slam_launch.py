import importlib.util
from pathlib import Path

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load_launch(path: Path):
    spec = importlib.util.spec_from_file_location(path.name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.generate_launch_description()


def test_package_metadata_declares_d555_visual_slam_test():
    cmake_lists = (PACKAGE_ROOT / "CMakeLists.txt").read_text()

    assert "test_realsense_d555_visual_slam_launch" in cmake_lists


def test_realsense_d555_visual_slam_launch_builds_rgbd_graph():
    launch_file = PACKAGE_ROOT / "launch" / "realsense_d555_visual_slam.launch.py"
    launch_text = launch_file.read_text()
    entities = _load_launch(launch_file).entities

    argument_names = [
        entity.name
        for entity in entities
        if isinstance(entity, DeclareLaunchArgument)
    ]

    assert argument_names == [
        "depth_profile",
        "color_profile",
        "emitter_enabled",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
    ]

    assert sum(isinstance(entity, IncludeLaunchDescription) for entity in entities) == 0
    assert sum(isinstance(entity, OpaqueFunction) for entity in entities) == 1

    for expected_text in (
        "def _launch_setup(context, *args, **kwargs):",
        "realsense2_camera",
        "realsense2_camera_node",
        "nvidia::isaac_ros::visual_slam::VisualSlamNode",
        '"device_type": "d555"',
        '"tracking_mode": 2',
        '"depth_scale_factor": 1000.0',
        '"align_depth.enable": True',
        '"enable_sync": True',
        '"depth_module.depth_profile": depth_profile',
        '"rgb_camera.color_profile": color_profile',
        '"depth_module.emitter_enabled": emitter_enabled',
        '"base_frame": "camera_link"',
        '"camera_optical_frames": ["camera_color_optical_frame"]',
        '"enable_slam_visualization": False',
        '"enable_localization_n_mapping": False',
        '"publish_map_to_odom_tf": False',
        '"publish_odom_to_base_tf": True',
        '("visual_slam/image_0", "/camera/color/image_raw")',
        '("visual_slam/camera_info_0", "/camera/color/camera_info")',
        '("visual_slam/depth_0", "/camera/aligned_depth_to_color/image_raw")',
        'DeclareLaunchArgument("depth_profile", default_value="640,360,30")',
        'DeclareLaunchArgument("color_profile", default_value="640,360,30")',
        'DeclareLaunchArgument("emitter_enabled", default_value="1")',
        'DeclareLaunchArgument("image_jitter_threshold_ms", default_value="34.0")',
    ):
        assert expected_text in launch_text

    for removed_argument in (
        "camera_name",
        "camera_namespace",
        "device_type",
        "base_frame",
        "camera_optical_frames",
        "depth_scale_factor",
        "enable_localization_n_mapping",
        "publish_map_to_odom_tf",
        "publish_odom_to_base_tf",
        "enable_ground_constraint_in_odometry",
        "enable_ground_constraint_in_slam",
        "enable_slam_visualization",
    ):
        assert f'DeclareLaunchArgument("{removed_argument}"' not in launch_text

    for default_parameter in (
        '"enable_image_denoising": False',
        '"enable_ground_constraint_in_odometry": False',
        '"enable_ground_constraint_in_slam": False',
        '"enable_infra1": False',
        '"enable_infra2": False',
        '"enable_color": True',
        '"enable_depth": True',
        '"depth_module.enable_auto_exposure": True',
        '"rgb_camera.enable_auto_exposure": True',
        '"enable_gyro": False',
        '"enable_accel": False',
        '"decimation_filter.enable": False',
        '"spatial_filter.enable": False',
        '"temporal_filter.enable": False',
        '"hole_filling_filter.enable": False',
    ):
        assert default_parameter not in launch_text
