import time
import numpy as np
import random


class TrafficPattern:
    """Defines different traffic generation patterns"""

    def __init__(
        self, name, base_rate, burst_probability, burst_multiplier, duration=60
    ):
        self.name = name
        self.base_rate = base_rate
        self.burst_probability = burst_probability
        self.burst_multiplier = burst_multiplier
        self.duration = duration
        self.start_time = time.time()

    def get_spawn_rate(self):
        elapsed = time.time() - self.start_time
        cycle_time = elapsed % self.duration

        if self.name == "steady":
            return self.base_rate
        elif self.name == "wave":
            wave_factor = (np.sin(cycle_time / self.duration * 2 * np.pi) + 1) / 2
            return self.base_rate * (0.5 + wave_factor)
        elif self.name == "spike":
            if cycle_time > self.duration * 0.8:
                return self.base_rate * 3
            return self.base_rate * 0.3
        elif self.name == "random":
            return self.base_rate * random.uniform(0.2, 2.0)
        return self.base_rate
