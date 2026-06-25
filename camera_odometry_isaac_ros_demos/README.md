# camera_odometry_isaac_ros_demos

Host-native Isaac ROS camera odometry demos.

## ZED2i VIO Odometry

Run from a sourced ROS 2 environment:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch camera_odometry_isaac_ros_demos zed2i_visual_slam.launch.py
```

The launch file starts the ZED2i wrapper and Isaac ROS Visual SLAM in one
component container with:

```text
grab_resolution:=VGA
pub_frame_rate:=30.0
tracking_mode:=1
enable_localization_n_mapping:=False
publish_map_to_odom_tf:=False
publish_odom_to_base_tf:=True
base_frame:=zed2i_camera_center
camera_optical_frames:=['zed2i_left_camera_frame_optical', 'zed2i_right_camera_frame_optical']
imu_frame:=zed2i_imu_link
imu_topic:=zed_node/imu/data
```

The interface specs use `672x376`, matching the ZED2i VGA output. Isaac ROS
image converter memory pools must match the actual incoming image size.

The default mode is VIO odometry-only: it fuses stereo images and the ZED2i IMU,
does not build a SLAM map, and publishes the pose to
`/visual_slam/tracking/odometry`. In RViz, use `odom` as the fixed frame.

## Drift checks

The VGA default is for stable 30 Hz processing. If drift is too high, first check
that the scene has enough texture and that the robot body, hands, or cables are
not covering a large part of either image. ZED SDK warnings such as
`low texture or occlusion` mean tracking accuracy can be poor regardless of ROS
settings.

For a ground robot, try planar odometry and mask any fixed foreground at the
bottom of the image:

```bash
ros2 launch camera_odometry_isaac_ros_demos zed2i_visual_slam.launch.py \
  enable_ground_constraint_in_odometry:=True \
  img_mask_bottom:=30
```

For more visual features, try HD720. It uses more compute, so confirm image rate
and jitter after switching:

```bash
ros2 launch camera_odometry_isaac_ros_demos zed2i_visual_slam.launch.py \
  grab_resolution:=HD720 \
  interface_specs_file:=$(ros2 pkg prefix camera_odometry_isaac_ros_demos)/share/camera_odometry_isaac_ros_demos/config/zed2i_hd720_visual_slam_interface_specs.json
```

If accumulated odometry drift is the main problem and map corrections are
acceptable, enable localization and mapping:

```bash
ros2 launch camera_odometry_isaac_ros_demos zed2i_visual_slam.launch.py \
  enable_localization_n_mapping:=True \
  publish_map_to_odom_tf:=True
```
