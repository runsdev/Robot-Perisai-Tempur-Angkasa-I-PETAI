import pygame
import random
import time
from enum import Enum
from collections import deque
import numpy as np


class ServerStatus(Enum):
    HEALTHY = "healthy"
    OVERLOADED = "overloaded"
    FAILED = "failed"
    DEGRADED = "degraded"


class ServerType(Enum):
    STANDARD = "standard"
    HIGH_PERFORMANCE = "high_performance"
    MEMORY_OPTIMIZED = "memory_optimized"
    CPU_OPTIMIZED = "cpu_optimized"


class UpstreamServer:
    def __init__(self, x, y, name, server_type=ServerType.STANDARD, weight=1):
        self.x = x
        self.y = y
        self.name = name
        self.weight = weight
        self.server_type = server_type

        self._set_server_specs()

        self.active_connections = 0
        self.total_requests = 0
        self.processing_requests = []
        self.request_queue = deque()

        self.current_cpu_usage = 0.0
        self.current_memory_usage = 0.0

        self.status = ServerStatus.HEALTHY
        self.failure_probability = 0.0001
        self.recovery_time = 0
        self.last_failure_time = 0

        self.response_times = deque(maxlen=100)
        self.total_response_time = 0.0
        self.avg_response_time = 0.0
        self.last_performance_update = time.time()

        self.color = (100, 255, 100)
        self.size = 60
        self.pulse_intensity = 0

        self.load_history = deque(maxlen=50)
        self.utilization_threshold = 0.8

    def _set_server_specs(self):
        """Set server specifications based on server type"""
        specs = {
            ServerType.STANDARD: {
                "cpu_cores": 4,
                "memory_gb": 8,
                "base_processing_speed": 1.0,
            },
            ServerType.HIGH_PERFORMANCE: {
                "cpu_cores": 8,
                "memory_gb": 16,
                "base_processing_speed": 1.5,
            },
            ServerType.MEMORY_OPTIMIZED: {
                "cpu_cores": 4,
                "memory_gb": 32,
                "base_processing_speed": 0.9,
            },
            ServerType.CPU_OPTIMIZED: {
                "cpu_cores": 12,
                "memory_gb": 8,
                "base_processing_speed": 1.3,
            },
        }

        spec = specs[self.server_type]
        self.cpu_cores = spec["cpu_cores"]
        self.memory_gb = spec["memory_gb"]
        self.base_processing_speed = spec["base_processing_speed"]

    @property
    def cpu_utilization(self):
        """Calculate CPU utilization percentage"""
        return min(100.0, (self.current_cpu_usage / self.cpu_cores) * 100)

    @property
    def memory_utilization(self):
        """Calculate memory utilization percentage"""
        return min(100.0, (self.current_memory_usage / self.memory_gb) * 100)

    @property
    def load_score(self):
        """Calculate comprehensive load score for resource-based load balancing"""
        if self.status != ServerStatus.HEALTHY:
            return float("inf")

        cpu_weight = 0.5
        memory_weight = 0.4
        response_weight = 0.1

        cpu_score = self.cpu_utilization / 100
        memory_score = self.memory_utilization / 100

        response_score = (
            min(1.0, self.avg_response_time / 10.0) if self.avg_response_time > 0 else 0
        )

        return (
            cpu_weight * cpu_score
            + memory_weight * memory_score
            + response_weight * response_score
        )

    def can_accept_request(self, cpu_requirement=0.5, memory_requirement=0.1):
        """Check if server can accept new request with resource requirements"""
        if self.status not in [ServerStatus.HEALTHY, ServerStatus.DEGRADED]:
            return False

        cpu_available = self.cpu_cores - self.current_cpu_usage
        memory_available = self.memory_gb - self.current_memory_usage

        return (
            cpu_available >= cpu_requirement and memory_available >= memory_requirement
        )

    def add_connection(
        self, cpu_requirement=0.5, memory_requirement=0.1, processing_time=3.0
    ):
        """Add connection with resource requirements and processing time"""
        if not self.can_accept_request(cpu_requirement, memory_requirement):
            return False

        self.active_connections += 1
        self.total_requests += 1
        self.current_cpu_usage += cpu_requirement
        self.current_memory_usage += memory_requirement

        request_data = {
            "start_time": time.time(),
            "cpu_requirement": cpu_requirement,
            "memory_requirement": memory_requirement,
            "processing_time": processing_time * self.base_processing_speed,
            "remaining_time": processing_time * self.base_processing_speed,
        }
        self.processing_requests.append(request_data)

        return True

    def remove_connection(self):
        """Remove connection and free resources - only used for manual cleanup"""

        pass

    def update(self):
        """Update server state, process requests, and handle failures"""
        current_time = time.time()

        completed_requests = []
        for i, request in enumerate(self.processing_requests):
            request["remaining_time"] -= 1 / 60

            if request["remaining_time"] <= 0:

                response_time = current_time - request["start_time"]
                self.response_times.append(response_time)
                self.total_response_time += response_time

                self.current_cpu_usage = max(
                    0, self.current_cpu_usage - request["cpu_requirement"]
                )
                self.current_memory_usage = max(
                    0, self.current_memory_usage - request["memory_requirement"]
                )

                completed_requests.append(i)

        for i in sorted(completed_requests, reverse=True):
            del self.processing_requests[i]

        self.active_connections = len(self.processing_requests)

        self.current_cpu_usage = max(0, self.current_cpu_usage)
        self.current_memory_usage = max(0, self.current_memory_usage)

        if self.response_times:
            self.avg_response_time = np.mean(self.response_times)

        self._update_status()

        self._simulate_failures_and_recovery(current_time)

        current_load = self.load_score if self.load_score != float("inf") else 1.0
        self.load_history.append(current_load)

        self.pulse_intensity = (self.pulse_intensity + 0.1) % (2 * 3.14159)

    def _update_status(self):
        """Update server status based on current load and utilization"""
        if self.status == ServerStatus.FAILED:
            return

        cpu_util = self.cpu_utilization
        memory_util = self.memory_utilization

        if cpu_util > 95 or memory_util > 95:
            self.status = ServerStatus.OVERLOADED
            self.failure_probability = 0.001
        elif cpu_util > 80 or memory_util > 80:
            self.status = ServerStatus.DEGRADED
            self.failure_probability = 0.0005
        else:
            self.status = ServerStatus.HEALTHY
            self.failure_probability = 0.0001

    def _simulate_failures_and_recovery(self, current_time):
        """Simulate random server failures and recovery"""
        if self.status == ServerStatus.FAILED:

            if self.recovery_time > 0:
                self.recovery_time -= 1 / 60
            else:
                self.status = ServerStatus.HEALTHY
                self.current_cpu_usage = 0
                self.current_memory_usage = 0
                self.active_connections = 0
                self.processing_requests.clear()
        else:

            if random.random() < self.failure_probability:
                self.status = ServerStatus.FAILED
                self.recovery_time = random.uniform(5, 15)
                self.last_failure_time = current_time

                self.current_cpu_usage = 0
                self.current_memory_usage = 0
                self.active_connections = 0
                self.processing_requests.clear()

    def is_overloaded(self):
        return self.status in [ServerStatus.OVERLOADED, ServerStatus.FAILED]

    def get_server_info(self):
        """Get comprehensive server information"""
        return {
            "name": self.name,
            "type": self.server_type.value,
            "status": self.status.value,
            "connections": self.active_connections,
            "cpu_usage": f"{self.cpu_utilization:.1f}%",
            "memory_usage": f"{self.memory_utilization:.1f}%",
            "load_score": f"{self.load_score:.3f}",
            "avg_response_time": f"{self.avg_response_time:.2f}s",
            "total_requests": self.total_requests,
        }

    def draw(self, screen, font):

        base_colors = {
            ServerStatus.HEALTHY: (100, 255, 100),
            ServerStatus.DEGRADED: (255, 255, 100),
            ServerStatus.OVERLOADED: (255, 150, 50),
            ServerStatus.FAILED: (255, 50, 50),
        }

        base_color = base_colors[self.status]

        if self.status == ServerStatus.FAILED:
            pulse = abs(np.sin(self.pulse_intensity)) * 100
            color = (min(255, base_color[0] + pulse), base_color[1], base_color[2])
        else:

            load_intensity = (
                min(1.0, self.load_score) if self.load_score != float("inf") else 1.0
            )
            intensity_factor = 0.5 + (load_intensity * 0.5)
            color = tuple(int(c * intensity_factor) for c in base_color)

        pygame.draw.circle(screen, color, (self.x, self.y), self.size // 2)

        border_colors = {
            ServerType.STANDARD: (255, 255, 255),
            ServerType.HIGH_PERFORMANCE: (255, 215, 0),
            ServerType.MEMORY_OPTIMIZED: (0, 191, 255),
            ServerType.CPU_OPTIMIZED: (255, 20, 147),
        }
        border_color = border_colors[self.server_type]
        pygame.draw.circle(screen, border_color, (self.x, self.y), self.size // 2, 3)

        name_text = font.render(
            f"{self.name} ({self.server_type.value[:4].upper()})", True, (255, 255, 255)
        )
        name_rect = name_text.get_rect(
            left=self.x + self.size // 2 + 10, centery=self.y - 15
        )
        screen.blit(name_text, name_rect)

        metrics = [
            f"Conn: {self.active_connections}",
            f"CPU: {self.cpu_utilization:.1f}%",
            f"Mem: {self.memory_utilization:.1f}%",
            (
                f"Load: {self.load_score:.2f}"
                if self.load_score != float("inf")
                else "Load: inf"
            ),
        ]

        for i, metric in enumerate(metrics):
            metric_text = font.render(metric, True, (255, 255, 255))
            metric_rect = metric_text.get_rect(
                left=self.x + self.size // 2 + 10, centery=self.y + (i * 12) - 5
            )
            screen.blit(metric_text, metric_rect)

        additional_info = [
            f"Total: {self.total_requests}",
            f"Resp: {self.avg_response_time:.2f}s",
            f"Status: {self.status.value}",
        ]

        for i, info in enumerate(additional_info):
            color = (200, 200, 200) if i < 2 else (150, 150, 255)
            info_text = font.render(info, True, color)
            info_rect = info_text.get_rect(center=(self.x, self.y + 40 + (i * 15)))
            screen.blit(info_text, info_rect)

        bar_width = 60
        bar_height = 4

        cpu_bar_rect = pygame.Rect(
            self.x - bar_width // 2, self.y + 85, bar_width, bar_height
        )
        pygame.draw.rect(screen, (100, 100, 100), cpu_bar_rect)
        cpu_fill_width = int((self.cpu_utilization / 100) * bar_width)
        cpu_fill_rect = pygame.Rect(
            self.x - bar_width // 2, self.y + 85, cpu_fill_width, bar_height
        )
        cpu_color = (255, 100, 100) if self.cpu_utilization > 80 else (100, 255, 100)
        pygame.draw.rect(screen, cpu_color, cpu_fill_rect)

        mem_bar_rect = pygame.Rect(
            self.x - bar_width // 2, self.y + 92, bar_width, bar_height
        )
        pygame.draw.rect(screen, (100, 100, 100), mem_bar_rect)
        mem_fill_width = int((self.memory_utilization / 100) * bar_width)
        mem_fill_rect = pygame.Rect(
            self.x - bar_width // 2, self.y + 92, mem_fill_width, bar_height
        )
        mem_color = (255, 100, 100) if self.memory_utilization > 80 else (100, 255, 100)
        pygame.draw.rect(screen, mem_color, mem_fill_rect)
