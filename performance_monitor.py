import time
import numpy as np
from collections import deque


class PerformanceMonitor:
    """Monitors and tracks system performance metrics"""

    def __init__(self):
        self.metrics = {
            "response_times": deque(maxlen=10000),
            "success_rates": deque(maxlen=100),
            "server_utilizations": deque(maxlen=100),
            "algorithm_performance": {},
            "user_type_stats": {},
        }
        self.start_time = time.time()

    def record_user_completion(self, user):
        """Record metrics when a user completes (success or failure)"""
        response_time = user.get_response_time()
        self.metrics["response_times"].append(response_time)

        user_type = user.user_type.value
        if user_type not in self.metrics["user_type_stats"]:
            self.metrics["user_type_stats"][user_type] = {
                "count": 0,
                "successes": 0,
                "total_response_time": 0,
            }

        stats = self.metrics["user_type_stats"][user_type]
        stats["count"] += 1
        stats["total_response_time"] += response_time
        if not user.failed:
            stats["successes"] += 1

    def get_performance_summary(self):
        """Get comprehensive performance summary"""
        if not self.metrics["response_times"]:
            return {}

        response_times = list(self.metrics["response_times"])

        summary = {
            "avg_response_time": np.mean(response_times),
            "p95_response_time": np.percentile(response_times, 95),
            "p99_response_time": np.percentile(response_times, 99),
            "total_requests": len(response_times),
            "uptime": time.time() - self.start_time,
        }

        summary["user_type_breakdown"] = {}
        for user_type, stats in self.metrics["user_type_stats"].items():
            if stats["count"] > 0:
                summary["user_type_breakdown"][user_type] = {
                    "count": stats["count"],
                    "success_rate": stats["successes"] / stats["count"],
                    "avg_response_time": stats["total_response_time"] / stats["count"],
                }

        return summary
