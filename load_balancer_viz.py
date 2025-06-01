import pygame
import random
import time
import json
import threading
import numpy as np
from collections import deque
from user import User, UserType
from load_balancer import LoadBalancer, LoadBalancingAlgorithm
from upstream_server import UpstreamServer, ServerType, ServerStatus
from report import SimulationReportGenerator
from traffic_pattern import TrafficPattern
from performance_monitor import PerformanceMonitor


class LoadBalancerVisualization:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.users = []
        self.completed_users = []
        self.last_spawn_time = 0

        self.current_traffic_pattern = TrafficPattern("steady", 2.0, 0.1, 2.0)
        self.traffic_patterns = {
            "steady": TrafficPattern("steady", 2.0, 0.1, 2.0),
            "wave": TrafficPattern("wave", 3.0, 0.05, 1.5),
            "spike": TrafficPattern("spike", 1.5, 0.2, 3.0),
            "random": TrafficPattern("random", 2.5, 0.15, 2.5),
        }

        self.performance_monitor = PerformanceMonitor()
        self.last_performance_update = time.time()

        self.server_stats = {}
        self.server_performance_history = {}
        self.server_load_distribution = {}
        self.server_failure_tracking = {}

        self.request_distribution_by_type = {
            "LIGHT": {"count": 0, "success": 0, "avg_response": 0.0},
            "STANDARD": {"count": 0, "success": 0, "avg_response": 0.0},
            "HEAVY": {"count": 0, "success": 0, "avg_response": 0.0},
            "BURST": {"count": 0, "success": 0, "avg_response": 0.0},
            "NAUGHTY": {"count": 0, "success": 0, "avg_response": 0.0},
        }

        self.algorithm_performance_history = {}
        self.algorithm_switch_times = []

        self.system_resource_history = {
            "cpu_usage": deque(maxlen=100),
            "memory_usage": deque(maxlen=100),
            "network_throughput": deque(maxlen=100),
            "request_latency": deque(maxlen=100),
        }

        self.traffic_analytics = {
            "peak_concurrent_users": 0,
            "total_throughput": 0,
            "hourly_distribution": [0] * 24,
            "pattern_efficiency": {},
            "burst_frequency": 0,
            "sustained_load_periods": [],
        }

        self.server_type_analytics = {
            ServerType.STANDARD: {
                "requests": 0,
                "success_rate": 0.0,
                "avg_response": 0.0,
                "uptime": 0.0,
            },
            ServerType.HIGH_PERFORMANCE: {
                "requests": 0,
                "success_rate": 0.0,
                "avg_response": 0.0,
                "uptime": 0.0,
            },
            ServerType.MEMORY_OPTIMIZED: {
                "requests": 0,
                "success_rate": 0.0,
                "avg_response": 0.0,
                "uptime": 0.0,
            },
            ServerType.CPU_OPTIMIZED: {
                "requests": 0,
                "success_rate": 0.0,
                "avg_response": 0.0,
                "uptime": 0.0,
            },
        }

        self.successful_users = 0
        self.timeout_users = 0
        self.total_spawned_users = 0
        self.system_start_time = time.time()

        self.simulation_running = False
        self.simulation_start_time = 0
        self.simulation_duration = 60
        self.simulation_spawn_rate = 5.0
        self.simulation_elapsed = 0

        self.simulation_total_users = 0
        self.simulation_success_users = 0
        self.simulation_failed_users = 0

        self.bg_color = (15, 15, 25)
        self.text_color = (255, 255, 255)
        self.accent_color = (0, 200, 255)

        self.small_font = pygame.font.Font(None, 18)
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 48)

        self.event_log = deque(maxlen=50)
        self.log_event("System initialized")

        self.setup_infrastructure()

        self.algorithm_cycle_enabled = False
        self.algorithm_cycle_interval = 30.0
        self.last_algorithm_switch = time.time()
        self.algorithm_index = 0
        self.available_algorithms = list(LoadBalancingAlgorithm)

        self.simulation_panel_width = 300
        self.button_height = 30
        self.input_height = 25

        self.server_dropdowns = {}
        for i, server in enumerate(["SRV-01", "SRV-02", "SRV-03", "SRV-04"]):
            self.server_dropdowns[server] = {
                "open": False,
                "selected": list(ServerType)[i],
            }

        self.editing_field = None
        self.input_text = ""
        self.rate_input_rect = None
        self.duration_input_rect = None

        self._counting_lock = threading.Lock()

        self._counted_simulation_users = set()
        self._counted_overall_users = set()

        self.report_generator = SimulationReportGenerator()
        self.auto_save_reports = True
        self.reports_saved = False

    def setup_infrastructure(self):
        offset = 100
        """Setup load balancer and servers with diverse configurations"""

        lb_x = self.width // 4 - offset
        lb_y = self.height // 2
        self.load_balancer = LoadBalancer(
            lb_x, lb_y, LoadBalancingAlgorithm.RESOURCE_BASED
        )

        server_configs = [
            {
                "x": 3 * self.width // 4 - offset,
                "y": self.height // 5,
                "name": "SRV-01",
                "server_type": ServerType.STANDARD,
                "weight": 1,
            },
            {
                "x": 3 * self.width // 4 - offset,
                "y": 2 * self.height // 5,
                "name": "SRV-02",
                "server_type": ServerType.HIGH_PERFORMANCE,
                "weight": 3,
            },
            {
                "x": 3 * self.width // 4 - offset,
                "y": 3 * self.height // 5,
                "name": "SRV-03",
                "server_type": ServerType.MEMORY_OPTIMIZED,
                "weight": 2,
            },
            {
                "x": 3 * self.width // 4 - offset,
                "y": 4 * self.height // 5,
                "name": "SRV-04",
                "server_type": ServerType.CPU_OPTIMIZED,
                "weight": 2,
            },
        ]

        self.servers = []
        for config in server_configs:
            server = UpstreamServer(**config)
            self.servers.append(server)

        self.load_balancer.set_servers(self.servers)
        self.log_event(
            f"Infrastructure setup: {len(self.servers)} servers, {self.load_balancer.algorithm.value} algorithm"
        )

    def spawn_user(self, user_type=None):
        """Spawn user with optional type specification"""
        start_x = 50
        start_y = random.randint(100, self.height - 100)
        user = User(start_x, start_y, self.load_balancer, user_type)
        user.set_screen_height(self.height)

        user.unique_id = f"{time.time()}_{random.randint(1000, 9999)}"

        if self.simulation_running:
            user.is_simulation_user = True
            user.simulation_id = self.simulation_start_time

            with self._counting_lock:
                self.simulation_total_users += 1
        else:
            user.is_simulation_user = False
            user.simulation_id = None

        self.users.append(user)
        self.total_spawned_users += 1

    def spawn_burst_traffic(self, count=5):
        """Spawn a burst of traffic for stress testing"""
        for _ in range(count):
            user_type = random.choice(list(UserType))
            self.spawn_user(user_type)
        self.log_event(f"Traffic burst: {count} users spawned")

    def cycle_algorithm(self):
        """Cycle to next load balancing algorithm"""
        if self.algorithm_cycle_enabled:
            current_time = time.time()
            if (
                current_time - self.last_algorithm_switch
                >= self.algorithm_cycle_interval
            ):
                self.algorithm_index = (self.algorithm_index + 1) % len(
                    self.available_algorithms
                )
                new_algorithm = self.available_algorithms[self.algorithm_index]
                self.switch_algorithm(new_algorithm)
                self.last_algorithm_switch = current_time

    def switch_algorithm(self, algorithm):
        """Switch to specified algorithm"""
        old_algorithm = self.load_balancer.algorithm.value
        self.load_balancer.switch_algorithm(algorithm)
        self.log_event(f"Algorithm switched: {old_algorithm} → {algorithm.value}")

    def switch_traffic_pattern(self, pattern_name):
        """Switch to specified traffic pattern"""
        if pattern_name in self.traffic_patterns:
            self.current_traffic_pattern = self.traffic_patterns[pattern_name]
            self.log_event(f"Traffic pattern changed to: {pattern_name}")

    def log_event(self, message):
        """Log system events with timestamp"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.event_log.append(f"[{timestamp}] {message}")

    def reset_all_state(self):
        """Reset all system state to initial conditions for new simulation"""
        self.log_event("Resetting all system state for new simulation")

        self.users.clear()
        self.completed_users.clear()

        for server in self.servers:
            server.active_connections = 0
            server.total_requests = 0
            server.processing_requests.clear()
            server.request_queue.clear()
            server.current_cpu_usage = 0.0
            server.current_memory_usage = 0.0
            server.status = ServerStatus.HEALTHY
            server.recovery_time = 0
            server.response_times.clear()
            server.total_response_time = 0.0
            server.avg_response_time = 0.0
            server.load_history.clear()

        self.load_balancer.round_robin_index = 0
        self.load_balancer.weighted_round_robin_current = 0
        self.load_balancer.total_requests_received = 0
        self.load_balancer.total_requests_routed = 0
        self.load_balancer.dropped_requests = 0
        self.load_balancer.request_history.clear()
        self.load_balancer.routing_decisions.clear()
        self.load_balancer._rebuild_weighted_list()

        self.performance_monitor = PerformanceMonitor()

        self.successful_users = 0
        self.timeout_users = 0
        self.total_spawned_users = 0

        self._counted_simulation_users.clear()
        self._counted_overall_users.clear()

        self.simulation_total_users = 0
        self.simulation_success_users = 0
        self.simulation_failed_users = 0

        self.log_event("System state reset complete")

    def save_simulation_report(self):
        """Save comprehensive simulation report"""
        if not hasattr(self, "report_generator") or not self.report_generator:
            self.log_event("No report generator available")
            return None

        try:
            self.log_event("Generating simulation report...")

            self.report_generator.finalize_simulation()

            self.report_generator.collect_server_metrics(self.servers)
            self.report_generator.collect_user_analytics(
                self.completed_users, self.users
            )
            self.report_generator.collect_load_balancer_performance(self.load_balancer)
            self.report_generator.collect_system_statistics(self)

            report_files = self.report_generator.generate_comprehensive_report()

            if report_files:
                self.log_event(f"Reports saved: {len(report_files)} files generated")
                return report_files
            else:
                self.log_event("Warning: No report files generated")
                return None

        except Exception as e:
            self.log_event(f"Error generating reports: {str(e)}")
            return None

    def start_simulation(self):
        """Start the scenario simulation with full state reset"""

        if self.total_spawned_users > 0:
            self.log_event("Saving pre-simulation report...")
            self.save_simulation_report()

        self.reset_all_state()
        self.report_generator = SimulationReportGenerator()

        with self._counting_lock:
            self.simulation_running = True
            self.simulation_start_time = time.time()
            self.simulation_elapsed = 0

        if hasattr(self, "report_generator"):
            simulation_config = {
                "screen_resolution": f"{self.width}x{self.height}",
                "initial_algorithm": self.load_balancer.algorithm.value,
                "server_count": len(self.servers),
                "server_types": [s.server_type.value for s in self.servers],
                "traffic_pattern": self.current_traffic_pattern.name,
                "auto_algorithm_cycling": self.algorithm_cycle_enabled,
                "simulation_duration": self.simulation_duration,
                "simulation_spawn_rate": self.simulation_spawn_rate,
            }
            self.report_generator.initialize_simulation(simulation_config)

        self.log_event(
            f"Simulation started: {self.simulation_spawn_rate}/s for {self.simulation_duration}s (STATE RESET)"
        )

    def stop_simulation(self):
        """Stop the scenario simulation and save comprehensive report"""
        if not self.simulation_running:
            return

        self.simulation_running = False

        self.log_event("Simulation stopped - generating final report...")
        report_files = self.save_simulation_report()

        if report_files:
            self.log_event(f"Simulation report saved to {len(report_files)} files")

            simulation_duration = time.time() - self.simulation_start_time
            success_rate = (
                self.simulation_success_users
                / max(1, (self.simulation_success_users + self.simulation_failed_users))
            ) * 100

            self.log_event(f"Simulation Summary:")
            self.log_event(f"  Duration: {simulation_duration:.1f}s")
            self.log_event(f"  Total Users: {self.simulation_total_users}")
            self.log_event(f"  Success Rate: {success_rate:.1f}%")
            self.log_event(f"  Algorithm: {self.load_balancer.algorithm.value}")
        else:
            self.log_event("Warning: Failed to generate simulation report")

    def update_server_type(self, server_name, new_type):
        """Update a server's type"""
        for server in self.servers:
            if server.name == server_name:
                server.server_type = new_type
                server._set_server_specs()
                self.log_event(f"Server {server_name} changed to {new_type.value}")
                break

    def _count_simulation_completion(self, user, is_success):
        """Thread-safe simulation counting to prevent race conditions"""
        with self._counting_lock:

            if (
                hasattr(user, "is_simulation_user")
                and user.is_simulation_user
                and hasattr(user, "simulation_id")
                and user.simulation_id == self.simulation_start_time
                and hasattr(user, "unique_id")
                and user.unique_id not in self._counted_simulation_users
            ):

                self._counted_simulation_users.add(user.unique_id)

                if is_success:
                    self.simulation_success_users += 1
                else:
                    self.simulation_failed_users += 1

                return True
        return False

    def _count_overall_completion(self, user, is_success):
        """Thread-safe overall counting to prevent race conditions"""
        with self._counting_lock:
            if (
                hasattr(user, "unique_id")
                and user.unique_id not in self._counted_overall_users
            ):

                self._counted_overall_users.add(user.unique_id)

                if is_success:
                    self.successful_users += 1
                else:
                    self.timeout_users += 1

                return True
        return False

    def update(self):
        """Main update loop with enhanced features"""
        current_time = time.time()

        if self.simulation_running:
            self.simulation_elapsed = current_time - self.simulation_start_time
            if self.simulation_elapsed >= self.simulation_duration:
                self.stop_simulation()

        if self.simulation_running:
            spawn_rate = self.simulation_spawn_rate
            spawn_interval = 1.0 / spawn_rate if spawn_rate > 0 else float("inf")

            if current_time - self.last_spawn_time > spawn_interval:
                self.spawn_user()
                self.last_spawn_time = current_time
        else:

            pass

        self.cycle_algorithm()

        remaining_users = []
        completed_this_update = 0

        completed_users = []

        for user in self.users:
            user_still_active = user.update()

            if user_still_active:

                remaining_users.append(user)
            else:

                completed_users.append(user)

        for user in completed_users:

            is_success = user.state == "done" and not user.failed

            self._count_simulation_completion(user, is_success)
            self._count_overall_completion(user, is_success)

            self.performance_monitor.record_user_completion(user)
            self.completed_users.append(user)
            completed_this_update += 1

        self.users = remaining_users

        for server in self.servers:
            server.update()

        if current_time - self.last_performance_update >= 10.0:
            performance = self.load_balancer.evaluate_performance()
            if performance:
                self.log_event(
                    f"Performance: {performance['success_rate']:.1%} success, "
                    f"avg load: {performance['avg_load']:.2f}"
                )
            self.last_performance_update = current_time

        if self.simulation_spawn_rate > 50:
            if current_time % 1.0 < 0.1:
                self._validate_simulation_counts()
        else:
            self._validate_simulation_counts()

        self.update_server_statistics()

        self.update_traffic_analytics()

        self.update_algorithm_performance_tracking()

        self.update_system_resource_tracking()

    def _validate_simulation_counts(self):
        """Validate simulation counts to ensure consistency"""
        with self._counting_lock:
            total_counted = self.simulation_success_users + self.simulation_failed_users

            max_discrepancy = max(2, int(self.simulation_spawn_rate * 0.01))

            if abs(total_counted - self.simulation_total_users) > max_discrepancy:
                self.log_event(
                    f"Count validation: Total={self.simulation_total_users}, "
                    f"Success={self.simulation_success_users}, "
                    f"Failed={self.simulation_failed_users}, "
                    f"Sum={total_counted}, "
                    f"Tracked={len(self._counted_simulation_users)}"
                )

    def get_system_stats(self):
        """Get comprehensive system statistics"""
        uptime = time.time() - self.system_start_time
        total_completed = self.successful_users + self.timeout_users

        stats = {
            "uptime": uptime,
            "total_spawned": self.total_spawned_users,
            "active_users": len(self.users),
            "successful": self.successful_users,
            "timeouts": self.timeout_users,
            "success_rate": (self.successful_users / max(1, total_completed)) * 100,
            "algorithm": self.load_balancer.algorithm.value,
            "traffic_pattern": self.current_traffic_pattern.name,
        }

        healthy_servers = len(
            [s for s in self.servers if s.status == ServerStatus.HEALTHY]
        )
        stats["healthy_servers"] = f"{healthy_servers}/{len(self.servers)}"

        return stats

    def draw_header(self, screen):
        """Draw enhanced header with system information"""

        title_text = f"Load Balancer System - {self.load_balancer.algorithm.value.replace('_', ' ').title()}"
        title = self.title_font.render(title_text, True, self.accent_color)
        screen.blit(title, (20, 15))

        stats = self.get_system_stats()
        stats_text = (
            f"Uptime: {stats['uptime']:.0f}s | "
            f"Active: {stats['active_users']} | "
            f"Success Rate: {stats['success_rate']:.1f}% | "
            f"Servers: {stats['healthy_servers']}"
        )

        stats_surface = self.font.render(stats_text, True, self.text_color)
        screen.blit(stats_surface, (20, 55))

        if self.simulation_running:
            pattern_text = f"SIMULATION ACTIVE | Rate: {self.simulation_spawn_rate:.1f}/s | Remaining: {max(0, self.simulation_duration - self.simulation_elapsed):.1f}s"
            pattern_color = (255, 100, 100)
        else:
            pattern_text = f"IDLE MODE - No automatic spawning | Manual controls: SPACE (single), B (burst)"
            pattern_color = (150, 150, 150)

        pattern_surface = self.font.render(pattern_text, True, pattern_color)
        screen.blit(pattern_surface, (20, 80))

    def draw_legend(self, screen):
        """Draw comprehensive legend"""
        legend_x = 20
        legend_y = 120

        legend_items = [
            ("User Types:", None, (255, 255, 255)),
            ("L = Light", (150, 200, 255), None),
            ("S = Standard", (100, 150, 255), None),
            ("H = Heavy", (50, 100, 200), None),
            ("B = Burst", (255, 150, 50), None),
            ("", None, None),
            ("Server Types:", None, (255, 255, 255)),
            ("Standard", (255, 255, 255), None),
            ("High-Perf", (255, 215, 0), None),
            ("Memory-Opt", (0, 191, 255), None),
            ("CPU-Opt", (255, 20, 147), None),
            ("", None, None),
            ("States:", None, (255, 255, 255)),
            ("Moving", (100, 150, 255), None),
            ("Waiting", (255, 255, 0), None),
            ("Processing", (255, 200, 0), None),
            ("Timeout", (255, 100, 100), None),
            ("", None, None),
            ("Attack Types:", None, (255, 255, 255)),
            ("DOS", (255, 0, 0), None),
            ("Resource Exhaustion", (150, 0, 150), None),
            ("Slowloris", (255, 100, 0), None),
            ("Amplification", (255, 0, 150), None),
            ("Priority Abuse", (100, 0, 0), None),
        ]

        for i, (text, color, text_color) in enumerate(legend_items):
            if not text:
                continue

            y_pos = legend_y + (i * 15)

            if color:
                pygame.draw.circle(screen, color, (legend_x + 5, y_pos + 5), 4)
                text_surface = self.small_font.render(
                    text, True, text_color or self.text_color
                )
                screen.blit(text_surface, (legend_x + 15, y_pos))
            else:
                text_surface = self.small_font.render(
                    text, True, text_color or self.text_color
                )
                screen.blit(text_surface, (legend_x, y_pos))

    def draw_performance_panel(self, screen):
        """Draw performance monitoring panel"""
        panel_x = 740
        panel_y = self.height - 150
        panel_width = 280
        panel_height = 140

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(screen, self.accent_color, panel_rect, 2)

        title = self.font.render("Performance Monitor", True, self.accent_color)
        screen.blit(title, (panel_x + 10, panel_y + 10))

        perf_summary = self.performance_monitor.get_performance_summary()
        if perf_summary:
            metrics_text = [
                f"Avg Response: {perf_summary.get('avg_response_time', 0):.2f}s",
                f"P95 Response: {perf_summary.get('p95_response_time', 0):.2f}s",
                f"P99 Response: {perf_summary.get('p99_response_time', 0):.2f}s",
                f"Total Requests: {perf_summary.get('total_requests', 0)}",
            ]

            for i, metric in enumerate(metrics_text):
                metric_surface = self.small_font.render(metric, True, self.text_color)
                screen.blit(metric_surface, (panel_x + 10, panel_y + 35 + (i * 16)))

        algo_stats = self.load_balancer.get_algorithm_stats()
        if algo_stats:
            algo_text = f"Algorithm Success: {algo_stats.get('success_rate', 0):.1%}"
            algo_surface = self.small_font.render(
                algo_text,
                True,
                (
                    (0, 255, 0)
                    if algo_stats.get("success_rate", 0) > 0.9
                    else (255, 255, 0)
                ),
            )
            screen.blit(algo_surface, (panel_x + 10, panel_y + 115))

    def draw_instructions(self, screen):
        """Draw control instructions"""
        if self.simulation_running:

            instructions = [
                "Simulation Mode:",
                "S - Stop simulation",
                "1-7 - Switch algorithm",
                "A - Auto algorithm cycle",
                "SPACE/B/Q/W/E/R - Disabled",
                "ESC - Quit",
            ]
        else:

            instructions = [
                "Idle Mode (No Auto-spawn):",
                "SPACE - Spawn single user",
                "B - Spawn burst traffic (8 users)",
                "1-7 - Switch algorithm",
                "A - Auto algorithm cycle",
                "S - Start simulation",
                "ESC - Quit",
            ]

        for i, instruction in enumerate(instructions):
            if i == 0:
                color = self.accent_color
            elif self.simulation_running and "Disabled" in instruction:
                color = (150, 150, 150)
            elif not self.simulation_running and (
                "SPACE" in instruction or "B -" in instruction
            ):
                color = (255, 255, 100)
            else:
                color = (200, 200, 200)

            font = self.font if i == 0 else self.small_font
            text = font.render(instruction, True, color)
            screen.blit(text, (20, self.height - 150 + (i * 18)))

    def draw_server_configuration(self, screen):

        panel_x = 220
        panel_y = self.height - 290
        panel_width = 500
        panel_height = 280

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (25, 25, 35), panel_rect)
        pygame.draw.rect(screen, self.accent_color, panel_rect, 2)

        y_offset = panel_y + 10

        config_title = self.font.render("Server Configuration", True, self.accent_color)
        screen.blit(config_title, (panel_x + 10, y_offset))
        y_offset += 35

        server_types = list(ServerType)
        type_names = {
            ServerType.STANDARD: "Standard",
            ServerType.HIGH_PERFORMANCE: "High-Perf",
            ServerType.MEMORY_OPTIMIZED: "Memory-Opt",
            ServerType.CPU_OPTIMIZED: "CPU-Opt",
        }

        if not hasattr(self, "dropdown_rects"):
            self.dropdown_rects = {}

        col_width = (panel_width - 40) // 2
        servers_per_row = 2

        for i, server in enumerate(self.servers):

            row = i // servers_per_row
            col = i % servers_per_row

            x_pos = panel_x + 10 + (col * col_width)
            y_pos = y_offset + (row * 110)

            server_label = self.small_font.render(
                f"{server.name}:", True, self.text_color
            )
            screen.blit(server_label, (x_pos, y_pos))
            y_pos += 18

            dropdown_rect = pygame.Rect(x_pos, y_pos, col_width - 20, self.input_height)
            pygame.draw.rect(screen, (40, 40, 50), dropdown_rect)
            pygame.draw.rect(screen, (100, 100, 100), dropdown_rect, 1)

            current_type = type_names[server.server_type]
            dropdown_text = self.small_font.render(current_type, True, self.text_color)
            screen.blit(dropdown_text, (dropdown_rect.x + 5, dropdown_rect.y + 5))

            arrow = "▼" if not self.server_dropdowns[server.name]["open"] else "▲"
            arrow_text = self.small_font.render(arrow, True, self.text_color)
            screen.blit(arrow_text, (dropdown_rect.right - 20, dropdown_rect.y + 5))

            self.dropdown_rects[server.name] = {"main": dropdown_rect, "options": []}

            if self.server_dropdowns[server.name]["open"]:
                option_y = y_pos + self.input_height
                for j, server_type in enumerate(server_types):
                    option_rect = pygame.Rect(
                        dropdown_rect.x,
                        option_y,
                        dropdown_rect.width,
                        self.input_height,
                    )

                    if server_type == server.server_type:
                        pygame.draw.rect(screen, (60, 60, 80), option_rect)
                    else:
                        pygame.draw.rect(screen, (50, 50, 60), option_rect)

                    pygame.draw.rect(screen, (100, 100, 100), option_rect, 1)

                    option_text = self.small_font.render(
                        type_names[server_type], True, self.text_color
                    )
                    screen.blit(option_text, (option_rect.x + 5, option_rect.y + 5))

                    self.dropdown_rects[server.name]["options"].append(
                        {"rect": option_rect, "type": server_type}
                    )

                    option_y += self.input_height

    def draw_simulation_panel(self, screen):
        """Draw simulation control panel on the right side with comprehensive metrics"""
        panel_x = self.width - self.simulation_panel_width - 20
        panel_y = 100
        panel_height = self.height - 200

        panel_rect = pygame.Rect(
            panel_x, panel_y, self.simulation_panel_width, panel_height
        )
        pygame.draw.rect(screen, (25, 25, 35), panel_rect)
        pygame.draw.rect(screen, self.accent_color, panel_rect, 2)

        title = self.font.render(
            "Simulation Control & Metrics", True, self.accent_color
        )
        screen.blit(title, (panel_x + 10, panel_y + 10))

        y_offset = panel_y + 50

        if self.simulation_running:
            remaining = max(0, self.simulation_duration - self.simulation_elapsed)
            status_text = f"Running: {remaining:.1f}s remaining"
            status_color = (0, 255, 0)
        else:
            status_text = "Stopped"
            status_color = (255, 100, 100)

        status_surface = self.font.render(status_text, True, status_color)
        screen.blit(status_surface, (panel_x + 10, y_offset))
        y_offset += 35

        counters_title = self.small_font.render(
            "Simulation Stats:", True, self.accent_color
        )
        screen.blit(counters_title, (panel_x + 10, y_offset))
        y_offset += 20

        total_text = self.small_font.render(
            f"Total Users: {self.simulation_success_users + self.simulation_failed_users}",
            True,
            self.text_color,
        )
        screen.blit(total_text, (panel_x + 10, y_offset))
        y_offset += 15

        success_text = self.small_font.render(
            f"Success: {self.simulation_success_users}", True, (0, 255, 0)
        )
        screen.blit(success_text, (panel_x + 10, y_offset))
        y_offset += 15

        failed_text = self.small_font.render(
            f"Failed: {self.simulation_failed_users}", True, (255, 100, 100)
        )
        screen.blit(failed_text, (panel_x + 10, y_offset))
        y_offset += 15

        if (self.simulation_failed_users + self.simulation_success_users) > 0:
            sim_success_rate = (
                self.simulation_success_users
                / (self.simulation_failed_users + self.simulation_success_users)
            ) * 100
            rate_color = (
                (0, 255, 0)
                if sim_success_rate > 80
                else (255, 255, 0) if sim_success_rate > 60 else (255, 100, 100)
            )
            rate_text = self.small_font.render(
                f"Success Rate: {sim_success_rate:.1f}%", True, rate_color
            )
            screen.blit(rate_text, (panel_x + 10, y_offset))
        y_offset += 25

        server_metrics_title = self.small_font.render(
            "Server Performance:", True, self.accent_color
        )
        screen.blit(server_metrics_title, (panel_x + 10, y_offset))
        y_offset += 20

        server_stats = self.get_comprehensive_server_stats()

        for server_name, stats in server_stats.items():

            server_header = self.small_font.render(
                f"{server_name} ({stats['type'][:4].upper()})", True, self.text_color
            )
            screen.blit(server_header, (panel_x + 10, y_offset))
            y_offset += 12

            status_colors = {
                "healthy": (0, 255, 0),
                "degraded": (255, 255, 0),
                "overloaded": (255, 150, 50),
                "failed": (255, 50, 50),
            }
            status_color = status_colors.get(stats["status"], (255, 255, 255))

            metrics_line1 = f"  Conn:{stats['active_connections']} CPU:{stats['current_cpu']:.0f}% Mem:{stats['current_memory']:.0f}%"
            metrics_line2 = f"  Req:{stats['total_requests']} RT:{stats['avg_response_time']:.2f}s Up:{stats['uptime_percentage']:.0f}%"

            metrics1_text = self.small_font.render(metrics_line1, True, status_color)
            screen.blit(metrics1_text, (panel_x + 10, y_offset))
            y_offset += 12

            metrics2_text = self.small_font.render(metrics_line2, True, (200, 200, 200))
            screen.blit(metrics2_text, (panel_x + 10, y_offset))
            y_offset += 15

        y_offset += 10
        algo_title = self.small_font.render(
            "Algorithm Performance:", True, self.accent_color
        )
        screen.blit(algo_title, (panel_x + 10, y_offset))
        y_offset += 15

        algo_stats = self.load_balancer.get_algorithm_stats()
        if algo_stats:
            current_algo = f"Current: {algo_stats.get('algorithm', 'Unknown').replace('_', ' ').title()}"
            algo_text = self.small_font.render(current_algo, True, self.text_color)
            screen.blit(algo_text, (panel_x + 10, y_offset))
            y_offset += 12

            success_rate = algo_stats.get("success_rate", 0) * 100
            success_color = (
                (0, 255, 0)
                if success_rate > 90
                else (255, 255, 0) if success_rate > 70 else (255, 100, 100)
            )

            algo_metrics = f"Success: {success_rate:.1f}% Routed: {algo_stats.get('requests_routed', 0)}"
            algo_metrics_text = self.small_font.render(
                algo_metrics, True, success_color
            )
            screen.blit(algo_metrics_text, (panel_x + 10, y_offset))
            y_offset += 12

            dropped = algo_stats.get("dropped_requests", 0)
            if dropped > 0:
                dropped_text = self.small_font.render(
                    f"Dropped: {dropped}", True, (255, 100, 100)
                )
                screen.blit(dropped_text, (panel_x + 10, y_offset))
                y_offset += 12

        y_offset += 10
        traffic_title = self.small_font.render(
            "Traffic Analytics:", True, self.accent_color
        )
        screen.blit(traffic_title, (panel_x + 10, y_offset))
        y_offset += 15

        peak_users = self.traffic_analytics["peak_concurrent_users"]
        current_users = len(self.users)
        burst_freq = self.traffic_analytics["burst_frequency"]

        peak_text = self.small_font.render(
            f"Peak Concurrent: {peak_users}", True, self.text_color
        )
        screen.blit(peak_text, (panel_x + 10, y_offset))
        y_offset += 12

        current_text = self.small_font.render(
            f"Current Active: {current_users}", True, self.text_color
        )
        screen.blit(current_text, (panel_x + 10, y_offset))
        y_offset += 12

        burst_text = self.small_font.render(
            f"Burst Events: {burst_freq}", True, self.text_color
        )
        screen.blit(burst_text, (panel_x + 10, y_offset))
        y_offset += 15

        y_offset += 10
        perf_title = self.small_font.render(
            "Performance Summary:", True, self.accent_color
        )
        screen.blit(perf_title, (panel_x + 10, y_offset))
        y_offset += 15

        perf_summary = self.performance_monitor.get_performance_summary()
        if perf_summary:
            avg_response = perf_summary.get("avg_response_time", 0)
            p95_response = perf_summary.get("p95_response_time", 0)
            total_requests = perf_summary.get("total_requests", 0)

            response_color = (
                (0, 255, 0)
                if avg_response < 2
                else (255, 255, 0) if avg_response < 5 else (255, 100, 100)
            )

            avg_text = self.small_font.render(
                f"Avg Response: {avg_response:.2f}s", True, response_color
            )
            screen.blit(avg_text, (panel_x + 10, y_offset))
            y_offset += 12

            p95_text = self.small_font.render(
                f"P95 Response: {p95_response:.2f}s", True, self.text_color
            )
            screen.blit(p95_text, (panel_x + 10, y_offset))
            y_offset += 12

            total_text = self.small_font.render(
                f"Total Processed: {total_requests}", True, self.text_color
            )
            screen.blit(total_text, (panel_x + 10, y_offset))
            y_offset += 20

        rate_label = self.small_font.render("Users per second:", True, self.text_color)
        screen.blit(rate_label, (panel_x + 10, y_offset))
        y_offset += 20

        rate_rect = pygame.Rect(panel_x + 10, y_offset, 100, self.input_height)
        self.rate_input_rect = rate_rect

        if self.editing_field == "rate":
            pygame.draw.rect(screen, (60, 60, 80), rate_rect)
            pygame.draw.rect(screen, (0, 200, 255), rate_rect, 2)
            display_text = self.input_text
        else:
            pygame.draw.rect(screen, (40, 40, 50), rate_rect)
            pygame.draw.rect(screen, (100, 100, 100), rate_rect, 1)
            display_text = f"{self.simulation_spawn_rate:.1f}"

        rate_text = self.small_font.render(display_text, True, self.text_color)
        screen.blit(rate_text, (rate_rect.x + 5, rate_rect.y + 5))

        if self.editing_field == "rate":
            cursor_x = rate_rect.x + 5 + rate_text.get_width()
            if int(time.time() * 2) % 2:
                pygame.draw.line(
                    screen,
                    self.text_color,
                    (cursor_x, rate_rect.y + 3),
                    (cursor_x, rate_rect.y + rate_rect.height - 3),
                    1,
                )

        y_offset += 35

        duration_label = self.small_font.render(
            "Duration (seconds):", True, self.text_color
        )
        screen.blit(duration_label, (panel_x + 10, y_offset))
        y_offset += 20

        duration_rect = pygame.Rect(panel_x + 10, y_offset, 100, self.input_height)
        self.duration_input_rect = duration_rect

        if self.editing_field == "duration":
            pygame.draw.rect(screen, (60, 60, 80), duration_rect)
            pygame.draw.rect(screen, (0, 200, 255), duration_rect, 2)
            display_text = self.input_text
        else:
            pygame.draw.rect(screen, (40, 40, 50), duration_rect)
            pygame.draw.rect(screen, (100, 100, 100), duration_rect, 1)
            display_text = f"{self.simulation_duration}"

        duration_text = self.small_font.render(display_text, True, self.text_color)
        screen.blit(duration_text, (duration_rect.x + 5, duration_rect.y + 5))

        if self.editing_field == "duration":
            cursor_x = duration_rect.x + 5 + duration_text.get_width()
            if int(time.time() * 2) % 2:
                pygame.draw.line(
                    screen,
                    self.text_color,
                    (cursor_x, duration_rect.y + 3),
                    (cursor_x, duration_rect.y + duration_rect.height - 3),
                    1,
                )

        y_offset += 40

    def handle_mouse_click(self, pos):
        """Handle mouse clicks for both simulation panel and server configuration"""

        panel_x = self.width - self.simulation_panel_width - 20
        panel_y = 100

        config_panel_x = 220
        config_panel_y = self.height - 290
        config_panel_width = 500
        config_panel_height = 680

        in_config_panel = (
            config_panel_x <= pos[0] <= config_panel_x + config_panel_width
        )

        in_simulation_panel = (
            panel_x <= pos[0] <= self.width - 20
            and panel_y <= pos[1] <= panel_y + self.height - 200
        )

        if not (in_simulation_panel or in_config_panel):
            self.editing_field = None
            return

        if in_simulation_panel:
            if (
                hasattr(self, "rate_input_rect")
                and self.rate_input_rect
                and self.rate_input_rect.collidepoint(pos)
            ):
                self.editing_field = "rate"
                self.input_text = f"{self.simulation_spawn_rate:.1f}"
                return

            if (
                hasattr(self, "duration_input_rect")
                and self.duration_input_rect
                and self.duration_input_rect.collidepoint(pos)
            ):
                self.editing_field = "duration"
                self.input_text = f"{self.simulation_duration}"
                return

        if hasattr(self, "dropdown_rects"):
            for server_name, rects in self.dropdown_rects.items():

                if rects["main"].collidepoint(pos):

                    self.server_dropdowns[server_name]["open"] = (
                        not self.server_dropdowns[server_name]["open"]
                    )

                    for other_name in self.server_dropdowns:
                        if other_name != server_name:
                            self.server_dropdowns[other_name]["open"] = False
                    return

                for option in rects["options"]:
                    if option["rect"].collidepoint(pos):

                        server_type = option["type"]
                        self.update_server_type(server_name, server_type)
                        self.server_dropdowns[server_name]["open"] = False
                        return

    def handle_text_input(self, text):
        """Handle text input for editable fields"""
        if self.editing_field and len(self.input_text) < 10:

            if text.isdigit() or (text == "." and "." not in self.input_text):
                self.input_text += text

    def handle_key_input(self, key):
        """Handle special key inputs for text editing"""
        if self.editing_field:
            if key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:

                try:
                    value = float(self.input_text) if self.input_text else 0
                    if self.editing_field == "rate":
                        new_rate = float(self.input_text)
                        self.simulation_spawn_rate = max(0.1, min(100.0, new_rate))
                        self.log_event(
                            f"Spawn rate changed to {self.simulation_spawn_rate:.1f}/s"
                        )
                    elif self.editing_field == "duration":
                        new_duration = int(float(self.input_text))
                        self.simulation_duration = max(10, min(3600, new_duration))
                        self.log_event(
                            f"Duration changed to {self.simulation_duration}s"
                        )
                except ValueError:
                    self.log_event("Invalid input - please enter a valid number")
                self.editing_field = None
            elif key == pygame.K_ESCAPE:

                self.editing_field = None

    def handle_keypress(self, key):
        """Handle keyboard input for system control"""

        if self.editing_field:
            self.handle_key_input(key)
            return

        if key == pygame.K_SPACE:

            if not self.simulation_running:
                self.spawn_user()
            else:
                self.log_event("Manual spawning disabled during simulation")
        elif key == pygame.K_b:

            if not self.simulation_running:
                self.spawn_burst_traffic(8)
            else:
                self.log_event("Burst traffic disabled during simulation")
        elif key == pygame.K_a:
            self.algorithm_cycle_enabled = not self.algorithm_cycle_enabled
            status = "enabled" if self.algorithm_cycle_enabled else "disabled"
            self.log_event(f"Algorithm auto-cycling {status}")
        elif key in [
            pygame.K_1,
            pygame.K_2,
            pygame.K_3,
            pygame.K_4,
            pygame.K_5,
            pygame.K_6,
            pygame.K_7,
        ]:
            algo_index = key - pygame.K_1
            if algo_index < len(self.available_algorithms):
                self.switch_algorithm(self.available_algorithms[algo_index])
        elif key == pygame.K_q:

            if not self.simulation_running:
                self.switch_traffic_pattern("steady")
            else:
                self.log_event("Traffic pattern changes disabled during simulation")
        elif key == pygame.K_w:
            if not self.simulation_running:
                self.switch_traffic_pattern("wave")
            else:
                self.log_event("Traffic pattern changes disabled during simulation")
        elif key == pygame.K_e:
            if not self.simulation_running:
                self.switch_traffic_pattern("spike")
            else:
                self.log_event("Traffic pattern changes disabled during simulation")
        elif key == pygame.K_r:
            if not self.simulation_running:
                self.switch_traffic_pattern("random")
            else:
                self.log_event("Traffic pattern changes disabled during simulation")
        elif key == pygame.K_s:

            if self.simulation_running:
                self.stop_simulation()
            else:
                self.start_simulation()

    def draw(self, screen):
        """Main drawing method with all enhancements"""
        screen.fill(self.bg_color)

        self.draw_header(screen)
        self.draw_legend(screen)
        self.draw_instructions(screen)

        self.draw_server_configuration(screen)

        for server in self.servers:
            line_color = (100, 100, 100)
            if server.status == ServerStatus.FAILED:
                line_color = (100, 50, 50)
            elif server.status == ServerStatus.OVERLOADED:
                line_color = (150, 100, 50)
            elif server.active_connections > 0:
                intensity = min(255, 100 + (server.active_connections * 30))
                line_color = (intensity, 100, 100)

            line_width = 2 + min(3, server.active_connections)
            pygame.draw.line(
                screen,
                line_color,
                (self.load_balancer.x, self.load_balancer.y),
                (server.x, server.y),
                line_width,
            )

        for server in self.servers:
            server.draw(screen, self.small_font)

        for user in self.users:
            user.draw(screen)

        self.load_balancer.draw(screen)

        if self.algorithm_cycle_enabled:
            cycle_text = (
                f"Auto-cycling algorithms every {self.algorithm_cycle_interval}s"
            )
            cycle_surface = self.small_font.render(cycle_text, True, (255, 255, 0))
            screen.blit(cycle_surface, (self.width - 350, 50))

        self.draw_performance_panel(screen)

        self.draw_simulation_panel(screen)

    def update_server_statistics(self):
        """Update comprehensive server-based statistics"""
        current_time = time.time()

        for server in self.servers:
            server_name = server.name

            if server_name not in self.server_stats:
                self.server_stats[server_name] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_response_time": 0.0,
                    "uptime_start": current_time,
                    "downtime_periods": [],
                    "peak_connections": 0,
                    "cpu_utilization_history": deque(maxlen=100),
                    "memory_utilization_history": deque(maxlen=100),
                    "last_status": server.status,
                }

            stats = self.server_stats[server_name]

            if stats["last_status"] != server.status:
                if server.status == ServerStatus.FAILED:
                    stats["downtime_periods"].append(
                        {"start": current_time, "end": None, "reason": "failure"}
                    )
                elif stats["last_status"] == ServerStatus.FAILED:

                    if (
                        stats["downtime_periods"]
                        and stats["downtime_periods"][-1]["end"] is None
                    ):
                        stats["downtime_periods"][-1]["end"] = current_time

                stats["last_status"] = server.status

            stats["cpu_utilization_history"].append(server.cpu_utilization)
            stats["memory_utilization_history"].append(server.memory_utilization)

            if server.active_connections > stats["peak_connections"]:
                stats["peak_connections"] = server.active_connections

            server_type = server.server_type
            type_stats = self.server_type_analytics[server_type]

            uptime_duration = current_time - stats["uptime_start"]
            downtime_total = sum(
                (period["end"] or current_time) - period["start"]
                for period in stats["downtime_periods"]
            )
            uptime_percentage = (
                ((uptime_duration - downtime_total) / uptime_duration) * 100
                if uptime_duration > 0
                else 100
            )
            type_stats["uptime"] = uptime_percentage

            if server_name not in self.server_performance_history:
                self.server_performance_history[server_name] = {
                    "load_scores": deque(maxlen=50),
                    "response_times": deque(maxlen=100),
                    "connection_counts": deque(maxlen=100),
                    "error_rates": deque(maxlen=50),
                }

            perf_history = self.server_performance_history[server_name]
            perf_history["load_scores"].append(
                server.load_score if server.load_score != float("inf") else 1.0
            )
            perf_history["response_times"].extend(list(server.response_times)[-10:])
            perf_history["connection_counts"].append(server.active_connections)

            error_rate = 1.0 if server.status == ServerStatus.FAILED else 0.0
            perf_history["error_rates"].append(error_rate)

            if server_name not in self.server_load_distribution:
                self.server_load_distribution[server_name] = {
                    "request_distribution": [],
                    "load_balance_efficiency": 0.0,
                    "utilization_variance": 0.0,
                }

    def update_traffic_analytics(self):
        """Update traffic pattern analytics"""
        current_time = time.time()
        current_hour = int(time.localtime(current_time).tm_hour)

        self.traffic_analytics["hourly_distribution"][current_hour] += len(self.users)

        current_concurrent = len(self.users)
        if current_concurrent > self.traffic_analytics["peak_concurrent_users"]:
            self.traffic_analytics["peak_concurrent_users"] = current_concurrent

        self.traffic_analytics["total_throughput"] = self.total_spawned_users

        pattern_name = self.current_traffic_pattern.name
        if pattern_name not in self.traffic_analytics["pattern_efficiency"]:
            self.traffic_analytics["pattern_efficiency"][pattern_name] = {
                "total_requests": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "utilization_efficiency": 0.0,
            }

        pattern_stats = self.traffic_analytics["pattern_efficiency"][pattern_name]
        pattern_stats["total_requests"] = self.total_spawned_users

        total_completed = self.successful_users + self.timeout_users
        if total_completed > 0:
            pattern_stats["success_rate"] = (
                self.successful_users / total_completed
            ) * 100

    def update_algorithm_performance_tracking(self):
        """Track algorithm performance over time"""
        current_algorithm = self.load_balancer.algorithm.value
        current_time = time.time()

        if current_algorithm not in self.algorithm_performance_history:
            self.algorithm_performance_history[current_algorithm] = {
                "total_time": 0.0,
                "total_requests": 0,
                "successful_requests": 0,
                "avg_response_time": 0.0,
                "server_utilization": [],
                "load_distribution_variance": [],
                "start_time": current_time,
            }

        algo_stats = self.algorithm_performance_history[current_algorithm]

        algo_stats["total_requests"] = self.load_balancer.total_requests_received
        algo_stats["successful_requests"] = self.load_balancer.total_requests_routed

        server_loads = [
            s.load_score for s in self.servers if s.load_score != float("inf")
        ]
        if server_loads:
            load_variance = np.var(server_loads)
            algo_stats["load_distribution_variance"].append(load_variance)

        avg_utilization = np.mean([s.cpu_utilization for s in self.servers])
        algo_stats["server_utilization"].append(avg_utilization)

    def update_system_resource_tracking(self):
        """Update system-wide resource utilization tracking"""
        current_time = time.time()

        total_cpu_usage = sum(s.current_cpu_usage for s in self.servers)
        total_memory_usage = sum(s.current_memory_usage for s in self.servers)
        total_cpu_capacity = sum(s.cpu_cores for s in self.servers)
        total_memory_capacity = sum(s.memory_gb for s in self.servers)

        system_cpu_percentage = (
            (total_cpu_usage / total_cpu_capacity) * 100
            if total_cpu_capacity > 0
            else 0
        )
        system_memory_percentage = (
            (total_memory_usage / total_memory_capacity) * 100
            if total_memory_capacity > 0
            else 0
        )

        self.system_resource_history["cpu_usage"].append(system_cpu_percentage)
        self.system_resource_history["memory_usage"].append(system_memory_percentage)

        if len(self.system_resource_history["network_throughput"]) > 0:
            recent_requests = len(
                [
                    u
                    for u in self.users
                    if hasattr(u, "spawn_time") and current_time - u.spawn_time < 1.0
                ]
            )
            self.system_resource_history["network_throughput"].append(recent_requests)
        else:
            self.system_resource_history["network_throughput"].append(0)

        if self.performance_monitor.metrics["response_times"]:
            recent_latency = np.mean(
                list(self.performance_monitor.metrics["response_times"])[-10:]
            )
            self.system_resource_history["request_latency"].append(recent_latency)
        else:
            self.system_resource_history["request_latency"].append(0)

    def get_comprehensive_server_stats(self):
        """Get detailed server statistics for display"""
        stats = {}

        for server in self.servers:
            server_name = server.name
            server_stats = self.server_stats.get(server_name, {})
            perf_history = self.server_performance_history.get(server_name, {})

            cpu_history = server_stats.get("cpu_utilization_history", [])
            memory_history = server_stats.get("memory_utilization_history", [])

            stats[server_name] = {
                "status": server.status.value,
                "type": server.server_type.value,
                "active_connections": server.active_connections,
                "total_requests": server.total_requests,
                "current_cpu": server.cpu_utilization,
                "current_memory": server.memory_utilization,
                "load_score": (
                    server.load_score if server.load_score != float("inf") else "N/A"
                ),
                "avg_response_time": server.avg_response_time,
                "peak_connections": server_stats.get("peak_connections", 0),
                "avg_cpu_utilization": np.mean(cpu_history) if cpu_history else 0,
                "peak_cpu_utilization": max(cpu_history) if cpu_history else 0,
                "avg_memory_utilization": (
                    np.mean(memory_history) if memory_history else 0
                ),
                "peak_memory_utilization": max(memory_history) if memory_history else 0,
                "uptime_percentage": self._calculate_uptime_percentage(server_name),
                "failure_count": len(server_stats.get("downtime_periods", [])),
                "load_variance": (
                    np.var(perf_history.get("load_scores", [0]))
                    if perf_history.get("load_scores")
                    else 0
                ),
                "connection_stability": (
                    np.std(perf_history.get("connection_counts", [0]))
                    if perf_history.get("connection_counts")
                    else 0
                ),
            }

        return stats

    def _calculate_uptime_percentage(self, server_name):
        """Calculate uptime percentage for a server"""
        if server_name not in self.server_stats:
            return 100.0

        current_time = time.time()
        stats = self.server_stats[server_name]
        uptime_start = stats.get("uptime_start", current_time)
        downtime_periods = stats.get("downtime_periods", [])

        total_duration = current_time - uptime_start
        if total_duration <= 0:
            return 100.0

        total_downtime = sum(
            (period["end"] or current_time) - period["start"]
            for period in downtime_periods
        )

        uptime_percentage = ((total_duration - total_downtime) / total_duration) * 100
        return max(0, min(100, uptime_percentage))

    def get_algorithm_comparison_stats(self):
        """Get comparative statistics for all algorithms used"""
        comparison = {}

        for algorithm, stats in self.algorithm_performance_history.items():
            if stats["total_requests"] > 0:
                success_rate = (
                    stats["successful_requests"] / stats["total_requests"]
                ) * 100
                avg_server_utilization = (
                    np.mean(stats["server_utilization"])
                    if stats["server_utilization"]
                    else 0
                )
                avg_load_variance = (
                    np.mean(stats["load_distribution_variance"])
                    if stats["load_distribution_variance"]
                    else 0
                )

                comparison[algorithm] = {
                    "success_rate": success_rate,
                    "total_requests": stats["total_requests"],
                    "avg_server_utilization": avg_server_utilization,
                    "load_distribution_efficiency": 1.0 / (1.0 + avg_load_variance),
                    "response_time": stats.get("avg_response_time", 0),
                }

        return comparison

    def get_traffic_pattern_analysis(self):
        """Get analysis of traffic patterns and their effectiveness"""
        analysis = {}

        for pattern_name, pattern_stats in self.traffic_analytics[
            "pattern_efficiency"
        ].items():
            if pattern_stats["total_requests"] > 0:
                analysis[pattern_name] = {
                    "total_requests": pattern_stats["total_requests"],
                    "success_rate": pattern_stats["success_rate"],
                    "avg_response_time": pattern_stats["avg_response_time"],
                    "peak_concurrent_users": self.traffic_analytics[
                        "peak_concurrent_users"
                    ],
                    "burst_frequency": self.traffic_analytics.get("burst_frequency", 0),
                }

        return analysis
