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


def test_package_metadata_declares_d555_rtabmap_test():
    cmake_lists = (PACKAGE_ROOT / "CMakeLists.txt").read_text()

    assert "test_realsense_d555_rtabmap_rgbd_launch" in cmake_lists


def test_d555_rtabmap_rgbd_launch_composes_realsense_odometry_and_slam():
    launch_file = PACKAGE_ROOT / "launch" / "realsense_d555_rtabmap_rgbd.launch.py"
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
        '"device_type": "d555"',
        '"align_depth.enable": "true"',
        '"enable_sync": "true"',
        '"rgb_camera.color_profile": "640x360x30"',
        '"depth_module.depth_profile": "640x360x30"',
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
        '"initial_reset"',
        '"camera_name": camera_name',
        '"camera_namespace": camera_namespace',
        '"enable_color": "true"',
        '"enable_depth": "true"',
        '"enable_rgbd": "true"',
        'DeclareLaunchArgument("camera_name"',
        'DeclareLaunchArgument("camera_namespace"',
    ):
        assert removed_argument not in launch_text
