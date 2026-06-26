# isaac_ros_vslam_demos

Host-native Isaac ROS camera odometry demos.

## ZED2i Stereo Odometry

Run from a sourced ROS 2 environment:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch isaac_ros_vslam_demos zed2i_visual_slam.launch.py
```

The launch file starts the ZED2i wrapper and Isaac ROS Visual SLAM in one
component container. Launch arguments:

```text
interface_specs_file:=<package config>/zed2i_visual_slam_interface_specs.json
grab_resolution:=VGA
grab_frame_rate:=30
pub_frame_rate:=30.0
image_jitter_threshold_ms:=34.0
sync_matching_threshold_ms:=5.0
```

Fixed internal settings:

```text
tracking_mode:=0
publish_imu:=False
publish_imu_tf:=False
enable_localization_n_mapping:=False
publish_map_to_odom_tf:=False
publish_odom_to_base_tf:=True
base_frame:=zed2i_camera_center
camera_optical_frames:=['zed2i_left_camera_frame_optical', 'zed2i_right_camera_frame_optical']
```

The interface specs use `672x376`, matching the ZED2i VGA output. Isaac ROS
image converter memory pools must match the actual incoming image size.

The default mode is stereo visual odometry-only. It does not fuse the ZED2i IMU,
does not build a SLAM map, and publishes the pose to
`/visual_slam/tracking/odometry`. In RViz, use `odom` as the fixed frame.

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
ros2 launch isaac_ros_vslam_demos zed2i_visual_slam.launch.py \
  grab_resolution:=HD720 \
  interface_specs_file:=$(ros2 pkg prefix isaac_ros_vslam_demos)/share/isaac_ros_vslam_demos/config/zed2i_hd720_visual_slam_interface_specs.json
```

## RealSense D405 RGB-D Odometry

The D405 launch uses Isaac ROS Visual SLAM RGB-D mode. It subscribes to color
and aligned depth from `realsense2_camera`; no IMU is used.

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch isaac_ros_vslam_demos realsense_d405_visual_slam.launch.py
```

Launch arguments:

```text
depth_profile:=640,360,60
color_profile:=640,360,60
emitter_enabled:=1
image_jitter_threshold_ms:=20.0
sync_matching_threshold_ms:=10.0
```

Fixed internal settings:

```text
device_type:=d405
tracking_mode:=2
depth_scale_factor:=1000.0
enable_localization_n_mapping:=False
publish_map_to_odom_tf:=False
publish_odom_to_base_tf:=True
```

Check the input and odometry rates:

```bash
ros2 topic hz /camera/color/image_raw --window 100
ros2 topic hz /camera/aligned_depth_to_color/image_raw --window 100
ros2 topic hz /visual_slam/tracking/odometry --window 100
```

If Visual SLAM reports a frame delta near `100 ms`, the camera stream is only
arriving at about 10 Hz. Check the actual rates and lower resolution, fix USB
bandwidth, or intentionally relax `image_jitter_threshold_ms` only for slow
debug runs:

```bash
ros2 launch isaac_ros_vslam_demos realsense_d405_visual_slam.launch.py \
  depth_profile:=424,240,30 \
  color_profile:=424,240,30
```

## RealSense D555 RGB-D Odometry

The D555 launch also uses Isaac ROS Visual SLAM RGB-D mode through
`realsense2_camera`, with the device type pinned to `d555`.

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch isaac_ros_vslam_demos realsense_d555_visual_slam.launch.py
```

Launch arguments:

```text
depth_profile:=640,360,30
color_profile:=640,360,30
emitter_enabled:=1
image_jitter_threshold_ms:=34.0
sync_matching_threshold_ms:=10.0
```

Fixed internal settings:

```text
device_type:=d555
tracking_mode:=2
depth_scale_factor:=1000.0
enable_localization_n_mapping:=False
publish_map_to_odom_tf:=False
publish_odom_to_base_tf:=True
```

Check the D555 input and odometry rates the same way:

```bash
ros2 topic hz /camera/color/image_raw --window 100
ros2 topic hz /camera/aligned_depth_to_color/image_raw --window 100
ros2 topic hz /visual_slam/tracking/odometry --window 100
```
