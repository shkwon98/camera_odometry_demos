import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _package_name(package_root: Path) -> str:
    return ET.parse(package_root / "package.xml").getroot().findtext("name")


def _package_exec_depends(package_root: Path) -> set[str]:
    root = ET.parse(package_root / "package.xml").getroot()
    return {element.text for element in root.findall("exec_depend")}


def test_camera_odometry_demos_is_a_package_collection():
    assert not (REPOSITORY_ROOT / "package.xml").exists()
    assert not (REPOSITORY_ROOT / "CMakeLists.txt").exists()

    expected_packages = {
        "camera_odometry_demos": "camera_odometry_demos",
        "rtabmap_demos": "rtabmap_demos",
        "isaac_ros_vslam_demos": "isaac_ros_vslam_demos",
    }

    for directory_name, package_name in expected_packages.items():
        package_root = REPOSITORY_ROOT / directory_name
        assert package_root.is_dir()
        assert (package_root / "package.xml").is_file()
        assert (package_root / "CMakeLists.txt").is_file()
        assert _package_name(package_root) == package_name


def test_collection_package_depends_on_demo_packages():
    metapackage_root = REPOSITORY_ROOT / "camera_odometry_demos"
    package_xml = (metapackage_root / "package.xml").read_text()

    assert "Metapackage for camera odometry demo packages." in package_xml
    assert {
        "rtabmap_demos",
        "isaac_ros_vslam_demos",
    }.issubset(_package_exec_depends(metapackage_root))


def test_isaac_zed2i_visual_slam_example_is_packaged():
    package_root = REPOSITORY_ROOT / "isaac_ros_vslam_demos"
    launch_file = package_root / "launch" / "zed2i_visual_slam.launch.py"
    specs_file = package_root / "config" / "zed2i_visual_slam_interface_specs.json"

    assert launch_file.is_file()
    assert specs_file.is_file()

    launch_text = launch_file.read_text()
    for expected_text in (
        "zed_components",
        "stereolabs::ZedCamera",
        "nvidia::isaac_ros::visual_slam::VisualSlamNode",
        '"general.grab_resolution": grab_resolution',
        "zed2i_camera_center",
        "zed2i_left_camera_frame_optical",
        "zed2i_right_camera_frame_optical",
    ):
        assert expected_text in launch_text

    assert "isaac_ros_examples.launch.py" not in launch_text

    specs = json.loads(specs_file.read_text())
    assert specs["camera_model"] == "zed2i"
    assert specs["camera_resolution"] == {"width": 672, "height": 376}
