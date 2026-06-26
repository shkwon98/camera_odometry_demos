import importlib.util
from pathlib import Path

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch_ros.actions import ComposableNodeContainer, Node


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load_launch(path: Path):
    spec = importlib.util.spec_from_file_location(path.name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.generate_launch_description()


def _argument_names(path: Path) -> list[str]:
    return [
        entity.name
        for entity in _load_launch(path).entities
        if isinstance(entity, DeclareLaunchArgument)
    ]


def _assert_direct_realsense_launch(path: Path):
    entities = _load_launch(path).entities
    launch_text = path.read_text()

    assert "isaac_ros_vslam_templates" not in launch_text
    assert "IncludeLaunchDescription" not in launch_text
    assert sum(isinstance(entity, IncludeLaunchDescription) for entity in entities) == 0
    assert sum(isinstance(entity, OpaqueFunction) for entity in entities) == 0
    assert any(
        isinstance(entity, ComposableNodeContainer)
        and entity.node_package == "rclcpp_components"
        and entity.node_executable == "component_container_mt"
        for entity in entities
    )
    assert any(
        isinstance(entity, Node)
        and entity.node_package == "rviz2"
        and entity.node_executable == "rviz2"
        for entity in entities
    )


def _assert_rviz_config(path: Path, expected_topics: tuple[str, ...]):
    assert path.is_file()
    rviz_text = path.read_text()
    for expected_text in (
        "Class: rviz_default_plugins/TF",
        "Class: rviz_default_plugins/Path",
        "Class: rviz_default_plugins/Odometry",
        "Shape:",
        "Axes Length: 0.12",
        "Axes Radius: 0.012",
        "Value: Axes",
        "Class: rviz_default_plugins/PointCloud2",
        "Class: rviz_default_plugins/Image",
    ):
        assert expected_text in rviz_text
    assert "Shape: Axes" not in rviz_text
    for topic in expected_topics:
        assert topic in rviz_text


def test_package_metadata_declares_realsense_dependency_and_test():
    package_xml = (PACKAGE_ROOT / "package.xml").read_text()
    cmake_lists = (PACKAGE_ROOT / "CMakeLists.txt").read_text()

    assert "<exec_depend>realsense2_camera</exec_depend>" in package_xml
    assert "<exec_depend>rviz2</exec_depend>" in package_xml
    assert "test_realsense_d405_visual_slam_launch" in cmake_lists
    assert "install(DIRECTORY config launch rviz DESTINATION share/${PROJECT_NAME})" in cmake_lists


def test_ambiguous_d405_visual_slam_alias_was_removed():
    assert not (PACKAGE_ROOT / "launch" / "isaac_ros_vslam_templates.py").exists()
    assert not (PACKAGE_ROOT / "launch" / "realsense_d405_visual_slam.launch.py").exists()
    assert not (PACKAGE_ROOT / "rviz" / "realsense_d405_visual_slam.rviz").exists()


def test_d405_rgbd_launch_is_standalone():
    launch_file = PACKAGE_ROOT / "launch" / "realsense_d405_vslam_rgbd.launch.py"
    launch_text = launch_file.read_text()

    _assert_direct_realsense_launch(launch_file)
    assert _argument_names(launch_file) == [
        "depth_profile",
        "color_profile",
        "emitter_enabled",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
        "launch_rviz",
    ]

    for expected_text in (
        "def generate_launch_description():",
        '"device_type": "d405"',
        '"enable_infra": False',
        '"enable_infra1": False',
        '"enable_infra2": False',
        '"enable_color": True',
        '"enable_depth": True',
        '"enable_gyro": False',
        '"enable_accel": False',
        '"enable_motion": False',
        '"tracking_mode": 2',
        '"depth_scale_factor": 1000.0',
        '"align_depth.enable": True',
        '"enable_sync": True',
        '"depth_module.depth_profile": depth_profile',
        '"rgb_camera.color_profile": color_profile',
        '"depth_module.emitter_enabled": emitter_enabled',
        '"camera_optical_frames": ["camera_color_optical_frame"]',
        '("visual_slam/image_0", "/camera/color/image_raw")',
        '("visual_slam/camera_info_0", "/camera/color/camera_info")',
        '("visual_slam/depth_0", "/camera/aligned_depth_to_color/image_raw")',
        'DeclareLaunchArgument("depth_profile", default_value="640,360,30")',
        'DeclareLaunchArgument("color_profile", default_value="848,480,30")',
        'DeclareLaunchArgument("image_jitter_threshold_ms", default_value="34.0")',
        '"realsense_d405_vslam_rgbd.rviz"',
    ):
        assert expected_text in launch_text

    _assert_rviz_config(
        PACKAGE_ROOT / "rviz" / "realsense_d405_vslam_rgbd.rviz",
        (
            "/visual_slam/tracking/odometry",
            "/visual_slam/tracking/vo_path",
            "/visual_slam/tracking/slam_path",
            "/visual_slam/vis/landmarks_cloud",
            "/visual_slam/vis/observations_cloud",
            "/camera/color/image_raw",
            "/camera/aligned_depth_to_color/image_raw",
        ),
    )


def test_d405_stereo_launch_is_standalone():
    launch_file = PACKAGE_ROOT / "launch" / "realsense_d405_vslam_stereo.launch.py"
    launch_text = launch_file.read_text()

    _assert_direct_realsense_launch(launch_file)
    assert _argument_names(launch_file) == [
        "infra_profile",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
        "launch_rviz",
    ]

    for expected_text in (
        '"device_type": "d405"',
        '"enable_infra1": True',
        '"enable_infra2": True',
        '"enable_color": False',
        '"enable_depth": False',
        '"tracking_mode": 0',
        '"rectified_images": True',
        '"camera_infra1_optical_frame"',
        '"camera_infra2_optical_frame"',
        '("visual_slam/image_0", "/camera/infra1/image_rect_raw")',
        '("visual_slam/camera_info_0", "/camera/infra1/camera_info")',
        '("visual_slam/image_1", "/camera/infra2/image_rect_raw")',
        '("visual_slam/camera_info_1", "/camera/infra2/camera_info")',
        '"realsense_d405_vslam_stereo.rviz"',
    ):
        assert expected_text in launch_text
    assert '"imu_frame"' not in launch_text
    assert '("visual_slam/imu",' not in launch_text

    _assert_rviz_config(
        PACKAGE_ROOT / "rviz" / "realsense_d405_vslam_stereo.rviz",
        (
            "/visual_slam/tracking/odometry",
            "/visual_slam/tracking/vo_path",
            "/visual_slam/tracking/slam_path",
            "/visual_slam/vis/landmarks_cloud",
            "/visual_slam/vis/observations_cloud",
            "/camera/infra1/image_rect_raw",
            "/camera/infra2/image_rect_raw",
        ),
    )
