#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped

class WaypointCollector(Node):
    def __init__(self):
        super().__init__('waypoint_collector')
        # Lắng nghe topic /clicked_point từ RViz2
        self.subscription = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.listener_callback,
            10)
        self.room_count = 1
        self.waypoints_dict = {}
        
        self.get_logger().info('=========================================')
        self.get_logger().info(' Tool Thu Thập Tọa Độ Tự Động Đã Chạy!')
        self.get_logger().info(' Hãy sang RViz2, dùng công cụ "Publish Point" và click vào các phòng.')
        self.get_logger().info('=========================================')

    def listener_callback(self, msg):
        # Lấy tọa độ x, y và làm tròn 2 chữ số thập phân
        x = round(msg.point.x, 2)
        y = round(msg.point.y, 2)
        
        room_name = f'Phong_{self.room_count}'
        self.waypoints_dict[room_name] = (x, y)
        
        self.get_logger().info(f'📍 Đã bắt được {room_name}: (x: {x}, y: {y})')
        
        # Ghi đè liên tục ra file text để lưu trữ an toàn
        with open('danh_sach_phong.txt', 'w', encoding='utf-8') as f:
            f.write("# Copy đoạn này dán vào biến ROOMS trong file ga_navigator.py nhé:\n")
            f.write("ROOMS = {\n")
            for name, coords in self.waypoints_dict.items():
                f.write(f"    '{name}': {coords},\n")
            f.write("}\n")
            
        self.room_count += 1

def main(args=None):
    rclpy.init(args=args)
    waypoint_collector = WaypointCollector()
    
    try:
        rclpy.spin(waypoint_collector)
    except KeyboardInterrupt:
        waypoint_collector.get_logger().info('Đã dừng thu thập tọa độ.')
    finally:
        waypoint_collector.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()