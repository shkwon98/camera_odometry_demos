import importlib.util
import os
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
        "      Covariance:\n        Orientation:\n",
        "        Value: false\n      Shape:\n",
        "Shape:",
        "Axes Length: 0.12",
        "Axes Radius: 0.012",
        "Value: Axes",
        "Class: rviz_default_plugins/PointCloud2",
        "Class: rviz_default_plugins/Image",
        "Fixed Frame: map",
    ):
        assert expected_text in rviz_text
    assert "Shape: Axes" not in rviz_text
    for unused_topic in (
        "/visual_slam/vis/observations_cloud",
        "/visual_slam/vis/pose_graph_nodes",
        "/visual_slam/vis/pose_graph_edges",
        "/visual_slam/vis/localizer",
        "/visual_slam/vis/localizer_map_cloud",
        "/visual_slam/vis/gravity",
        "/visual_slam/vis/velocity",
        "/visual_slam/vis/slam_odometry",
    ):
        assert unused_topic not in rviz_text
    for topic in expected_topics:
        assert topic in rviz_text


def _assert_vslam_visualization_settings(launch_text: str):
    for expected_text in (
        '"enable_slam_visualization": True',
        '"enable_landmarks_view": True',
        '"enable_observations_view": False',
    ):
        assert expected_text in launch_text


def test_package_metadata_declares_d555_visual_slam_test_and_restamper():
    cmake_lists = (PACKAGE_ROOT / "CMakeLists.txt").read_text()
    package_xml = (PACKAGE_ROOT / "package.xml").read_text()

    assert "test_realsense_d555_visual_slam_launch" in cmake_lists
    assert "install(PROGRAMS" in cmake_lists
    assert "scripts/restamp_realsense_rgbd.py" in cmake_lists
    assert "scripts/restamp_realsense_stereo.py" in cmake_lists
    assert "<exec_depend>rclpy</exec_depend>" in package_xml
    assert "<exec_depend>sensor_msgs</exec_depend>" in package_xml


def test_ambiguous_d555_visual_slam_alias_was_removed():
    assert not (PACKAGE_ROOT / "launch" / "realsense_d555_visual_slam.launch.py").exists()
    assert not (PACKAGE_ROOT / "rviz" / "realsense_d555_visual_slam.rviz").exists()


def test_d555_rgbd_launch_is_standalone_and_uses_restamper():
    launch_file = PACKAGE_ROOT / "launch" / "realsense_d555_vslam_rgbd.launch.py"
    launch_text = launch_file.read_text()

    _assert_direct_realsense_launch(launch_file)
    _assert_vslam_visualization_settings(launch_text)
    assert _argument_names(launch_file) == [
        "depth_profile",
        "color_profile",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
        "enable_slam",
        "launch_rviz",
    ]

    for expected_text in (
        '"device_type": "d555"',
        '"tracking_mode": 2',
        '"depth_scale_factor": 1000.0',
        '"enable_localization_n_mapping": enable_slam',
        '"publish_map_to_odom_tf": True',
        "restamp_realsense_rgbd.py",
        '"color_image_in": "/camera/color/image_raw"',
        '"color_image_out": "/camera_odom_d555/color/image_raw"',
        '"depth_image_in": "/camera/aligned_depth_to_color/image_raw"',
        '"depth_image_out": "/camera_odom_d555/aligned_depth_to_color/image_raw"',
        '"color_info_in": "/camera/color/camera_info"',
        '"color_info_out": "/camera_odom_d555/color/camera_info"',
        '("visual_slam/image_0", "/camera_odom_d555/color/image_raw")',
        '("visual_slam/camera_info_0", "/camera_odom_d555/color/camera_info")',
        "/camera_odom_d555/aligned_depth_to_color/image_raw",
        '"realsense_d555_vslam_rgbd.rviz"',
        'DeclareLaunchArgument("enable_slam", default_value="true")',
    ):
        assert expected_text in launch_text

    _assert_rviz_config(
        PACKAGE_ROOT / "rviz" / "realsense_d555_vslam_rgbd.rviz",
        (
            "/visual_slam/tracking/odometry",
            "/visual_slam/tracking/vo_path",
            "/visual_slam/tracking/slam_path",
            "/visual_slam/vis/landmarks_cloud",
            "/visual_slam/vis/loop_closure_cloud",
            "/camera_odom_d555/color/image_raw",
            "/camera_odom_d555/aligned_depth_to_color/image_raw",
        ),
    )

    restamp_script = PACKAGE_ROOT / "scripts" / "restamp_realsense_rgbd.py"
    assert restamp_script.is_file()
    assert os.access(restamp_script, os.X_OK)
    restamp_text = restamp_script.read_text()
    for expected_text in (
        "class RestampRealSenseRgbd(Node):",
        "self.get_clock().now().to_msg()",
        "Image",
        "CameraInfo",
        "create_subscription",
        "create_publisher",
        "ReliabilityPolicy.BEST_EFFORT",
        "ReliabilityPolicy.RELIABLE",
    ):
        assert expected_text in restamp_text

    restamp_stereo_script = PACKAGE_ROOT / "scripts" / "restamp_realsense_stereo.py"
    assert restamp_stereo_script.is_file()
    assert os.access(restamp_stereo_script, os.X_OK)
    restamp_stereo_text = restamp_stereo_script.read_text()
    for expected_text in (
        "class RestampRealSenseStereo(Node):",
        "Time(nanoseconds=stamp_ns).to_msg()",
        "max(self.get_clock().now().nanoseconds, self._last_stamp_ns + 1)",
        "left_image_in",
        "right_image_in",
        "left_info_in",
        "right_info_in",
        "ReliabilityPolicy.BEST_EFFORT",
        "ReliabilityPolicy.RELIABLE",
    ):
        assert expected_text in restamp_stereo_text


def test_d555_stereo_launch_is_standalone():
    launch_file = PACKAGE_ROOT / "launch" / "realsense_d555_vslam_stereo.launch.py"
    launch_text = launch_file.read_text()

    _assert_direct_realsense_launch(launch_file)
    _assert_vslam_visualization_settings(launch_text)
    assert _argument_names(launch_file) == [
        "infra_profile",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
        "enable_slam",
        "launch_rviz",
    ]
    assert '"tracking_mode": 0' in launch_text
    assert '"enable_localization_n_mapping": enable_slam' in launch_text
    assert '"publish_map_to_odom_tf": True' in launch_text
    assert '"enable_sync": True' in launch_text
    assert '"depth_module.emitter_enabled": False' in launch_text
    assert '"enable_gyro": False' in launch_text
    assert '"enable_accel": False' in launch_text
    assert "restamp_realsense_stereo.py" in launch_text
    assert '"left_image_out": "/camera_odom_d555/infra1/image_rect_raw"' in launch_text
    assert '"right_image_out": "/camera_odom_d555/infra2/image_rect_raw"' in launch_text
    assert '("visual_slam/image_0", "/camera_odom_d555/infra1/image_rect_raw")' in launch_text
    assert '("visual_slam/camera_info_0", "/camera_odom_d555/infra1/camera_info")' in launch_text
    assert '("visual_slam/image_1", "/camera_odom_d555/infra2/image_rect_raw")' in launch_text
    assert '("visual_slam/camera_info_1", "/camera_odom_d555/infra2/camera_info")' in launch_text
    assert '("visual_slam/imu",' not in launch_text
    assert '"realsense_d555_vslam_stereo.rviz"' in launch_text
    assert 'DeclareLaunchArgument("enable_slam", default_value="true")' in launch_text


def test_d555_stereo_imu_launch_is_standalone():
    launch_file = (
        PACKAGE_ROOT / "launch" / "realsense_d555_vslam_stereo_imu.launch.py"
    )
    launch_text = launch_file.read_text()

    _assert_direct_realsense_launch(launch_file)
    _assert_vslam_visualization_settings(launch_text)
    assert _argument_names(launch_file) == [
        "infra_profile",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
        "enable_slam",
        "launch_rviz",
    ]

    for expected_text in (
        '"tracking_mode": 1',
        '"enable_localization_n_mapping": enable_slam',
        '"publish_map_to_odom_tf": True',
        '"enable_sync": True',
        '"depth_module.emitter_enabled": False',
        '"enable_gyro": True',
        '"enable_accel": True',
        '"unite_imu_method": 2',
        "restamp_realsense_stereo.py",
        '("visual_slam/image_0", "/camera_odom_d555/infra1/image_rect_raw")',
        '("visual_slam/camera_info_0", "/camera_odom_d555/infra1/camera_info")',
        '("visual_slam/image_1", "/camera_odom_d555/infra2/image_rect_raw")',
        '("visual_slam/camera_info_1", "/camera_odom_d555/infra2/camera_info")',
        '"imu_frame": "camera_gyro_optical_frame"',
        '"gyro_noise_density": 0.000244',
        '"accel_noise_density": 0.001862',
        '("visual_slam/imu", "/camera/imu")',
        '"realsense_d555_vslam_stereo_imu.rviz"',
        'DeclareLaunchArgument("enable_slam", default_value="true")',
    ):
        assert expected_text in launch_text

    for rviz_name in (
        "realsense_d555_vslam_stereo.rviz",
        "realsense_d555_vslam_stereo_imu.rviz",
    ):
        _assert_rviz_config(
            PACKAGE_ROOT / "rviz" / rviz_name,
            (
                "/visual_slam/tracking/odometry",
                "/visual_slam/tracking/vo_path",
                "/visual_slam/tracking/slam_path",
                "/visual_slam/vis/landmarks_cloud",
                "/visual_slam/vis/loop_closure_cloud",
                "/camera_odom_d555/infra1/image_rect_raw",
                "/camera_odom_d555/infra2/image_rect_raw",
            ),
        )
