# camera_odom_isaac_ros_examples

Host-native Isaac ROS camera odometry demos.

## Supported launch groups

These examples follow the input modes used by the local Isaac ROS Visual SLAM
launch files:

```text
RGB-D:
  realsense_d405_vslam_rgbd.launch.py
  realsense_d555_vslam_rgbd.launch.py
  zed2i_vslam_rgbd.launch.py

Stereo:
  realsense_d405_vslam_stereo.launch.py
  realsense_d555_vslam_stereo.launch.py
  zed2i_vslam_stereo.launch.py

Stereo + IMU:
  realsense_d555_vslam_stereo_imu.launch.py
  zed2i_vslam_stereo_imu.launch.py
```

The older `realsense_d405_visual_slam.launch.py`,
`realsense_d555_visual_slam.launch.py`, and `zed2i_visual_slam.launch.py` names
were removed because they overlap with the explicit RGB-D or stereo launch
files.

Single RGB, RGB + IMU, and RGB-D + IMU launch groups are intentionally not
provided here because the installed Isaac ROS examples expose RGB-D mode
(`tracking_mode:=2`) and stereo/VIO modes (`tracking_mode:=0/1`), not those
single-RGB combinations.

## ZED2i Odometry

Run from a sourced ROS 2 environment:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch camera_odom_isaac_ros_examples zed2i_vslam_rgbd.launch.py
ros2 launch camera_odom_isaac_ros_examples zed2i_vslam_stereo.launch.py
```

To fuse the ZED2i IMU:

```bash
ros2 launch camera_odom_isaac_ros_examples zed2i_vslam_stereo_imu.launch.py
```

The launch files start the ZED2i wrapper and Isaac ROS Visual SLAM in one
component container. Common launch arguments:

```text
interface_specs_file:=<package config>/zed2i_visual_slam_interface_specs.json
grab_resolution:=VGA
grab_frame_rate:=30
pub_frame_rate:=30.0
image_jitter_threshold_ms:=34.0
sync_matching_threshold_ms:=5.0
enable_slam:=true
```

The RGB-D launch also accepts:

```text
depth_mode:=NEURAL
```

Fixed internal settings for the stereo launch:

```text
tracking_mode:=0
publish_imu:=False
publish_imu_tf:=False
publish_map_to_odom_tf:=True
publish_odom_to_base_tf:=True
base_frame:=zed2i_camera_center
camera_optical_frames:=['zed2i_left_camera_frame_optical', 'zed2i_right_camera_frame_optical']
```

The interface specs use `672x376`, matching the ZED2i VGA output. Isaac ROS
image converter memory pools must match the actual incoming image size.

The RGB-D and stereo launches do not fuse the ZED2i IMU. They publish
`map -> odom` and use `map` as the RViz fixed frame by default. Set
`enable_slam:=false` when comparing pure odometry drift.
`zed2i_vslam_rgbd_imu.launch.py` is intentionally not provided; use
`zed2i_vslam_stereo_imu.launch.py` for ZED2i IMU fusion.

## Drift checks

The VGA default is for stable 30 Hz processing. If drift is too high, first check
that the scene has enough texture and that the robot body, hands, or cables are
not covering a large part of either image. ZED SDK warnings such as
`low texture or occlusion` mean tracking accuracy can be poor regardless of ROS
settings.

For 3D motion, ground constraints are fixed off in this demo.

For more visual features, try HD720. It uses more compute, so confirm image rate
and jitter after switching:

```bash
ros2 launch camera_odom_isaac_ros_examples zed2i_vslam_stereo.launch.py \
  grab_resolution:=HD720 \
  interface_specs_file:=$(ros2 pkg prefix camera_odom_isaac_ros_examples)/share/camera_odom_isaac_ros_examples/config/zed2i_hd720_visual_slam_interface_specs.json
```

## RealSense D405 RGB-D Odometry

The D405 launch uses Isaac ROS Visual SLAM RGB-D mode. It subscribes to color
and aligned depth from `realsense2_camera`; no IMU is used.

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch camera_odom_isaac_ros_examples realsense_d405_vslam_rgbd.launch.py
```

The D405 stereo-only mode uses the left/right infrared streams:

```bash
ros2 launch camera_odom_isaac_ros_examples realsense_d405_vslam_stereo.launch.py
```

Launch arguments:

```text
depth_profile:=480,270,30
color_profile:=480,270,30
emitter_enabled:=1
image_jitter_threshold_ms:=34.0
sync_matching_threshold_ms:=10.0
enable_slam:=true
```

Fixed internal settings:

```text
device_type:=d405
tracking_mode:=2
depth_scale_factor:=1000.0
publish_map_to_odom_tf:=True
publish_odom_to_base_tf:=True
```

Map-based localization/mapping is enabled by default for these launch files:

```bash
ros2 launch camera_odom_isaac_ros_examples realsense_d405_vslam_rgbd.launch.py \
  enable_slam:=true
```

This turns on Isaac ROS Visual SLAM localization/mapping. The launch always
publishes `map -> odom`, and the RViz config uses `map` as the fixed frame. Set
`enable_slam:=false` when comparing pure odometry drift.

Check the input and odometry rates:

```bash
ros2 topic hz /camera/color/image_raw --window 100
ros2 topic hz /camera/aligned_depth_to_color/image_raw --window 100
ros2 topic hz /visual_slam/tracking/odometry --window 100
```

If Visual SLAM reports a frame delta near `100 ms`, the camera stream is only
arriving at about 10 Hz. Check the actual rates and USB bandwidth, or
intentionally relax `image_jitter_threshold_ms` only for slow debug runs. If the
RealSense node reports `overflow video frame detected`, the depth stream is
being published with corrupted frames. Keep the D405 RGB-D launch at the default
`480,270,30` profiles, then try disabling the projector or moving the camera to
a direct USB 3 port:

```bash
ros2 launch camera_odom_isaac_ros_examples realsense_d405_vslam_rgbd.launch.py \
  emitter_enabled:=0
```

Avoid `depth_profile:=424,240,30` with `align_depth.enable:=True` on this setup;
it has been observed to abort `realsense2_camera_node` during startup.

## RealSense D555 RGB-D Odometry

The D555 launch also uses Isaac ROS Visual SLAM RGB-D mode through
`realsense2_camera`, with the device type pinned to `d555`.

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch camera_odom_isaac_ros_examples realsense_d555_vslam_rgbd.launch.py
```

D555 stereo-only and stereo + IMU modes use the infrared streams:

```bash
ros2 launch camera_odom_isaac_ros_examples realsense_d555_vslam_stereo.launch.py
ros2 launch camera_odom_isaac_ros_examples realsense_d555_vslam_stereo_imu.launch.py
```

The D555 stereo launch files restamp the infrared image and camera info topics
before Visual SLAM. This avoids D555 hardware timestamp ordering issues such as
`Frame timestamps must be strictly increasing`.

Launch arguments:

```text
depth_profile:=640,360,30
color_profile:=640,360,30
image_jitter_threshold_ms:=34.0
sync_matching_threshold_ms:=10.0
enable_slam:=true
```

Fixed internal settings:

```text
device_type:=d555
tracking_mode:=2
depth_scale_factor:=1000.0
publish_map_to_odom_tf:=True
publish_odom_to_base_tf:=True
```

Check the D555 input and odometry rates the same way:

```bash
ros2 topic hz /camera/color/image_raw --window 100
ros2 topic hz /camera/aligned_depth_to_color/image_raw --window 100
ros2 topic hz /visual_slam/tracking/odometry --window 100
```
