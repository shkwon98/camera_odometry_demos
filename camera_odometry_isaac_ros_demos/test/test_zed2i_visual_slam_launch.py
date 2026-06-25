import importlib.util
import json
from pathlib import Path

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load_launch(path: Path):
    spec = importlib.util.spec_from_file_location(path.name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.generate_launch_description()


def test_package_metadata_installs_launch_and_config_files():
    package_xml = (PACKAGE_ROOT / "package.xml").read_text()
    cmake_lists = (PACKAGE_ROOT / "CMakeLists.txt").read_text()

    assert "<name>camera_odometry_isaac_ros_demos</name>" in package_xml
    for dependency in (
        "isaac_ros_image_proc",
        "isaac_ros_visual_slam",
        "launch",
        "launch_ros",
        "rclcpp_components",
        "zed_components",
        "zed_description",
        "zed_wrapper",
    ):
        assert f"<exec_depend>{dependency}</exec_depend>" in package_xml

    assert "install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})" in cmake_lists


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


def test_zed2i_visual_slam_launch_builds_vga_vio_odometry_graph():
    launch_file = PACKAGE_ROOT / "launch" / "zed2i_visual_slam.launch.py"
    launch_text = launch_file.read_text()
    entities = _load_launch(launch_file).entities

    argument_names = [
        entity.name
        for entity in entities
        if isinstance(entity, DeclareLaunchArgument)
    ]

    assert argument_names[:5] == [
        "interface_specs_file",
        "pub_frame_rate",
        "grab_frame_rate",
        "grab_resolution",
        "base_frame",
    ]
    assert "camera_optical_frames" in argument_names
    assert "tracking_mode" in argument_names
    assert "imu_frame" in argument_names
    assert "imu_topic" in argument_names
    assert "imu_pub_rate" in argument_names
    assert "enable_localization_n_mapping" in argument_names
    assert "publish_map_to_odom_tf" in argument_names
    assert "publish_odom_to_base_tf" in argument_names
    assert "enable_ground_constraint_in_odometry" in argument_names
    assert "enable_ground_constraint_in_slam" in argument_names
    assert "img_mask_top" in argument_names
    assert "img_mask_bottom" in argument_names
    assert "img_mask_left" in argument_names
    assert "img_mask_right" in argument_names
    assert "sync_matching_threshold_ms" in argument_names
    assert "image_jitter_threshold_ms" in argument_names
    assert sum(isinstance(entity, IncludeLaunchDescription) for entity in entities) == 0

    for expected_text in (
        "zed_components",
        "stereolabs::ZedCamera",
        "nvidia::isaac_ros::visual_slam::VisualSlamNode",
        "nvidia::isaac_ros::image_proc::ImageFormatConverterNode",
        "component_container_mt",
        '"general.grab_resolution": grab_resolution',
        '"general.pub_resolution": "NATIVE"',
        '"depth.depth_mode": "NONE"',
        '"sensors.publish_imu": True',
        '"sensors.publish_imu_tf": True',
        '"sensors.sensors_pub_rate": imu_pub_rate',
        '"tracking_mode": tracking_mode',
        '"imu_frame": imu_frame',
        '"enable_localization_n_mapping": enable_localization_n_mapping',
        '"publish_map_to_odom_tf": publish_map_to_odom_tf',
        '"publish_odom_to_base_tf": publish_odom_to_base_tf',
        '"enable_ground_constraint_in_odometry": enable_ground_constraint_in_odometry',
        '"enable_ground_constraint_in_slam": enable_ground_constraint_in_slam',
        '"img_mask_top": img_mask_top',
        '"img_mask_bottom": img_mask_bottom',
        '"img_mask_left": img_mask_left',
        '"img_mask_right": img_mask_right',
        '"sync_matching_threshold_ms": sync_matching_threshold_ms',
        '"calibration_frequency": calibration_frequency',
        '("visual_slam/imu", imu_topic)',
        "zed_left_rgb_converter",
        "vslam_left_mono_converter",
        "zed2i_visual_slam_interface_specs.json",
        'FindPackageShare("camera_odometry_isaac_ros_demos")',
        'DeclareLaunchArgument("grab_resolution", default_value="VGA")',
        'DeclareLaunchArgument("tracking_mode", default_value="1")',
        'DeclareLaunchArgument("enable_localization_n_mapping", default_value="False")',
        'DeclareLaunchArgument("publish_map_to_odom_tf", default_value="False")',
        'DeclareLaunchArgument("publish_odom_to_base_tf", default_value="True")',
        'DeclareLaunchArgument("enable_ground_constraint_in_odometry", default_value="False")',
        'DeclareLaunchArgument("enable_ground_constraint_in_slam", default_value="False")',
        'DeclareLaunchArgument("img_mask_bottom", default_value="0")',
        'DeclareLaunchArgument("sync_matching_threshold_ms", default_value="5.0")',
        'DeclareLaunchArgument("imu_frame", default_value="zed2i_imu_link")',
        'DeclareLaunchArgument("imu_topic", default_value="zed_node/imu/data")',
        "zed2i_camera_center",
        "zed2i_left_camera_frame_optical",
        "zed2i_right_camera_frame_optical",
    ):
        assert expected_text in launch_text

    for removed_text in (
        "isaac_ros_examples.launch.py",
        "zed_stereo_rect,visual_slam",
        "image_format_node_left",
        "image_format_node_right",
    ):
        assert removed_text not in launch_text
