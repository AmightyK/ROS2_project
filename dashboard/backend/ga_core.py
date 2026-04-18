#!/usr/bin/env python3

import random
import json
import itertools
import os

# ================================
# LOAD DISTANCE MATRIX
# ================================
def load_distance_matrix(file_path="distance_matrix.json"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ================================
# FITNESS FUNCTION
# ================================
def route_distance(route, distance_matrix, start_distances=None):
    if not route:
        return float('inf')

    total = 0.0

    # Nếu có khoảng cách từ robot hiện tại → phòng đầu tiên
    if start_distances and route[0] in start_distances:
        total += start_distances[route[0]]

    # Khoảng cách giữa các phòng
    for i in range(len(route) - 1):
        a = route[i]
        b = route[i + 1]
        total += distance_matrix[a][b]

    return total

# ================================
# GA OPERATORS
# ================================
def create_route(rooms):
    route = list(rooms)
    random.shuffle(route)
    return route

def crossover(parent1, parent2):
    if len(parent1) < 2:
        return list(parent1) # Fix lỗi Tuple

    start, end = sorted(random.sample(range(len(parent1)), 2))
    segment = list(parent1)[start:end]

    child = [x for x in parent2 if x not in segment]
    return child[:start] + segment + child[start:]

def mutate(route, mutation_rate=0.1):
    if random.random() < mutation_rate and len(route) >= 2:
        i, j = random.sample(range(len(route)), 2)
        route[i], route[j] = route[j], route[i]

def tournament_selection(population, distance_matrix, start_distances, k=3):
    selected = random.sample(population, k)
    return min(
        selected,
        key=lambda r: route_distance(r, distance_matrix, start_distances)
    )

# ================================
# MAIN GA
# ================================
def run_genetic_algorithm(selected_rooms, distance_matrix=None, start_distances=None, pop_size=1000, generations=2000, mutation_rate=0.1, seed_route=None):
    if len(selected_rooms) <= 1:
        return list(selected_rooms)

    if distance_matrix is None:
        distance_matrix = load_distance_matrix()

    # Nếu ít phòng → brute force luôn cho chuẩn xác tuyệt đối
    if len(selected_rooms) < 7:
        all_routes = itertools.permutations(selected_rooms)
        best = min(
            all_routes,
            key=lambda r: route_distance(r, distance_matrix, start_distances)
        )
        return list(best)

    dynamic_pop_size = pop_size + (len(selected_rooms) * 10)
    dynamic_generations = generations + (len(selected_rooms) * 20)

    population = []
    
    # Bơm hạt giống từ quỹ đạo cũ
    if seed_route is not None:
        valid_seed = [room for room in seed_route if room in selected_rooms]
        if set(valid_seed) == set(selected_rooms):
            seed_count = max(1, dynamic_pop_size // 10)
            population.append(valid_seed) 
            for _ in range(seed_count - 1):
                mutated_seed = valid_seed.copy()
                mutate(mutated_seed, mutation_rate=0.5) 
                population.append(mutated_seed)

    while len(population) < dynamic_pop_size:
        population.append(create_route(selected_rooms))

    best_route = None
    best_distance = float('inf')
    stagnation = 0

    for gen in range(dynamic_generations):
        population = sorted(
            population,
            key=lambda r: route_distance(r, distance_matrix, start_distances)
        )

        current_best = population[0]
        current_dist = route_distance(current_best, distance_matrix, start_distances)

        if current_dist < best_distance:
            best_distance = current_dist
            best_route = list(current_best)
            stagnation = 0
        else:
            stagnation += 1

        if stagnation >= 150:
            break

        next_gen = population[:2] 

        while len(next_gen) < dynamic_pop_size:
            p1 = tournament_selection(population, distance_matrix, start_distances, k=4)
            p2 = tournament_selection(population, distance_matrix, start_distances, k=4)

            child = crossover(p1, p2)
            mutate(child, mutation_rate)
            next_gen.append(child)

        population = next_gen

    return best_route