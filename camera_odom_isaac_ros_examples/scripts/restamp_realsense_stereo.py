#!/usr/bin/env python3

import copy

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo
from sensor_msgs.msg import Image


class RestampRealSenseStereo(Node):
    def __init__(self):
        super().__init__("restamp_realsense_stereo")

        input_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )
        output_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )

        self._left_info = None
        self._right_info = None
        self._last_stamp_ns = 0

        self._left_image_publisher = self.create_publisher(
            Image,
            self._topic("left_image_out", "/camera_odom_d555/infra1/image_rect_raw"),
            output_qos,
        )
        self._left_info_publisher = self.create_publisher(
            CameraInfo,
            self._topic("left_info_out", "/camera_odom_d555/infra1/camera_info"),
            output_qos,
        )
        self._right_image_publisher = self.create_publisher(
            Image,
            self._topic("right_image_out", "/camera_odom_d555/infra2/image_rect_raw"),
            output_qos,
        )
        self._right_info_publisher = self.create_publisher(
            CameraInfo,
            self._topic("right_info_out", "/camera_odom_d555/infra2/camera_info"),
            output_qos,
        )

        self.create_subscription(
            Image,
            self._topic("left_image_in", "/camera/infra1/image_rect_raw"),
            self._publish_left,
            input_qos,
        )
        self.create_subscription(
            CameraInfo,
            self._topic("left_info_in", "/camera/infra1/camera_info"),
            self._store_left_info,
            input_qos,
        )
        self.create_subscription(
            Image,
            self._topic("right_image_in", "/camera/infra2/image_rect_raw"),
            self._publish_right,
            input_qos,
        )
        self.create_subscription(
            CameraInfo,
            self._topic("right_info_in", "/camera/infra2/camera_info"),
            self._store_right_info,
            input_qos,
        )

    def _topic(self, name, default_value):
        self.declare_parameter(name, default_value)
        return self.get_parameter(name).value

    def _next_stamp(self):
        stamp_ns = max(self.get_clock().now().nanoseconds, self._last_stamp_ns + 1)
        self._last_stamp_ns = stamp_ns
        return Time(nanoseconds=stamp_ns).to_msg()

    def _store_left_info(self, message):
        self._left_info = message

    def _store_right_info(self, message):
        self._right_info = message

    def _publish_left(self, image):
        if self._left_info is None:
            return
        stamp = self._next_stamp()
        image_out = copy.deepcopy(image)
        info_out = copy.deepcopy(self._left_info)
        image_out.header.stamp = stamp
        info_out.header.stamp = stamp
        self._left_image_publisher.publish(image_out)
        self._left_info_publisher.publish(info_out)

    def _publish_right(self, image):
        if self._right_info is None:
            return
        stamp = self._next_stamp()
        image_out = copy.deepcopy(image)
        info_out = copy.deepcopy(self._right_info)
        image_out.header.stamp = stamp
        info_out.header.stamp = stamp
        self._right_image_publisher.publish(image_out)
        self._right_info_publisher.publish(info_out)


def main():
    rclpy.init()
    node = RestampRealSenseStereo()

    cleaned_up = False

    def cleanup():
        nonlocal cleaned_up
        if cleaned_up:
            return
        cleaned_up = True
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
