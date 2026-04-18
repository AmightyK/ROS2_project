

#!/usr/bin/env python3

import rclpy
from rclpy.parameter import Parameter
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

import time
import sys
import os
import math
import threading

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import Lõi GA
try:
    from ga_core import run_genetic_algorithm, load_distance_matrix
except ImportError as e:
    print(f"⚠️ Lỗi: Không tìm thấy ga_core: {e}")
    sys.exit(1)

ROOMS = {
    'Phong_1': (-7.05, 4.57), 'Phong_2': (-3.69, 7.84), 'Phong_3': (0.23, 10.08), 'Phong_4': (5.32, 9.98),
    'Phong_5': (14.14, 8.38), 'Phong_6': (10.55, 7.17), 'Phong_7': (28.66, 8.23), 'Phong_8': (24.55, 7.21),
    'Phong_9': (38.84, 1.96), 'Phong_10': (28.89, 2.11), 'Phong_11': (28.23, -2.6), 'Phong_12': (22.26, 1.46),
    'Phong_13': (22.21, -1.85), 'Phong_14': (14.05, 1.28), 'Phong_15': (14.14, -1.29), 'Phong_16': (-7.25, -4.58),
    'Phong_17': (-3.8, -8.04), 'Phong_18': (0.92, -10.2), 'Phong_19': (4.75, -10.34), 'Phong_20': (14.18, -8.81),
    'Phong_21': (10.54, -7.17), 'Phong_22': (28.28, -8.49), 'Phong_23': (24.54, -7.27), 'Phong_24': (37.24, -9.66),
}

def get_robot_pose(tf_buffer):
    print("⏳ Đang đồng bộ vị trí thực tế từ cây TF...")
    while rclpy.ok():
        try:
            trans = tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            return trans.transform.translation.x, trans.transform.translation.y, trans.transform.rotation
        except Exception:
            try:
                trans = tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
                return trans.transform.translation.x, trans.transform.translation.y, trans.transform.rotation
            except Exception:
                time.sleep(0.5)

def get_path_length(nav, start_x, start_y, goal_x, goal_y):
    start = PoseStamped()
    start.header.frame_id = 'map'
    start.pose.position.x, start.pose.position.y = float(start_x), float(start_y)
    
    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.pose.position.x, goal.pose.position.y = float(goal_x), float(goal_y)

    path = nav.getPath(start, goal, use_start=True)
    if not path or len(path.poses) < 2:
        return float('inf')

    dist = 0.0
    for i in range(len(path.poses) - 1):
        p1 = path.poses[i].pose.position
        p2 = path.poses[i+1].pose.position
        dist += math.hypot(p1.x - p2.x, p1.y - p2.y)
    return dist

def main():
    rclpy.init()

    if len(sys.argv) < 2:
        print("❌ Cần truyền tham số phòng.")
        rclpy.shutdown()
        return

    # Nhận mode từ GUI truyền sang (mặc định là ga nếu không có)
    mode = sys.argv[2] if len(sys.argv) > 2 else "ga"

    # 1. Khởi tạo Node TF
    tf_node = rclpy.create_node(
        'tf_listener_dedicated',
        parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)]
    )
    tf_buffer = Buffer()
    tf_listener = TransformListener(tf_buffer, tf_node)

    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(tf_node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()
    
    time.sleep(2.0)
    
    current_x, current_y, current_rot = get_robot_pose(tf_buffer)
    print(f"📍 Khóa vị trí thực tại: X={current_x:.2f}, Y={current_y:.2f}")

    # 3. Khởi tạo Navigation
    nav = BasicNavigator()
    nav.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])

    init_pose = PoseStamped()
    init_pose.header.frame_id = 'map'
    init_pose.header.stamp = nav.get_clock().now().to_msg()
    init_pose.pose.position.x = current_x
    init_pose.pose.position.y = current_y
    init_pose.pose.orientation = current_rot
    
    nav.setInitialPose(init_pose)
    nav.initial_pose_received = True 

    print("\n[Nav2 Controller] Đang chờ hệ thống khởi động...")
    nav.waitUntilNav2Active()

    # Nhận list phòng, duy trì đúng thứ tự click của user (Python list preserve order)
    raw_rooms = sys.argv[1].split(",")
    # Lọc phòng rác nhưng dùng list comprehension để giữ nguyên thứ tự
    pending_rooms = []
    for r in raw_rooms:
        if r in ROOMS and r not in pending_rooms:
            pending_rooms.append(r)
            
    retry_counts = {room: 0 for room in pending_rooms}
    
    try:
        distance_matrix = load_distance_matrix()
    except Exception as e:
        print(f"❌ Lỗi nạp ma trận: {e}")
        rclpy.shutdown()
        return

    previous_best_route = None

    while pending_rooms:
        print("\n" + "="*50)
        current_x, current_y, _ = get_robot_pose(tf_buffer)
        
        if mode == "ga":
            print("[Bộ Não GA] ĐANG TÍNH TOÁN QUỸ ĐẠO TOÀN CỤC MỚI...")
            START_TO_ROOM_DISTANCES = {}
            euclidean_dists = []
            for room in pending_rooms:
                rx, ry = ROOMS[room]
                edist = math.hypot(current_x - rx, current_y - ry)
                euclidean_dists.append((room, edist))
            
            euclidean_dists.sort(key=lambda x: x[1])
            top_k_rooms = [r[0] for r in euclidean_dists[:5]]

            for room, edist in euclidean_dists:
                if room in top_k_rooms:
                    START_TO_ROOM_DISTANCES[room] = get_path_length(nav, current_x, current_y, ROOMS[room][0], ROOMS[room][1])
                else:
                    START_TO_ROOM_DISTANCES[room] = edist * 1.5

            master_route = run_genetic_algorithm(
                pending_rooms, 
                distance_matrix=distance_matrix, 
                start_distances=START_TO_ROOM_DISTANCES,
                seed_route=previous_best_route
            )
            previous_best_route = list(master_route)
            
        else:
            # CHẾ ĐỘ SEQUENTIAL: Chạy thẳng danh sách đang chờ hiện tại
            print("[Bộ Não] ĐANG CHẠY CHẾ ĐỘ TUẦN TỰ (SEQUENTIAL)...")
            master_route = list(pending_rooms)
            
        print(f"[ĐÍCH ĐẾN] QUỸ ĐẠO CHỐT: ({current_x:.1f}, {current_y:.1f}) -> {' -> '.join(master_route)}")
        print("="*50)
        
        # Di chuyển theo route đã chốt
        for target_room in master_route:
            if target_room not in pending_rooms: 
                continue
                
            print(f"\n🚀 Đang di chuyển đến trạm: {target_room} ...")
            target_pose = PoseStamped()
            target_pose.header.frame_id = 'map'
            target_pose.header.stamp = nav.get_clock().now().to_msg()
            target_pose.pose.position.x, target_pose.pose.position.y = ROOMS[target_room]
            target_pose.pose.orientation.w = 1.0

            nav.goToPose(target_pose)

            i = 0
            while not nav.isTaskComplete():
                i += 1
                if i % 10 == 0:
                    print(f" ⏳ Đang tiến về {target_room}...")
                time.sleep(0.5)

            result = nav.getResult()
            
            if result == TaskResult.SUCCEEDED:
                print(f"✅ Đã đến thành công {target_room}!")
                pending_rooms.remove(target_room)
                
            elif result == TaskResult.FAILED:
                retry_counts[target_room] += 1
                if retry_counts[target_room] >= 2:
                    print(f"❌ [HỦY] {target_room} bị chặn cứng 2 lần.")
                    pending_rooms.remove(target_room)
                else:
                    print(f"⚠️ [KẸT VẬT CẢN TẠI ĐÍCH] Sẽ hủy và lập lịch lại!")
                break
                    
            elif result == TaskResult.CANCELED:
                print("🛑 Nhiệm vụ bị hủy.")
                pending_rooms.clear()
                break

    print("\n🎉 [HOÀN TẤT] Ca làm việc kết thúc!")
    tf_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()