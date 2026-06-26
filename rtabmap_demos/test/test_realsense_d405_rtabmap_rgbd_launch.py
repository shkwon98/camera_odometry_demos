import importlib.util
from pathlib import Path

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch_ros.actions import Node


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load_launch(path: Path):
    spec = importlib.util.spec_from_file_location(path.name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.generate_launch_description()


def test_package_metadata_installs_launch_files():
    package_xml = (PACKAGE_ROOT / "package.xml").read_text()
    cmake_lists = (PACKAGE_ROOT / "CMakeLists.txt").read_text()

    assert "<name>rtabmap_demos</name>" in package_xml
    assert "project(rtabmap_demos)" in cmake_lists
    for dependency in (
        "launch",
        "launch_ros",
        "realsense2_camera",
        "rtabmap_odom",
        "rtabmap_slam",
    ):
        assert f"<exec_depend>{dependency}</exec_depend>" in package_xml

    assert "install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})" in cmake_lists


def test_d405_rtabmap_rgbd_launch_composes_realsense_odometry_and_slam():
    launch_file = PACKAGE_ROOT / "launch" / "realsense_d405_rtabmap_rgbd.launch.py"
    launch_text = launch_file.read_text()
    entities = _load_launch(launch_file).entities

    argument_names = [
        entity.name
        for entity in entities
        if isinstance(entity, DeclareLaunchArgument)
    ]

    assert argument_names == []
    assert sum(isinstance(entity, IncludeLaunchDescription) for entity in entities) == 1
    assert any(
        isinstance(entity, Node)
        and entity.node_package == "rtabmap_odom"
        and entity.node_executable == "rgbd_odometry"
        for entity in entities
    )
    assert any(
        isinstance(entity, Node)
        and entity.node_package == "rtabmap_slam"
        and entity.node_executable == "rtabmap"
        for entity in entities
    )

    for realsense_argument in (
        '"device_type": "d405"',
        '"align_depth.enable": "true"',
        '"enable_sync": "true"',
        '"rgb_camera.color_profile": "640x480x60"',
        '"depth_module.depth_profile": "640x480x60"',
    ):
        assert realsense_argument in launch_text

    for remapping in (
        '("rgb/image", "/camera/camera/color/image_raw")',
        '("depth/image", "/camera/camera/aligned_depth_to_color/image_raw")',
        '("rgb/camera_info", "/camera/camera/color/camera_info")',
        '("odom", "/odom")',
    ):
        assert remapping in launch_text

    for parameter in (
        '"frame_id": "camera_link"',
        '"odom_frame_id": "odom"',
        '"map_frame_id": "map"',
        '"publish_tf": True',
        '"approx_sync": True',
        '"subscribe_depth": True',
        '"subscribe_odom_info": True',
    ):
        assert parameter in launch_text

    assert "rs_launch.py" in launch_text
    assert '"-d"' in launch_text
    for removed_argument in (
        "realsense_rtabmap_rgbd.launch.py",
        '"camera_name": camera_name',
        '"camera_namespace": camera_namespace',
        '"enable_color": "true"',
        '"enable_depth": "true"',
        '"enable_rgbd": "true"',
        'DeclareLaunchArgument("camera_name"',
        'DeclareLaunchArgument("camera_namespace"',
        "rgb_camera_profile",
        "depth_module_profile",
        "align_depth_enable",
        "depth_module.emitter_enabled",
        "depth_module_emitter_enabled",
        'LaunchConfiguration("enable_sync")',
        'LaunchConfiguration("enable_rgbd")',
        'LaunchConfiguration("depth_qos")',
        'LaunchConfiguration("color_qos")',
        'LaunchConfiguration("frame_id")',
        'LaunchConfiguration("odom_frame_id")',
        'LaunchConfiguration("map_frame_id")',
        'LaunchConfiguration("approx_sync")',
        'LaunchConfiguration("publish_tf")',
        'DeclareLaunchArgument("enable_sync"',
        'DeclareLaunchArgument("enable_rgbd"',
        'DeclareLaunchArgument("rgb_camera_profile"',
        'DeclareLaunchArgument("depth_module_profile"',
        'DeclareLaunchArgument("depth_qos"',
        'DeclareLaunchArgument("color_qos"',
        'DeclareLaunchArgument("frame_id"',
        'DeclareLaunchArgument("odom_frame_id"',
        'DeclareLaunchArgument("map_frame_id"',
        'DeclareLaunchArgument("approx_sync"',
        'DeclareLaunchArgument("publish_tf"',
    ):
        assert removed_argument not in launch_text

    assert "delete_db_on_start" not in launch_text
    assert "def rtabmap_slam_node" not in launch_text
    assert "IfCondition" not in launch_text
    assert "UnlessCondition" not in launch_text
