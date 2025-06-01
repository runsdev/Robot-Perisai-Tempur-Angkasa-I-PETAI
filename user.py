import pygame
import math
import random
import time
from enum import Enum


class UserType(Enum):
    LIGHT = "light"
    STANDARD = "standard"
    HEAVY = "heavy"
    BURST = "burst"
    NAUGHTY = "naughty"


class RequestPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class AttackType(Enum):
    """Different types of attacks that naughty users can perform"""

    DOS = "dos"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SLOWLORIS = "slowloris"
    AMPLIFICATION = "amplification"
    PRIORITY_ABUSE = "priority_abuse"


class User:
    def __init__(self, x, y, load_balancer, user_type=None):
        self.x = float(x)
        self.y = float(y)
        self.load_balancer = load_balancer
        self.target_server = None
        self.state = "moving_to_lb"
        self.previous_state = "moving_to_lb"
        self.speed = 2.0
        self.radius = 5
        self.failed = False
        self.timeout_exit = False
        self.screen_height = 800

        self.user_type = user_type or self._generate_user_type()

        if self.user_type == UserType.NAUGHTY:
            self.attack_type = self._generate_attack_type()
            self.attack_intensity = random.uniform(0.5, 3.0)
            self.spawn_count = 0
            self.max_spawn_count = random.randint(1, 3)
            self.attack_duration = random.uniform(5.0, 15.0)
            self.attack_start_time = 0
            self.is_attacking = False
            self.spawned_requests = []
            self.stealth_mode = random.choice([True, False])
        else:
            self.attack_type = None
            self.attack_intensity = 0
            self.spawn_count = 0
            self.max_spawn_count = 0
            self.attack_duration = 0
            self.attack_start_time = 0
            self.is_attacking = False
            self.spawned_requests = []
            self.stealth_mode = False

        self._set_user_characteristics()

        self.cpu_requirement = self._generate_cpu_requirement()
        self.memory_requirement = self._generate_memory_requirement()
        self.priority = self._generate_priority()
        self.processing_time = self._generate_processing_time()

        self.arrival_time = time.time()
        self.waiting_time = 0
        self.max_waiting_time = self._get_max_waiting_time()
        self.processing_start_time = 0
        self.completion_time = 0
        self.processing_elapsed = 0
        self.load_balancer_reached_time = 0

        self.color = self._get_user_color()
        self.pulse_intensity = 0

        self.retry_count = 0
        self.max_retries = 3 if self.priority.value >= 3 else 1

        self.request_id = random.randint(10000, 99999)

        self.is_simulation_user = False
        self.simulation_id = None
        self.unique_id = None

    def _generate_user_type(self):
        """Generate user type based on probability distribution"""
        weights = [0.39, 0.3, 0.18, 0.12, 0.01]
        return random.choices(list(UserType), weights=weights)[0]

    def _generate_attack_type(self):
        """Generate attack type for naughty users"""
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        return random.choices(list(AttackType), weights=weights)[0]

    def _set_user_characteristics(self):
        """Set user characteristics based on type"""
        type_configs = {
            UserType.LIGHT: {
                "base_speed": 2.5,
                "patience_multiplier": 0.8,
                "retry_probability": 0.3,
            },
            UserType.STANDARD: {
                "base_speed": 2.0,
                "patience_multiplier": 1.0,
                "retry_probability": 0.5,
            },
            UserType.HEAVY: {
                "base_speed": 1.5,
                "patience_multiplier": 1.5,
                "retry_probability": 0.8,
            },
            UserType.BURST: {
                "base_speed": 3.0,
                "patience_multiplier": 0.6,
                "retry_probability": 0.9,
            },
            UserType.NAUGHTY: {
                "base_speed": 2.5 if self.stealth_mode else 4.0,
                "patience_multiplier": 0.1,
                "retry_probability": 0.95,
            },
        }

        config = type_configs[self.user_type]
        self.speed = config["base_speed"] + random.uniform(-0.5, 0.5)
        self.patience_multiplier = config["patience_multiplier"]
        self.retry_probability = config["retry_probability"]

    def _generate_cpu_requirement(self):
        """Generate CPU requirement based on user type"""
        if self.user_type == UserType.NAUGHTY:
            if self.attack_type == AttackType.RESOURCE_EXHAUSTION:
                return random.uniform(2.0, 5.0)
            elif self.attack_type == AttackType.DOS:
                return random.uniform(0.1, 0.3)
            elif self.attack_type == AttackType.SLOWLORIS:
                return random.uniform(0.05, 0.15)
            elif self.stealth_mode:
                return random.uniform(0.2, 0.8)
            else:
                return random.uniform(1.0, 3.0)

        type_ranges = {
            UserType.LIGHT: (0.1, 0.5),
            UserType.STANDARD: (0.3, 1.0),
            UserType.HEAVY: (0.8, 2.0),
            UserType.BURST: (0.2, 0.8),
        }
        min_cpu, max_cpu = type_ranges[self.user_type]
        return random.uniform(min_cpu, max_cpu)

    def _generate_memory_requirement(self):
        """Generate memory requirement based on user type"""
        if self.user_type == UserType.NAUGHTY:
            if self.attack_type == AttackType.RESOURCE_EXHAUSTION:
                return random.uniform(1.5, 4.0)
            elif self.attack_type == AttackType.AMPLIFICATION:
                return random.uniform(0.5, 1.5)
            elif self.stealth_mode:
                return random.uniform(0.1, 0.4)
            else:
                return random.uniform(0.8, 2.0)

        type_ranges = {
            UserType.LIGHT: (0.05, 0.2),
            UserType.STANDARD: (0.1, 0.5),
            UserType.HEAVY: (0.3, 1.5),
            UserType.BURST: (0.08, 0.3),
        }
        min_mem, max_mem = type_ranges[self.user_type]
        return random.uniform(min_mem, max_mem)

    def _generate_priority(self):
        """Generate request priority based on user type"""
        if self.user_type == UserType.NAUGHTY:
            if self.attack_type == AttackType.PRIORITY_ABUSE:
                return RequestPriority.CRITICAL
            elif self.stealth_mode:
                return random.choices(
                    list(RequestPriority), weights=[0.4, 0.4, 0.15, 0.05]
                )[0]
            else:
                return random.choices(
                    list(RequestPriority), weights=[0.1, 0.2, 0.3, 0.4]
                )[0]

        if self.user_type == UserType.BURST:
            return random.choices(list(RequestPriority), weights=[0.1, 0.3, 0.4, 0.2])[
                0
            ]
        elif self.user_type == UserType.HEAVY:
            return random.choices(list(RequestPriority), weights=[0.2, 0.4, 0.3, 0.1])[
                0
            ]
        else:
            return random.choices(
                list(RequestPriority), weights=[0.3, 0.5, 0.15, 0.05]
            )[0]

    def _generate_processing_time(self):
        """Generate processing time based on user type and requirements"""
        if self.user_type == UserType.NAUGHTY:
            if self.attack_type == AttackType.SLOWLORIS:
                return random.uniform(10.0, 30.0)
            elif self.attack_type == AttackType.DOS:
                return random.uniform(0.1, 0.5)
            elif self.attack_type == AttackType.RESOURCE_EXHAUSTION:
                return random.uniform(8.0, 20.0)
            elif self.stealth_mode:
                return random.uniform(2.0, 5.0)
            else:
                return random.uniform(5.0, 15.0)

        base_times = {
            UserType.LIGHT: 0.5,
            UserType.STANDARD: 1.5,
            UserType.HEAVY: 3.0,
            UserType.BURST: 1.0,
        }

        base_time = base_times[self.user_type]

        resource_factor = (self.cpu_requirement + self.memory_requirement) / 2
        priority_factor = 1.0 / self.priority.value

        final_time = base_time * resource_factor * priority_factor
        return max(0.5, final_time + random.uniform(-1.0, 1.0))

    def _get_max_waiting_time(self):
        """Get maximum waiting time based on user type and priority"""
        if self.user_type == UserType.NAUGHTY:
            return 1.0

        base_waiting = {
            UserType.LIGHT: 3.0,
            UserType.STANDARD: 5.0,
            UserType.HEAVY: 8.0,
            UserType.BURST: 2.0,
        }

        base = base_waiting[self.user_type] * self.patience_multiplier
        priority_bonus = self.priority.value * 1.5

        return base + priority_bonus

    def _get_user_color(self):
        """Get color based on user type and priority"""
        if self.user_type == UserType.NAUGHTY:
            if self.stealth_mode:

                return (120, 180, 255)
            else:

                attack_colors = {
                    AttackType.DOS: (255, 0, 0),
                    AttackType.RESOURCE_EXHAUSTION: (150, 0, 150),
                    AttackType.SLOWLORIS: (255, 100, 0),
                    AttackType.AMPLIFICATION: (255, 0, 150),
                    AttackType.PRIORITY_ABUSE: (100, 0, 0),
                }
                return attack_colors.get(self.attack_type, (255, 0, 0))

        type_colors = {
            UserType.LIGHT: (150, 200, 255),
            UserType.STANDARD: (100, 150, 255),
            UserType.HEAVY: (50, 100, 200),
            UserType.BURST: (255, 150, 50),
        }

        base_color = type_colors[self.user_type]

        priority_multiplier = 0.7 + (self.priority.value * 0.1)
        return tuple(min(255, int(c * priority_multiplier)) for c in base_color)

    def set_screen_height(self, height):
        self.screen_height = height

    def _execute_attack_behavior(self):
        """Execute specific attack behaviors based on attack type"""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_start_time = time.time()

        current_time = time.time()
        attack_elapsed = current_time - self.attack_start_time

        if attack_elapsed >= self.attack_duration:
            if (
                self.attack_type == AttackType.AMPLIFICATION
                and self.spawn_count < self.max_spawn_count
            ):

                pass
            else:
                self.state = "done"
                return []

        new_users = []

        if self.attack_type == AttackType.DOS:

            if random.random() < self.attack_intensity * 0.3:
                new_user = self._create_attack_clone()
                new_users.append(new_user)

        elif self.attack_type == AttackType.AMPLIFICATION:

            if (
                self.spawn_count < self.max_spawn_count
                and random.random() < self.attack_intensity * 0.1
            ):

                spawn_this_round = random.randint(2, 4)
                for _ in range(spawn_this_round):
                    if self.spawn_count < self.max_spawn_count:
                        new_user = self._create_attack_clone()
                        new_users.append(new_user)
                        self.spawn_count += 1

        elif self.attack_type == AttackType.SLOWLORIS:

            pass

        elif self.attack_type == AttackType.RESOURCE_EXHAUSTION:

            if random.random() < self.attack_intensity * 0.05:
                new_user = self._create_attack_clone()
                new_user.cpu_requirement *= 1.5
                new_user.memory_requirement *= 1.5
                new_users.append(new_user)

        elif self.attack_type == AttackType.PRIORITY_ABUSE:

            if random.random() < self.attack_intensity * 0.2:
                new_user = self._create_attack_clone()
                new_user.priority = RequestPriority.CRITICAL
                new_users.append(new_user)

        return new_users

    def _create_attack_clone(self):
        """Create a clone of this attack user with slight variations"""

        new_x = self.load_balancer.x + random.uniform(-50, 50)
        new_y = random.uniform(50, 150)

        clone = User(new_x, new_y, self.load_balancer, UserType.NAUGHTY)
        clone.attack_type = self.attack_type
        clone.stealth_mode = self.stealth_mode
        clone.attack_intensity = self.attack_intensity * random.uniform(0.8, 1.2)

        if not self.stealth_mode:
            clone.cpu_requirement = self.cpu_requirement * random.uniform(0.8, 1.2)
            clone.memory_requirement = self.memory_requirement * random.uniform(
                0.8, 1.2
            )
            clone.processing_time = self.processing_time * random.uniform(0.9, 1.1)

        return clone

    def update(self):

        if self.user_type == UserType.NAUGHTY and self.state == "at_lb":
            new_users = self._execute_attack_behavior()
            if new_users:

                return new_users

        if self.state == "moving_to_lb":
            return self._move_to_target(
                self.load_balancer.x, self.load_balancer.y, "at_lb"
            )

        elif self.state == "at_lb":

            if (
                hasattr(self, "load_balancer_reached_time")
                and self.load_balancer_reached_time == 0
            ):
                self.load_balancer_reached_time = time.time()

            self.target_server = self.load_balancer.assign_server(
                self.cpu_requirement, self.memory_requirement
            )

            if self.target_server:
                success = self.target_server.add_connection(
                    self.cpu_requirement, self.memory_requirement, self.processing_time
                )
                if success:
                    self.state = "moving_to_server"
                    self.processing_start_time = time.time()
                else:

                    self._handle_server_rejection()
            else:

                self.waiting_time += 1 / 60
                if self.waiting_time >= self.max_waiting_time:
                    self._handle_timeout()
            return True

        elif self.state == "moving_to_server":
            return self._move_to_target(
                self.target_server.x, self.target_server.y, "processing"
            )

        elif self.state == "processing":
            self.processing_elapsed += 1 / 60

            if (
                self.user_type == UserType.NAUGHTY
                and self.attack_type == AttackType.SLOWLORIS
            ):

                if random.random() < 0.1:
                    self.processing_time += 1.0

            if self.processing_elapsed >= self.processing_time:

                if hasattr(self.target_server, "remove_connection"):
                    self.target_server.remove_connection()
                self.completion_time = time.time()
                self.state = "done"
            return True

        elif self.state == "retry":

            self.waiting_time += 1 / 60
            retry_delay = 0.1 if self.user_type == UserType.NAUGHTY else 1.0
            if self.waiting_time >= retry_delay:
                self.waiting_time = 0
                self.state = "at_lb"
            return True

        elif self.state == "timeout_exit":

            return self._move_to_target(self.x, self.screen_height + 50, "done")

        elif self.state == "done":
            return False

        return True

    def _handle_server_rejection(self):
        """Handle when a server rejects the request"""
        self.retry_count += 1

        if (
            self.retry_count < self.max_retries
            and random.random() < self.retry_probability
        ):

            self.state = "retry"
            self.waiting_time = 0
        else:

            self._handle_timeout()

    def _handle_timeout(self):
        """Handle request timeout"""
        if not self.failed:
            self.failed = True
            self.timeout_exit = True
            self.state = "timeout_exit"
            self.completion_time = time.time()

    def _move_to_target(self, target_x, target_y, next_state):

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < self.speed:
            self.x = target_x
            self.y = target_y
            self.state = next_state
            return True

        self.x += (dx / distance) * self.speed
        self.y += (dy / distance) * self.speed
        return True

    def get_response_time(self):
        """Calculate total response time"""
        if self.completion_time > 0:
            return self.completion_time - self.arrival_time
        return time.time() - self.arrival_time

    def get_user_info(self):
        """Get comprehensive user information"""
        info = {
            "id": self.request_id,
            "type": self.user_type.value,
            "priority": self.priority.value,
            "cpu_req": f"{self.cpu_requirement:.2f}",
            "memory_req": f"{self.memory_requirement:.2f}",
            "processing_time": f"{self.processing_time:.2f}s",
            "state": self.state,
            "response_time": f"{self.get_response_time():.2f}s",
            "retries": self.retry_count,
            "failed": self.failed,
        }

        if self.user_type == UserType.NAUGHTY:
            info.update(
                {
                    "attack_type": self.attack_type.value,
                    "attack_intensity": f"{self.attack_intensity:.2f}",
                    "stealth_mode": self.stealth_mode,
                    "spawn_count": self.spawn_count,
                }
            )

        return info

    def draw(self, screen):

        self.pulse_intensity = (self.pulse_intensity + 0.15) % (2 * 3.14159)

        color = self.color

        if self.state == "timeout_exit":
            color = (255, 100, 100)
        elif self.state == "processing":
            if self.user_type == UserType.NAUGHTY:

                pulse = abs(math.sin(self.pulse_intensity * 2)) * 0.5 + 0.5
                color = tuple(int(c * pulse) for c in (255, 50, 50))
            else:

                pulse = abs(math.sin(self.pulse_intensity)) * 0.3 + 0.7
                color = tuple(int(c * pulse) for c in (255, 200, 0))
        elif self.state == "moving_to_server":
            color = (0, 255, 150)
        elif self.state == "at_lb" and self.waiting_time > 0:

            intensity = min(1.0, self.waiting_time / self.max_waiting_time)
            color = (255, int(255 * (1 - intensity)), 0)
        elif self.state == "retry":
            color = (255, 255, 0)

        if self.user_type == UserType.NAUGHTY and not self.stealth_mode:

            aura_radius = int(self.radius * 2.5)
            aura_alpha = int(50 + 30 * abs(math.sin(self.pulse_intensity * 3)))

            aura_surface = pygame.Surface(
                (aura_radius * 2, aura_radius * 2), pygame.SRCALPHA
            )
            aura_color = (*color[:3], aura_alpha)
            pygame.draw.circle(
                aura_surface, aura_color, (aura_radius, aura_radius), aura_radius
            )

            screen.blit(
                aura_surface, (int(self.x - aura_radius), int(self.y - aura_radius))
            )

        size_multiplier = 1.0 + (self.cpu_requirement + self.memory_requirement) / 4
        current_radius = int(self.radius * size_multiplier)

        if self.user_type == UserType.NAUGHTY:
            current_radius = int(current_radius * 1.2)

        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), current_radius)

        priority_colors = {
            RequestPriority.LOW: (100, 100, 100),
            RequestPriority.NORMAL: (255, 255, 255),
            RequestPriority.HIGH: (255, 255, 0),
            RequestPriority.CRITICAL: (255, 0, 0),
        }
        priority_color = priority_colors[self.priority]
        pygame.draw.circle(
            screen,
            priority_color,
            (int(self.x), int(self.y)),
            max(2, current_radius // 3),
        )

        type_indicators = {
            UserType.LIGHT: "L",
            UserType.STANDARD: "S",
            UserType.HEAVY: "H",
            UserType.BURST: "B",
            UserType.NAUGHTY: "ATTACK" if not self.stealth_mode else "NAUGHTY",
        }

        font = pygame.font.Font(None, 16)
        type_text = font.render(type_indicators[self.user_type], True, (255, 255, 255))
        type_rect = type_text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(type_text, type_rect)

        if self.user_type == UserType.NAUGHTY and not self.stealth_mode:
            attack_indicators = {
                AttackType.DOS: "DOS",
                AttackType.RESOURCE_EXHAUSTION: "RES_EXHAUST",
                AttackType.SLOWLORIS: "SLOWLORIS",
                AttackType.AMPLIFICATION: "AMPLIFICATION",
                AttackType.PRIORITY_ABUSE: "PRIORITY_ABUSE",
            }

            attack_text = font.render(
                attack_indicators.get(self.attack_type, "ATTACK"), True, (255, 255, 0)
            )
            attack_rect = attack_text.get_rect(
                center=(int(self.x), int(self.y + current_radius + 10))
            )
            screen.blit(attack_text, attack_rect)

        if self.state == "timeout_exit":

            pygame.draw.line(
                screen,
                (255, 255, 255),
                (int(self.x), int(self.y - 8)),
                (int(self.x), int(self.y + 8)),
                2,
            )
            pygame.draw.line(
                screen,
                (255, 255, 255),
                (int(self.x), int(self.y + 8)),
                (int(self.x - 4), int(self.y + 4)),
                2,
            )
            pygame.draw.line(
                screen,
                (255, 255, 255),
                (int(self.x), int(self.y + 8)),
                (int(self.x + 4), int(self.y + 4)),
                2,
            )

        elif self.state == "at_lb" and self.waiting_time > 0:

            angle = (self.waiting_time / self.max_waiting_time) * 2 * 3.14159
            end_x = self.x + (current_radius + 5) * math.cos(angle - 3.14159 / 2)
            end_y = self.y + (current_radius + 5) * math.sin(angle - 3.14159 / 2)
            pygame.draw.line(
                screen,
                (255, 255, 255),
                (int(self.x), int(self.y)),
                (int(end_x), int(end_y)),
                2,
            )

        elif self.retry_count > 0:

            retry_text = font.render(f"R{self.retry_count}", True, (255, 255, 0))
            retry_rect = retry_text.get_rect(
                center=(int(self.x), int(self.y + current_radius + 8))
            )
            screen.blit(retry_text, retry_rect)

        if (
            self.user_type == UserType.NAUGHTY
            and self.attack_type == AttackType.AMPLIFICATION
            and self.spawn_count > 0
        ):
            spawn_text = font.render(f"x{self.spawn_count}", True, (255, 150, 0))
            spawn_rect = spawn_text.get_rect(
                center=(int(self.x + current_radius + 15), int(self.y))
            )
            screen.blit(spawn_text, spawn_rect)

    def reset_for_new_simulation(self):
        """Reset user state for a new simulation"""
        self.state = "moving_to_lb"
        self.previous_state = "moving_to_lb"
        self.failed = False
        self.timeout_exit = False
        self.arrival_time = time.time()
        self.waiting_time = 0
        self.processing_elapsed = 0
        self.load_balancer_reached_time = 0
        self.completion_time = 0
        self.retry_count = 0
        self.is_attacking = False
        self.spawn_count = 0

        self.user_type = self._generate_user_type()
        if self.user_type == UserType.NAUGHTY:
            self.attack_type = self._generate_attack_type()
            self.attack_intensity = random.uniform(0.5, 3.0)
            self.max_spawn_count = random.randint(1, 3)
            self.attack_duration = random.uniform(5.0, 15.0)
            self.stealth_mode = random.choice([True, False])
        else:
            self.attack_type = None
            self.attack_intensity = 0
            self.max_spawn_count = 0
            self.attack_duration = 0
            self.stealth_mode = False

        self._set_user_characteristics()

    def save_to_report(self, report_file):
        """Save user data to the report file"""
        response_time = self.get_response_time()
        report_line = (
            f"{self.request_id},{self.user_type.value},{self.priority.value},"
            f"{self.cpu_requirement:.2f},{self.memory_requirement:.2f},"
            f"{self.processing_time:.2f},{self.arrival_time:.2f},"
            f"{self.completion_time:.2f},{response_time:.2f},"
            f"{self.retry_count},{int(self.failed)}\n"
        )

        with open(report_file, "a") as f:
            f.write(report_line)
