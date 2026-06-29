import importlib.util
import json
from pathlib import Path

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch_ros.actions import Node


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


def _assert_zed_launch(path: Path):
    entities = _load_launch(path).entities
    launch_text = path.read_text()

    assert "isaac_ros_vslam_templates" not in launch_text
    assert sum(isinstance(entity, IncludeLaunchDescription) for entity in entities) == 0
    assert sum(isinstance(entity, OpaqueFunction) for entity in entities) == 1
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


def test_package_metadata_installs_launch_and_config_files():
    package_xml = (PACKAGE_ROOT / "package.xml").read_text()
    cmake_lists = (PACKAGE_ROOT / "CMakeLists.txt").read_text()

    assert "<name>camera_odom_isaac_ros_examples</name>" in package_xml
    for dependency in (
        "isaac_ros_image_proc",
        "isaac_ros_visual_slam",
        "launch",
        "launch_ros",
        "rclcpp_components",
        "rviz2",
        "zed_components",
        "zed_description",
        "zed_wrapper",
    ):
        assert f"<exec_depend>{dependency}</exec_depend>" in package_xml

    assert "install(DIRECTORY config launch rviz DESTINATION share/${PROJECT_NAME})" in cmake_lists


def test_ambiguous_zed_visual_slam_alias_was_removed():
    assert not (PACKAGE_ROOT / "launch" / "zed2i_visual_slam.launch.py").exists()
    assert not (PACKAGE_ROOT / "launch" / "zed2i_vslam_rgbd_imu.launch.py").exists()
    assert not (PACKAGE_ROOT / "rviz" / "zed2i_visual_slam.rviz").exists()
    assert not (PACKAGE_ROOT / "rviz" / "zed2i_vslam_rgbd_imu.rviz").exists()


def test_zed2i_specs_select_zed2i_model_and_frames():
    specs = json.loads(
        (PACKAGE_ROOT / "config" / "zed2i_visual_slam_interface_specs.json").read_text()
    )
    hd720_specs = json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "zed2i_hd720_visual_slam_interface_specs.json"
        ).read_text()
    )

    assert specs["camera_model"] == "zed2i"
    assert specs["camera_frame"] == "zed2i_camera_center"
    assert specs["camera_resolution"] == {"width": 672, "height": 376}
    assert hd720_specs["camera_model"] == "zed2i"
    assert hd720_specs["camera_frame"] == "zed2i_camera_center"
    assert hd720_specs["camera_resolution"] == {"width": 1280, "height": 720}


def test_zed2i_stereo_launch_is_standalone():
    launch_file = PACKAGE_ROOT / "launch" / "zed2i_vslam_stereo.launch.py"
    launch_text = launch_file.read_text()

    _assert_zed_launch(launch_file)
    _assert_vslam_visualization_settings(launch_text)
    assert _argument_names(launch_file) == [
        "interface_specs_file",
        "pub_frame_rate",
        "grab_frame_rate",
        "grab_resolution",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
        "enable_slam",
        "launch_rviz",
    ]

    for expected_text in (
        "zed_components",
        "stereolabs::ZedCamera",
        "nvidia::isaac_ros::visual_slam::VisualSlamNode",
        "nvidia::isaac_ros::image_proc::ImageFormatConverterNode",
        '"depth.depth_mode": "NONE"',
        '"sensors.publish_imu": False',
        '"sensors.publish_imu_tf": False',
        '"tracking_mode": 0',
        '"enable_localization_n_mapping": enable_slam',
        '"publish_map_to_odom_tf": True',
        '"base_frame": "zed2i_camera_center"',
        '"zed2i_left_camera_frame_optical"',
        '"zed2i_right_camera_frame_optical"',
        "zed_left_rgb_converter",
        "vslam_left_mono_converter",
        '"zed2i_vslam_stereo.rviz"',
        'DeclareLaunchArgument("enable_slam", default_value="true")',
    ):
        assert expected_text in launch_text
    assert '"imu_frame":' not in launch_text
    assert '("visual_slam/imu",' not in launch_text


def test_zed2i_rgbd_launch_is_standalone():
    launch_file = PACKAGE_ROOT / "launch" / "zed2i_vslam_rgbd.launch.py"
    launch_text = launch_file.read_text()

    _assert_zed_launch(launch_file)
    _assert_vslam_visualization_settings(launch_text)
    assert _argument_names(launch_file) == [
        "interface_specs_file",
        "pub_frame_rate",
        "grab_frame_rate",
        "grab_resolution",
        "depth_mode",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
        "enable_slam",
        "launch_rviz",
    ]

    for expected_text in (
        "zed_components",
        "stereolabs::ZedCamera",
        "nvidia::isaac_ros::visual_slam::VisualSlamNode",
        "nvidia::isaac_ros::image_proc::ImageFormatConverterNode",
        '"video.publish_rgb": True',
        '"video.publish_left_right": False',
        '"depth.depth_mode": depth_mode',
        '"depth.publish_depth_map": True',
        '"sensors.publish_imu": False',
        '"sensors.publish_imu_tf": False',
        '"tracking_mode": 2',
        '"enable_localization_n_mapping": enable_slam',
        '"publish_map_to_odom_tf": True',
        '"depth_scale_factor": 1.0',
        '"num_cameras": 1',
        '"depth_camera_id": 0',
        '"base_frame": "zed2i_camera_center"',
        '"camera_optical_frames": ["zed2i_left_camera_frame_optical"]',
        "zed_rgb_converter",
        '("visual_slam/image_0", "rgb/image_rect")',
        '("visual_slam/camera_info_0", "rgb/camera_info_rect")',
        '("visual_slam/depth_0", "zed_node/depth/depth_registered")',
        '"zed2i_vslam_rgbd.rviz"',
        'DeclareLaunchArgument("enable_slam", default_value="true")',
    ):
        assert expected_text in launch_text
    assert '"imu_frame":' not in launch_text
    assert '("visual_slam/imu",' not in launch_text

    _assert_rviz_config(
        PACKAGE_ROOT / "rviz" / "zed2i_vslam_rgbd.rviz",
        (
            "/visual_slam/tracking/odometry",
            "/visual_slam/tracking/vo_path",
            "/visual_slam/tracking/slam_path",
            "/visual_slam/vis/landmarks_cloud",
            "/visual_slam/vis/loop_closure_cloud",
            "/rgb/image_rect",
            "/zed_node/depth/depth_registered",
        ),
    )


def test_zed2i_stereo_imu_launch_is_standalone():
    launch_file = PACKAGE_ROOT / "launch" / "zed2i_vslam_stereo_imu.launch.py"
    launch_text = launch_file.read_text()

    _assert_zed_launch(launch_file)
    _assert_vslam_visualization_settings(launch_text)
    assert _argument_names(launch_file) == [
        "interface_specs_file",
        "pub_frame_rate",
        "grab_frame_rate",
        "grab_resolution",
        "image_jitter_threshold_ms",
        "sync_matching_threshold_ms",
        "enable_slam",
        "launch_rviz",
    ]

    for expected_text in (
        '"sensors.publish_imu": True',
        '"sensors.publish_imu_tf": True',
        '"tracking_mode": 1',
        '"enable_localization_n_mapping": enable_slam',
        '"publish_map_to_odom_tf": True',
        '"imu_frame": "zed2i_imu_link"',
        '"gyro_noise_density": 0.000244',
        '"accel_noise_density": 0.001862',
        '("visual_slam/imu", "zed_node/imu/data")',
        '"zed2i_vslam_stereo_imu.rviz"',
        'DeclareLaunchArgument("enable_slam", default_value="true")',
    ):
        assert expected_text in launch_text

    for rviz_name in (
        "zed2i_vslam_stereo.rviz",
        "zed2i_vslam_stereo_imu.rviz",
    ):
        _assert_rviz_config(
            PACKAGE_ROOT / "rviz" / rviz_name,
            (
                "/visual_slam/tracking/odometry",
                "/visual_slam/tracking/vo_path",
                "/visual_slam/tracking/slam_path",
                "/visual_slam/vis/landmarks_cloud",
                "/visual_slam/vis/loop_closure_cloud",
                "/left/image_rect",
                "/right/image_rect",
            ),
        )
