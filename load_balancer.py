import pygame
import random
import time
from enum import Enum
from collections import deque
import numpy as np


class LoadBalancingAlgorithm(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RESOURCE_BASED = "resource_based"
    RANDOM = "random"
    POWER_OF_TWO = "power_of_two"


class LoadBalancer:
    def __init__(self, x, y, algorithm=LoadBalancingAlgorithm.LEAST_CONNECTIONS):
        self.x = x
        self.y = y
        self.servers = []
        self.algorithm = algorithm
        self.color = (255, 100, 100)
        self.size = 200

        self.round_robin_index = 0
        self.weighted_round_robin_current = 0
        self.weighted_servers_list = []

        self.total_requests_received = 0
        self.total_requests_routed = 0
        self.dropped_requests = 0
        self.algorithm_switch_count = 0
        self.last_algorithm_switch = 0

        self.request_history = deque(maxlen=100)
        self.routing_decisions = deque(maxlen=50)

        self.health_check_interval = 1.0
        self.last_health_check = time.time()

        self.adaptive_mode = False
        self.performance_window = deque(maxlen=20)
        self.last_performance_eval = time.time()

    def set_servers(self, servers):
        """Set the list of servers and initialize weighted list"""
        self.servers = servers
        self._rebuild_weighted_list()

    def _rebuild_weighted_list(self):
        """Rebuild weighted server list for weighted round robin"""
        self.weighted_servers_list = []
        for server in self.servers:
            if hasattr(server, "weight"):
                self.weighted_servers_list.extend([server] * server.weight)
            else:
                self.weighted_servers_list.append(server)

    def get_healthy_servers(self):
        """Get list of healthy servers that can accept requests"""
        return [s for s in self.servers if not s.is_overloaded()]

    def assign_server(self, cpu_requirement=None, memory_requirement=None):
        """Assign server using the current algorithm with optional resource requirements"""
        self.total_requests_received += 1

        if cpu_requirement is None:
            cpu_requirement = random.uniform(0.2, 1.5)
        if memory_requirement is None:
            memory_requirement = random.uniform(0.1, 1.0)

        request_info = {
            "timestamp": time.time(),
            "cpu_req": cpu_requirement,
            "memory_req": memory_requirement,
            "algorithm": self.algorithm.value,
        }
        self.request_history.append(request_info)

        server = None
        routing_method = None

        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            server, routing_method = self._round_robin_assignment(
                cpu_requirement, memory_requirement
            )
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            server, routing_method = self._least_connections_assignment(
                cpu_requirement, memory_requirement
            )
        elif self.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            server, routing_method = self._weighted_round_robin_assignment(
                cpu_requirement, memory_requirement
            )
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
            server, routing_method = self._least_response_time_assignment(
                cpu_requirement, memory_requirement
            )
        elif self.algorithm == LoadBalancingAlgorithm.RESOURCE_BASED:
            server, routing_method = self._resource_based_assignment(
                cpu_requirement, memory_requirement
            )
        elif self.algorithm == LoadBalancingAlgorithm.RANDOM:
            server, routing_method = self._random_assignment(
                cpu_requirement, memory_requirement
            )
        elif self.algorithm == LoadBalancingAlgorithm.POWER_OF_TWO:
            server, routing_method = self._power_of_two_assignment(
                cpu_requirement, memory_requirement
            )

        decision = {
            "timestamp": time.time(),
            "algorithm": self.algorithm.value,
            "method": routing_method,
            "server_id": getattr(server, "name", "None") if server else "None",
            "success": server is not None,
        }
        self.routing_decisions.append(decision)

        if server:
            self.total_requests_routed += 1
            return server
        else:
            self.dropped_requests += 1
            return None

    def _round_robin_assignment(self, cpu_req, memory_req):
        """Round robin server selection"""
        healthy_servers = self.get_healthy_servers()
        if not healthy_servers:
            return None, "no_healthy_servers"

        attempts = 0
        while attempts < len(healthy_servers):
            server = healthy_servers[self.round_robin_index % len(healthy_servers)]
            self.round_robin_index = (self.round_robin_index + 1) % len(healthy_servers)

            if server.can_accept_request(cpu_req, memory_req):
                return server, "round_robin_success"
            attempts += 1

        return None, "round_robin_all_full"

    def _least_connections_assignment(self, cpu_req, memory_req):
        """Least connections server selection"""
        available_servers = [
            s
            for s in self.get_healthy_servers()
            if s.can_accept_request(cpu_req, memory_req)
        ]

        if not available_servers:
            return None, "no_available_servers"

        best_server = min(available_servers, key=lambda s: s.active_connections)
        return best_server, "least_connections_success"

    def _weighted_round_robin_assignment(self, cpu_req, memory_req):
        """Weighted round robin server selection"""
        if not self.weighted_servers_list:
            self._rebuild_weighted_list()

        available_weighted = [
            s
            for s in self.weighted_servers_list
            if not s.is_overloaded() and s.can_accept_request(cpu_req, memory_req)
        ]

        if not available_weighted:
            return None, "no_weighted_available"

        server = available_weighted[
            self.weighted_round_robin_current % len(available_weighted)
        ]
        self.weighted_round_robin_current = (
            self.weighted_round_robin_current + 1
        ) % len(available_weighted)

        return server, "weighted_round_robin_success"

    def _least_response_time_assignment(self, cpu_req, memory_req):
        """Least response time server selection"""
        available_servers = [
            s
            for s in self.get_healthy_servers()
            if s.can_accept_request(cpu_req, memory_req)
        ]

        if not available_servers:
            return None, "no_available_servers"

        best_server = min(available_servers, key=lambda s: s.avg_response_time)
        return best_server, "least_response_time_success"

    def _resource_based_assignment(self, cpu_req, memory_req):
        """Resource-based server selection using load score"""
        available_servers = [
            s
            for s in self.get_healthy_servers()
            if s.can_accept_request(cpu_req, memory_req)
        ]

        if not available_servers:
            return None, "no_available_servers"

        best_server = min(available_servers, key=lambda s: s.load_score)
        return best_server, "resource_based_success"

    def _random_assignment(self, cpu_req, memory_req):
        """Random server selection"""
        available_servers = [
            s
            for s in self.get_healthy_servers()
            if s.can_accept_request(cpu_req, memory_req)
        ]

        if not available_servers:
            return None, "no_available_servers"

        server = random.choice(available_servers)
        return server, "random_success"

    def _power_of_two_assignment(self, cpu_req, memory_req):
        """Power of two choices algorithm"""
        healthy_servers = [
            s
            for s in self.get_healthy_servers()
            if s.can_accept_request(cpu_req, memory_req)
        ]

        if not healthy_servers:
            return None, "no_available_servers"

        if len(healthy_servers) == 1:
            return healthy_servers[0], "power_of_two_single"

        server1, server2 = random.sample(healthy_servers, 2)

        if server1.active_connections <= server2.active_connections:
            return server1, "power_of_two_choice1"
        else:
            return server2, "power_of_two_choice2"

    def switch_algorithm(self, new_algorithm):
        """Switch to a different load balancing algorithm"""
        if new_algorithm != self.algorithm:
            self.algorithm = new_algorithm
            self.algorithm_switch_count += 1
            self.last_algorithm_switch = time.time()

            self.round_robin_index = 0
            self.weighted_round_robin_current = 0
            self._rebuild_weighted_list()

    def evaluate_performance(self):
        """Evaluate current algorithm performance"""
        current_time = time.time()

        recent_requests = [
            r for r in self.request_history if current_time - r["timestamp"] < 10.0
        ]

        if not recent_requests:
            return None

        total_recent = len(recent_requests)
        recent_decisions = [
            d for d in self.routing_decisions if current_time - d["timestamp"] < 10.0
        ]
        successful_recent = len([d for d in recent_decisions if d["success"]])
        success_rate = successful_recent / total_recent if total_recent > 0 else 0

        avg_load = np.mean(
            [s.load_score for s in self.servers if s.load_score != float("inf")]
        )

        loads = [s.load_score for s in self.servers if s.load_score != float("inf")]
        load_variance = np.var(loads) if loads else 0

        performance = {
            "success_rate": success_rate,
            "avg_load": avg_load,
            "load_variance": load_variance,
            "total_requests": total_recent,
            "algorithm": self.algorithm.value,
            "timestamp": current_time,
        }

        self.performance_window.append(performance)
        return performance

    def get_algorithm_stats(self):
        """Get comprehensive statistics about algorithm performance"""
        if not self.routing_decisions:
            return {}

        current_time = time.time()
        recent_decisions = [
            d for d in self.routing_decisions if current_time - d["timestamp"] < 30.0
        ]

        if not recent_decisions:
            return {}

        method_counts = {}
        for decision in recent_decisions:
            method = decision["method"]
            method_counts[method] = method_counts.get(method, 0) + 1

        successful = len([d for d in recent_decisions if d["success"]])
        success_rate = successful / len(recent_decisions) if recent_decisions else 0

        return {
            "algorithm": self.algorithm.value,
            "success_rate": success_rate,
            "total_decisions": len(recent_decisions),
            "method_breakdown": method_counts,
            "requests_received": self.total_requests_received,
            "requests_routed": self.total_requests_routed,
            "dropped_requests": self.dropped_requests,
        }

    def draw(self, screen):

        base_color = self.color

        pulse = abs(np.sin(time.time() * 3)) * 0.3 + 0.7
        color = tuple(int(c * pulse) for c in base_color)

        rect = pygame.Rect(
            self.x - self.size // 2, self.y - self.size // 2, self.size, self.size
        )
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (255, 255, 255, 50), rect, 3)

        font = pygame.font.Font(None, 16)
        alg_text = font.render(self.algorithm.value.upper(), True, (255, 255, 255))
        alg_rect = alg_text.get_rect(center=(self.x, self.y - 5))
        screen.blit(alg_text, alg_rect)

        req_text = font.render(
            f"Req: {self.total_requests_received}", True, (255, 255, 255)
        )
        req_rect = req_text.get_rect(center=(self.x, self.y + 8))
        screen.blit(req_text, req_rect)
