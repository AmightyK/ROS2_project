#!/usr/bin/env python3

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from rclpy.parameter import Parameter
import random
import time
import json
import math
import sys
import itertools
import threading

# ==========================================
# 1. CẤU HÌNH TỌA ĐỘ CÁC PHÒNG
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

# ==========================================
# 2. TẢI MA TRẬN KHOẢNG CÁCH (TĨNH)
# ==========================================
matrix_file = 'distance_matrix.json'
try:
    with open(matrix_file, 'r', encoding='utf-8') as f:
        DISTANCE_MATRIX = json.load(f)
except FileNotFoundError:
    print(f"\n[LỖI] Không tìm thấy file {matrix_file}!")
    sys.exit()

START_TO_ROOM_DISTANCES = {}

# ==========================================
# 3. MENU VÀ HELPER FUNCTIONS
# ==========================================
def get_user_selection():
    room_names = list(ROOMS.keys())
    print("\n" + "="*50)
    print(" 🏥 HỆ THỐNG ĐIỀU HƯỚNG TỰ ĐỘNG - CÓ RE-PLANNING")
    print("="*50)
    print("  [0] 🛑 KẾT THÚC CA LÀM VIỆC (THOÁT)")
    for i, name in enumerate(room_names):
        print(f"  [{i + 1}] {name}")
    print("-" * 50)
    
    while True:
        user_input = input("👉 Nhập các phòng cần đi (VD: 1 3 4) hoặc '0': ")
        if user_input.strip() == '0':
            return None
        try:
            selected_indices = [int(x) - 1 for x in user_input.split()]
            selected_rooms = []
            valid = True
            for idx in selected_indices:
                if 0 <= idx < len(room_names):
                    selected_rooms.append(room_names[idx])
                else:
                    print(f"⚠️ Số {idx + 1} không tồn tại!")
                    valid = False; break
            
            if valid and len(selected_rooms) > 0:
                return list(dict.fromkeys(selected_rooms))
        except ValueError:
            print("⚠️ Định dạng không hợp lệ!")

# def get_robot_pose(tf_buffer, max_retries=5):
#     """Quét tọa độ robot chủ động (Ưu tiên base_link)"""
#     for i in range(max_retries):
#         try:
#             trans = tf_buffer.lookup_transform(
#                 'map', 'base_link', rclpy.time.Time(),
#                 timeout=rclpy.duration.Duration(seconds=1.0)
#             )
#             return trans.transform.translation.x, trans.transform.translation.y
#         except Exception:
#             try:
#                 trans = tf_buffer.lookup_transform(
#                     'map', 'base_footprint', rclpy.time.Time(),
#                     timeout=rclpy.duration.Duration(seconds=1.0)
#                 )
#                 return trans.transform.translation.x, trans.transform.translation.y
#             except Exception as e:
#                 print(f"[Debug TF] Lần thử {i+1} đang chờ cây TF đồng bộ: {e}")
                
#     print("⚠️ Không đọc được TF sau nhiều lần thử. Mặc định lấy [0.0, 0.0].")
#     return 0.0, 0.0

def get_robot_pose(tf_buffer, max_retries=5):
    """Quét tọa độ robot chủ động (Ưu tiên base_link)"""
    for i in range(max_retries):
        try:
            # Dùng rclpy.time.Time() (giá trị mặc định = 0) để lấy Transform mới nhất trong buffer
            trans = tf_buffer.lookup_transform(
                'map', 'base_link', rclpy.time.Time()
            )
            return trans.transform.translation.x, trans.transform.translation.y
        except Exception:
            try:
                trans = tf_buffer.lookup_transform(
                    'map', 'base_footprint', rclpy.time.Time()
                )
                return trans.transform.translation.x, trans.transform.translation.y
            except Exception as e:
                print(f"[Debug TF] Lần thử {i+1} đang chờ cây TF đồng bộ...")
                time.sleep(0.5) # Cần có sleep để nhường CPU cho luồng TF chạy
                
    print("⚠️ Không đọc được TF sau nhiều lần thử. Mặc định lấy [0.0, 0.0].")
    return 0.0, 0.0

def get_path_length(nav, start_x, start_y, goal_x, goal_y):
    start = PoseStamped()
    start.header.frame_id = 'map'
    start.pose.position.x = float(start_x)
    start.pose.position.y = float(start_y)
    
    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.pose.position.x = float(goal_x)
    goal.pose.position.y = float(goal_y)

    path = nav.getPath(start, goal, use_start=True)
    if not path or len(path.poses) < 2:
        return float('inf') # Trả về vô cực nếu đường bị chặn hoàn toàn

    dist = 0.0
    for i in range(len(path.poses) - 1):
        p1 = path.poses[i].pose.position
        p2 = path.poses[i+1].pose.position
        dist += math.hypot(p1.x - p2.x, p1.y - p2.y)
    return dist

# ==========================================
# 4. THUẬT TOÁN DI TRUYỀN (GA)
# ==========================================
def route_distance(route):
    dist = START_TO_ROOM_DISTANCES[route[0]]
    for i in range(len(route) - 1):
        dist += DISTANCE_MATRIX[route[i]][route[i+1]]
    return dist

def create_route(selected_rooms):
    route = list(selected_rooms)
    random.shuffle(route)
    return route

def crossover(parent1, parent2):
    if len(parent1) < 2: return parent1 
    start, end = sorted([random.randint(0, len(parent1)-1) for _ in range(2)])
    child_p1 = parent1[start:end]
    
    child_p1_set = set(child_p1)
    child_p2 = [item for item in parent2 if item not in child_p1_set]
    
    return child_p2[:start] + child_p1 + child_p2[start:]

def mutate(route):
    if len(route) < 2: return
    idx1, idx2 = random.sample(range(len(route)), 2)
    route[idx1], route[idx2] = route[idx2], route[idx1]

def tournament_selection(population, k=3):
    selected = random.sample(population, k)
    return min(selected, key=lambda x: route_distance(x))

def run_genetic_algorithm(selected_rooms, pop_size=1000, generations=2000, mutation_rate=0.1, seed_route=None):
    if len(selected_rooms) < 7:
        all_permutations = list(itertools.permutations(selected_rooms))
        return min(all_permutations, key=lambda x: route_distance(x))
    
    dynamic_pop_size = pop_size + (len(selected_rooms) * 10)
    dynamic_generations = generations + (len(selected_rooms) * 20)

    population = []
    
    if seed_route is not None:
        valid_seed = [room for room in seed_route if room in selected_rooms]
        if set(valid_seed) == set(selected_rooms):
            seed_count = max(1, dynamic_pop_size // 10)
            population.append(valid_seed) 
            for _ in range(seed_count - 1):
                mutated_seed = valid_seed.copy()
                mutate(mutated_seed) 
                population.append(mutated_seed)

    while len(population) < dynamic_pop_size:
        population.append(create_route(selected_rooms))
    
    best_distance = float('inf')
    no_improve_count = 0

    for _ in range(dynamic_generations):
        population = sorted(population, key=lambda x: route_distance(x))
        
        current_best_dist = route_distance(population[0])
        if current_best_dist < best_distance:
            best_distance = current_best_dist
            no_improve_count = 0
        else:
            no_improve_count += 1
            
        if no_improve_count >= 150: 
            break
            
        next_generation = population[:2] 
        
        while len(next_generation) < dynamic_pop_size:
            parent1 = tournament_selection(population, k=4)
            parent2 = tournament_selection(population, k=4)
            
            child = crossover(parent1, parent2)
            if random.random() < mutation_rate:
                mutate(child)
            next_generation.append(child)
            
        population = next_generation
        
    return min(population, key=lambda x: route_distance(x))

# ==========================================
# 5. ĐIỀU KHIỂN ROBOT VỚI NAV2 (GLOBAL PLAN)
# ==========================================
def main():
    rclpy.init()
    
    # 🔥 FIX LỖI: Tạo một Node độc lập chạy trên Thread riêng để nghe TF
    tf_node = rclpy.create_node('tf_listener_dedicated')
    tf_node.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])
    tf_buffer = Buffer()
    tf_listener = TransformListener(tf_buffer, tf_node)

    # Đẩy Node này vào Executor và cho chạy ngầm (Daemon Thread)
    # Nó sẽ liên tục nhận TF bất chấp việc luồng chính bị input() chặn lại
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(tf_node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()
    
    # Khởi tạo Nav2 độc lập
    nav = BasicNavigator()
    nav.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])

    print("\n[Nav2] Đang chờ hệ thống khởi động...")
    nav.waitUntilNav2Active()

    print("[Hệ thống] Đang đồng bộ TF Tree...")
    time.sleep(1.5)
    
    while True:
        selected_rooms = get_user_selection()
        if selected_rooms is None:
            print("\n👋 Đang tắt hệ thống...")
            break
            
        pending_rooms = list(selected_rooms) 
        retry_counts = {room: 0 for room in selected_rooms} 
        previous_best_route = None

        # Vòng lặp chính xử lý lập lịch và Re-planning
        while pending_rooms:
            print("\n" + "="*50)
            print("[Hệ thống] BẮT ĐẦU TÍNH TOÁN QUỸ ĐẠO TOÀN CỤC (GLOBAL PLAN)...")
            
            # Hàm get_robot_pose bây giờ sẽ luôn đọc được vì tf_node đang chạy ngầm
            current_x, current_y = get_robot_pose(tf_buffer)
            
            START_TO_ROOM_DISTANCES.clear()
            
            # Lọc Top 5 khoảng cách chim bay để quét đường đi thực tế
            euclidean_dists = []
            for room in pending_rooms:
                rx, ry = ROOMS[room][0], ROOMS[room][1]
                edist = math.hypot(current_x - rx, current_y - ry)
                euclidean_dists.append((room, edist))
            
            euclidean_dists.sort(key=lambda x: x[1])
            top_k_rooms = [r[0] for r in euclidean_dists[:5]]

            for room, edist in euclidean_dists:
                if room in top_k_rooms:
                    dist = get_path_length(nav, current_x, current_y, ROOMS[room][0], ROOMS[room][1])
                else:
                    dist = edist * 1.5 # Phạt trọng số nặng hơn với các phòng xa
                
                START_TO_ROOM_DISTANCES[room] = dist

            # Chạy GA để ra được quỹ đạo Master
            master_route = run_genetic_algorithm(pending_rooms, seed_route=previous_best_route)
            print(f"[GA] QUỸ ĐẠO TỐI ƯU TOÀN CỤC: Tọa độ ({current_x:.1f}, {current_y:.1f}) -> {' -> '.join(master_route)}")
            print("="*50)
            
            previous_best_route = list(master_route)
            
            # Vòng lặp trượt theo quỹ đạo Master
            for target_room in master_route:
                if target_room not in pending_rooms: 
                    continue
                    
                print(f"\n🚀 Đang di chuyển đến trạm: {target_room} ...")
                target_pose = PoseStamped()
                target_pose.header.frame_id = 'map'
                target_pose.header.stamp = nav.get_clock().now().to_msg()
                target_pose.pose.position.x = float(ROOMS[target_room][0])
                target_pose.pose.position.y = float(ROOMS[target_room][1])
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
                        print(f"❌ [CẢNH BÁO MỨC CAO] {target_room} bị chặn cứng 2 lần. Hủy bỏ nhiệm vụ tại phòng này!")
                        pending_rooms.remove(target_room)
                    else:
                        print(f"⚠️ [KẸT VẬT CẢN] Không thể đến {target_room} lúc này. Sẽ quay lại sau!")
                    break
                        
                elif result == TaskResult.CANCELED:
                    print("🛑 Nhiệm vụ bị hủy bởi người dùng.")
                    pending_rooms.clear()
                    break

        if not pending_rooms and selected_rooms is not None:
            print("\n" + "="*50)
            print("🎉 [HOÀN TẤT CA LÀM VIỆC] Đã xử lý xong toàn bộ danh sách phòng.")
            print("="*50 + "\n")

    # Clean up
    tf_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()