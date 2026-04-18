use std::collections::HashMap;
use tokio::net::TcpListener;
use tokio_tungstenite::accept_async;
use futures_util::{StreamExt, SinkExt};
use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Deserialize, Serialize, Debug)]
#[serde(tag = "type")]
enum FrontendMessage {
    #[serde(rename = "preview")]
    Preview { rooms: Vec<String>, mode: String },
    #[serde(rename = "execute")]
    Execute { rooms: Vec<String>, mode: String },
}

#[derive(Serialize)]
struct PreviewResponse {
    route: Vec<String>,
    distance: f64,
}

#[tokio::main]
async fn main() {
    let addr = "127.0.0.1:8080";
    let listener = TcpListener::bind(addr).await.expect("Failed to bind");
    println!("🚀 Backend Rust đang chạy tại: ws://{}", addr);

    while let Ok((stream, _)) = listener.accept().await {
        tokio::spawn(async move {
            let mut ws_stream = accept_async(stream).await.expect("Error during ws handshake");
            println!("✅ Frontend đã kết nối!");

            while let Some(msg) = ws_stream.next().await {
                if let Ok(msg) = msg {
                    if msg.is_text() {
                        let raw = msg.to_text().unwrap();
                        let parsed: Result<FrontendMessage, _> = serde_json::from_str(raw);

                        match parsed {
                            Ok(FrontendMessage::Preview { rooms, mode }) => {
                                println!("🔍 Preview: {:?} | mode: {}", rooms, mode);
                                let result = run_preview_sync(&rooms, &mode);
                                let resp = serde_json::to_string(&result).unwrap();
                                let _ = ws_stream.send(
                                    tokio_tungstenite::tungstenite::Message::Text(resp)
                                ).await;
                            }
                            Ok(FrontendMessage::Execute { rooms, mode }) => {
                                println!("🤖 Execute: {:?} | mode: {}", rooms, mode);
                                let _ = ws_stream.send(
                                    tokio_tungstenite::tungstenite::Message::Text(
                                        format!("Đang thực thi lộ trình qua {} phòng...", rooms.len())
                                    )
                                ).await;

                                let rooms_arg = rooms.join(",");
                                std::process::Command::new("python3")
                                    .arg("nav_controller.py")
                                    .arg(&rooms_arg)
                                    .arg(&mode)
                                    .spawn()
                                    .expect("Không thể khởi động nav_controller.py");
                            }
                            Err(_) => {
                                // Legacy format: { rooms, mode } -> treat as execute
                                if let Ok(req) = serde_json::from_str::<serde_json::Value>(raw) {
                                    if let (Some(rooms), Some(mode)) =
                                        (req.get("rooms"), req.get("mode"))
                                    {
                                        let rooms: Vec<String> = rooms.as_array()
                                            .map(|a| a.iter().filter_map(|v| v.as_str().map(String::from)).collect())
                                            .unwrap_or_default();
                                        let mode = mode.as_str().unwrap_or("ga").to_string();
                                        println!("🤖 (legacy) Execute: {:?} | mode: {}", rooms, mode);
                                        let rooms_arg = rooms.join(",");
                                        let _ = ws_stream.send(
                                            tokio_tungstenite::tungstenite::Message::Text(
                                                format!("Đang thực thi lộ trình qua {} phòng...", rooms.len())
                                            )
                                        ).await;
                                        std::process::Command::new("python3")
                                            .arg("../UI_inpython/nav_controller.py")
                                            .arg(&rooms_arg)
                                            .arg(&mode)
                                            .spawn()
                                            .expect("Không thể khởi động nav_controller.py");
                                    }
                                }
                            }
                        }
                    }
                }
            }
        });
    }
}

// ─────────────────────────────────────────────────────────────────
// GA Preview Logic
// ─────────────────────────────────────────────────────────────────

fn run_preview_sync(rooms: &[String], mode: &str) -> PreviewResponse {
    if rooms.is_empty() {
        return PreviewResponse { route: vec![], distance: 0.0 };
    }

    if mode == "sequential" {
        let dist = calc_sequential_distance(rooms);
        return PreviewResponse {
            route: rooms.to_vec(),
            distance: dist,
        };
    }

    // GA mode: call Python preview script
    let rooms_arg = rooms.join(",");
    let output = Command::new("python3")
        .arg("preview_ga.py")
        .arg(&rooms_arg)
        .arg(mode)
        .output();

    match output {
        Ok(out) => {
            if out.status.success() {
                let stdout = String::from_utf8_lossy(&out.stdout);
                let route_line = stdout.lines().find(|l| l.starts_with("route:"));
                let dist_line = stdout.lines().find(|l| l.starts_with("distance:"));

                let route: Vec<String> = route_line
                    .and_then(|l| l.strip_prefix("route:"))
                    .map(|l| {
                        l.trim()
                            .trim_start_matches(&['[', ']'][..])
                            .split(',')
                            .map(|s| {
                                s.trim()
                                    .trim_matches('\'')
                                    .trim()
                                    .to_string()
                            })
                            .filter(|s| !s.is_empty())
                            .collect::<Vec<_>>()
                    })
                    .unwrap_or_default();

                let distance: f64 = dist_line
                    .and_then(|l| l.strip_prefix("distance:"))
                    .and_then(|l| l.trim().parse().ok())
                    .unwrap_or(0.0);

                return PreviewResponse { route, distance };
            } else {
                eprintln!("preview_ga.py failed: {}", String::from_utf8_lossy(&out.stderr));
            }
        }
        Err(e) => {
            eprintln!("Failed to run preview_ga.py: {}", e);
        }
    }

    // Fallback: GA in Rust
    run_ga_rust(rooms)
}

// ─────────────────────────────────────────────────────────────────
// GA implemented in pure Rust (fallback)
// ─────────────────────────────────────────────────────────────────

fn route_dist(route: &[String], matrix: &HashMap<String, HashMap<String, f64>>) -> f64 {
    let mut total = 0.0;
    let n = route.len();
    for i in 0..n.saturating_sub(1) {
        let a = &route[i];
        let b = &route[i + 1];
        if let Some(a_map) = matrix.get(a) {
            if let Some(b_dist) = a_map.get(b) {
                total += *b_dist;
            }
        }
    }
    total
}

fn calc_sequential_distance(rooms: &[String]) -> f64 {
    let matrix = load_matrix();
    route_dist(rooms, &matrix)
}

fn load_matrix() -> HashMap<String, HashMap<String, f64>> {
    let path = std::path::Path::new("../UI_inpython/distance_matrix.json");
    let content = std::fs::read_to_string(path).unwrap_or_default();
    serde_json::from_str(&content).unwrap_or_default()
}

// Simple RNG (LCG) for deterministic results
struct Rng(u64);
impl Rng {
    fn new(seed: u64) -> Self { Rng(seed) }
    fn next_usize(&mut self, bound: usize) -> usize {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1);
        (self.0 >> 33) as usize % bound
    }
    fn next_f64(&mut self) -> f64 {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1);
        (self.0 >> 33) as f64 / u32::MAX as f64
    }
}

fn create_route(rng: &mut Rng, rooms: &[String]) -> Vec<String> {
    let mut r: Vec<String> = rooms.to_vec();
    for i in 0..r.len() {
        let j = rng.next_usize(r.len());
        r.swap(i, j);
    }
    r
}

fn crossover(p1: &[String], p2: &[String]) -> Vec<String> {
    if p1.len() < 2 {
        return p1.to_vec();
    }
    let len = p1.len();
    let s = rng_usize(len);
    let e = rng_usize(len);
    let (start, end) = if s < e { (s, e) } else { (e, s) };
    let seg: Vec<String> = p1[start..=end].to_vec();
    let child: Vec<String> = p2.iter().filter(|x| !seg.contains(x)).cloned().collect();
    let pos = start.min(child.len());
    let mut res = child[..pos].to_vec();
    res.extend(seg);
    res.extend(child[pos..].to_vec());
    res
}

// Thread-local RNG for non-mut helpers
fn rng_usize(bound: usize) -> usize {
    use std::time::{SystemTime, UNIX_EPOCH};
    let seed = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos() as u64;
    let mut r = Rng(seed);
    r.next_usize(bound)
}

fn mutate(route: &mut [String], rng: &mut Rng) {
    if rng.next_f64() < 0.1 && route.len() >= 2 {
        let i = rng.next_usize(route.len());
        let j = rng.next_usize(route.len());
        route.swap(i, j);
    }
}

fn tournament_selection<'a>(
    population: &'a [Vec<String>],
    matrix: &HashMap<String, HashMap<String, f64>>,
    k: usize,
    rng: &mut Rng,
) -> Vec<String> {
    let mut best: Option<(f64, &'a Vec<String>)> = None;
    for _ in 0..k {
        let idx = rng.next_usize(population.len());
        let d = route_dist(&population[idx], matrix);
        match best {
            None => best = Some((d, &population[idx])),
            Some((bd, _)) if d < bd => best = Some((d, &population[idx])),
            _ => {}
        }
    }
    best.map(|(_, r)| r.clone()).unwrap_or_else(|| population[0].clone())
}

fn run_ga_rust(rooms: &[String]) -> PreviewResponse {
    let n = rooms.len();
    if n <= 1 {
        return PreviewResponse { route: rooms.to_vec(), distance: 0.0 };
    }

    let pop_size = (1000 + n * 10).min(5000);
    let generations = (2000 + n * 20).min(8000);

    let matrix = load_matrix();
    let mut rng = Rng::new(42);

    let mut population: Vec<Vec<String>> = (0..pop_size)
        .map(|_| create_route(&mut rng, rooms))
        .collect();

    let mut best_route: Vec<String> = rooms.to_vec();
    let mut best_dist = route_dist(&best_route, &matrix);

    for _ in 0..generations {
        population.sort_by(|a, b| {
            route_dist(a, &matrix)
                .partial_cmp(&route_dist(b, &matrix))
                .unwrap()
        });

        let curr_best = &population[0];
        let curr_dist = route_dist(curr_best, &matrix);
        if curr_dist < best_dist {
            best_dist = curr_dist;
            best_route = curr_best.clone();
        }

        let mut new_pop = vec![population[0].clone(), population[1].clone()];

        while new_pop.len() < pop_size {
            let p1 = tournament_selection(&population, &matrix, 4, &mut rng);
            let p2 = tournament_selection(&population, &matrix, 4, &mut rng);
            let mut child = crossover(&p1, &p2);
            mutate(&mut child, &mut rng);
            new_pop.push(child);
        }

        population = new_pop;
    }

    PreviewResponse { route: best_route, distance: best_dist }
}
