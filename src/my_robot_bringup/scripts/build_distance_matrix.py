#!/usr/bin/env python3

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
import math
import json

# ==========================================
# 1. DÁN DANH SÁCH PHÒNG CỦA BẠN VÀO ĐÂY
# (Lấy từ file danh_sach_phong.txt mà tool trước đã tạo)
# ==========================================
ROOMS = {
    'Phong_1': (-7.05, 4.57),
    'Phong_2': (-3.69, 7.84),
    'Phong_3': (0.23, 10.08),
    'Phong_4': (5.32, 9.98),
    'Phong_5': (14.14, 8.38),
    'Phong_6': (10.55, 7.17),
    'Phong_7': (28.66, 8.23),
    'Phong_8': (24.55, 7.21),
    'Phong_9': (38.84, 1.96),
    'Phong_10': (28.89, 2.11),
    'Phong_11': (28.23, -2.6),
    'Phong_12': (22.26, 1.46),
    'Phong_13': (22.21, -1.85),
    'Phong_14': (14.05, 1.28),
    'Phong_15': (14.14, -1.29),
    'Phong_16': (-7.25, -4.58),
    'Phong_17': (-3.8, -8.04),
    'Phong_18': (0.92, -10.2),
    'Phong_19': (4.75, -10.34),
    'Phong_20': (14.18, -8.81),
    'Phong_21': (10.54, -7.17),
    'Phong_22': (28.28, -8.49),
    'Phong_23': (24.54, -7.27),
    'Phong_24': (37.24, -9.66),
}

def calculate_path_length(path):
    """Tính tổng chiều dài của một đường đi (Path) gồm nhiều điểm"""
    if not path or len(path.poses) < 2:
        return float('inf') # Trả về vô cực nếu không tìm được đường
    
    total_distance = 0.0
    for i in range(len(path.poses) - 1):
        p1 = path.poses[i].pose.position
        p2 = path.poses[i+1].pose.position
        dist = math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
        total_distance += dist
    return total_distance

def main():
    rclpy.init()
    nav = BasicNavigator()

    print("[Matrix Builder] Đang chờ hệ thống Navigation2 khởi động...")
    nav.waitUntilNav2Active()

    distance_matrix = {}
    room_names = list(ROOMS.keys())

    print(f"[Matrix Builder] Bắt đầu tính toán ma trận khoảng cách cho {len(room_names)} phòng...")

    # Khởi tạo ma trận rỗng
    for name in room_names:
        distance_matrix[name] = {}

    # Quét qua tất cả các cặp phòng
    for i in range(len(room_names)):
        for j in range(len(room_names)):
            room_A = room_names[i]
            room_B = room_names[j]

            # Khoảng cách từ một phòng đến chính nó là 0
            if i == j:
                distance_matrix[room_A][room_B] = 0.0
                continue
            
            # Để tiết kiệm thời gian, quãng đường A->B thường bằng B->A (nếu map không có đường 1 chiều)
            if j < i:
                distance_matrix[room_A][room_B] = distance_matrix[room_B][room_A]
                continue

            # Tạo Pose bắt đầu
            start_pose = PoseStamped()
            start_pose.header.frame_id = 'map'
            start_pose.pose.position.x = float(ROOMS[room_A][0])
            start_pose.pose.position.y = float(ROOMS[room_A][1])

            # Tạo Pose kết thúc
            goal_pose = PoseStamped()
            goal_pose.header.frame_id = 'map'
            goal_pose.pose.position.x = float(ROOMS[room_B][0])
            goal_pose.pose.position.y = float(ROOMS[room_B][1])

            # Yêu cầu Nav2 tìm đường (ComputePathToPose)
            path = nav.getPath(start_pose, goal_pose, use_start=True)
            
            # Tính độ dài đường đi thực tế
            length = calculate_path_length(path)
            distance_matrix[room_A][room_B] = round(length, 2)
            
            print(f" -> Quãng đường {room_A} đến {room_B}: {length:.2f} mét")

    # Lưu kết quả ra file JSON
    output_file = 'distance_matrix.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(distance_matrix, f, indent=4)

    print(f"\n[THÀNH CÔNG] Đã lưu ma trận khoảng cách vào file: {output_file}")
    rclpy.shutdown()

if __name__ == '__main__':
    main()