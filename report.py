import json
import csv
import time
import os
from datetime import datetime
from collections import defaultdict
import numpy as np
from user import UserType, AttackType
from upstream_server import ServerType, ServerStatus
from load_balancer import LoadBalancingAlgorithm


class SimulationReportGenerator:
    """Comprehensive report generator for load balancer simulation data"""

    def __init__(self):
        self.simulation_data = {
            "metadata": {},
            "server_metrics": {},
            "user_analytics": {},
            "load_balancer_performance": {},
            "system_statistics": {},
            "time_series_data": {},
            "security_analysis": {},
        }
        self.start_time = None
        self.end_time = None

    def initialize_simulation(self, simulation_config):
        """Initialize simulation tracking with configuration"""
        self.start_time = time.time()
        self.simulation_data["metadata"] = {
            "simulation_id": f"sim_{int(self.start_time)}",
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "configuration": simulation_config,
            "version": "1.0.0",
        }

    def reset(self):
        """Reset all simulation data to prepare for a new simulation"""
        self.simulation_data = {
            "metadata": {},
            "server_metrics": {},
            "user_analytics": {},
            "load_balancer_performance": {},
            "system_statistics": {},
            "time_series_data": {},
            "security_analysis": {},
        }
        self.start_time = None
        self.end_time = None

    def finalize_simulation(self):
        """Finalize simulation and set end time"""
        self.end_time = time.time()
        self.simulation_data["metadata"]["end_time"] = datetime.fromtimestamp(
            self.end_time
        ).isoformat()
        self.simulation_data["metadata"]["duration_seconds"] = (
            self.end_time - self.start_time
        )

    def collect_server_metrics(self, servers):
        """Collect comprehensive server performance metrics"""
        server_data = {}

        for server in servers:
            server_info = server.get_server_info()

            server_data[server.name] = {
                "basic_info": {
                    "name": server.name,
                    "type": server.server_type.value,
                    "status": server.status.value,
                    "weight": getattr(server, "weight", 1),
                },
                "resource_specs": {
                    "cpu_cores": server.cpu_cores,
                    "memory_gb": server.memory_gb,
                    "base_processing_speed": server.base_processing_speed,
                },
                "performance_metrics": {
                    "total_requests_processed": server.total_requests,
                    "current_connections": server.active_connections,
                    "cpu_utilization_percent": server.cpu_utilization,
                    "memory_utilization_percent": server.memory_utilization,
                    "load_score": (
                        server.load_score if server.load_score != float("inf") else -1
                    ),
                    "average_response_time": server.avg_response_time,
                    "last_failure_time": getattr(server, "last_failure_time", 0),
                },
                "historical_data": {
                    "response_times": (
                        list(server.response_times)
                        if hasattr(server, "response_times")
                        else []
                    ),
                    "load_history": (
                        list(server.load_history)
                        if hasattr(server, "load_history")
                        else []
                    ),
                },
                "utilization_analysis": self._analyze_server_utilization(server),
                "efficiency_metrics": self._calculate_server_efficiency(server),
            }

        self.simulation_data["server_metrics"] = server_data

    def _analyze_server_utilization(self, server):
        """Analyze server utilization patterns"""
        if not hasattr(server, "load_history") or not server.load_history:
            return {"status": "no_data"}

        load_history = list(server.load_history)

        return {
            "average_load": np.mean(load_history),
            "max_load": np.max(load_history),
            "min_load": np.min(load_history),
            "load_variance": np.var(load_history),
            "load_stability": 1.0 / (1.0 + np.var(load_history)),
            "peak_utilization_periods": self._identify_peak_periods(load_history),
            "efficiency_rating": self._calculate_efficiency_rating(server),
        }

    def _identify_peak_periods(self, load_history):
        """Identify periods of peak utilization"""
        if len(load_history) < 10:
            return []

        threshold = np.percentile(load_history, 80)
        peaks = []
        in_peak = False
        peak_start = 0

        for i, load in enumerate(load_history):
            if load >= threshold and not in_peak:
                in_peak = True
                peak_start = i
            elif load < threshold and in_peak:
                in_peak = False
                peaks.append(
                    {
                        "start_index": peak_start,
                        "end_index": i,
                        "duration": i - peak_start,
                        "average_load": np.mean(load_history[peak_start:i]),
                    }
                )

        return peaks

    def _calculate_efficiency_rating(self, server):
        """Calculate server efficiency rating (0-100)"""
        if server.total_requests == 0:
            return 0

        utilization_score = min(
            100, (server.cpu_utilization + server.memory_utilization) / 2
        )
        response_time_score = max(0, 100 - (server.avg_response_time * 20))
        reliability_score = 100 if server.status == ServerStatus.HEALTHY else 50

        efficiency = (
            utilization_score * 0.4
            + response_time_score * 0.4
            + reliability_score * 0.2
        )
        return min(100, max(0, efficiency))

    def _calculate_server_efficiency(self, server):
        """Calculate detailed server efficiency metrics"""
        if server.total_requests == 0:
            return {"status": "no_requests"}

        return {
            "requests_per_second": server.total_requests
            / (time.time() - (self.start_time or time.time())),
            "resource_efficiency": {
                "cpu_efficiency": server.total_requests
                / max(1, server.cpu_utilization),
                "memory_efficiency": server.total_requests
                / max(1, server.memory_utilization),
            },
            "throughput_per_core": server.total_requests / server.cpu_cores,
            "throughput_per_gb": server.total_requests / server.memory_gb,
            "overall_efficiency_score": self._calculate_efficiency_rating(server),
        }

    def collect_user_analytics(self, completed_users, active_users):
        """Collect comprehensive user behavior and performance analytics"""
        all_users = completed_users + active_users

        user_stats = {
            "total_users": len(all_users),
            "completed_users": len(completed_users),
            "active_users": len(active_users),
            "success_rate": len([u for u in completed_users if not u.failed])
            / max(1, len(completed_users)),
        }

        type_analysis = defaultdict(
            lambda: {
                "count": 0,
                "successes": 0,
                "failures": 0,
                "timeouts": 0,
                "response_times": [],
                "retry_counts": [],
                "resource_usage": [],
            }
        )

        attack_analysis = defaultdict(
            lambda: {
                "count": 0,
                "success_rate": 0,
                "average_intensity": 0,
                "spawn_counts": [],
                "durations": [],
            }
        )

        for user in all_users:
            user_type = user.user_type
            type_stats = type_analysis[user_type.value]

            type_stats["count"] += 1
            type_stats["response_times"].append(user.get_response_time())
            type_stats["retry_counts"].append(user.retry_count)
            type_stats["resource_usage"].append(
                {
                    "cpu": user.cpu_requirement,
                    "memory": user.memory_requirement,
                    "processing_time": user.processing_time,
                }
            )

            if user in completed_users:
                if user.failed:
                    type_stats["failures"] += 1
                    if user.timeout_exit:
                        type_stats["timeouts"] += 1
                else:
                    type_stats["successes"] += 1

            if user_type == UserType.NAUGHTY and hasattr(user, "attack_type"):
                attack_type = user.attack_type.value
                attack_stats = attack_analysis[attack_type]
                attack_stats["count"] += 1
                attack_stats["average_intensity"] += getattr(
                    user, "attack_intensity", 0
                )
                if hasattr(user, "spawn_count"):
                    attack_stats["spawn_counts"].append(user.spawn_count)
                if hasattr(user, "attack_duration"):
                    attack_stats["durations"].append(user.attack_duration)

        for user_type, stats in type_analysis.items():
            if stats["count"] > 0:
                stats["success_rate"] = stats["successes"] / stats["count"]
                stats["failure_rate"] = stats["failures"] / stats["count"]
                stats["timeout_rate"] = stats["timeouts"] / stats["count"]
                stats["avg_response_time"] = (
                    np.mean(stats["response_times"]) if stats["response_times"] else 0
                )
                stats["avg_retry_count"] = (
                    np.mean(stats["retry_counts"]) if stats["retry_counts"] else 0
                )
                stats["avg_cpu_usage"] = (
                    np.mean([r["cpu"] for r in stats["resource_usage"]])
                    if stats["resource_usage"]
                    else 0
                )
                stats["avg_memory_usage"] = (
                    np.mean([r["memory"] for r in stats["resource_usage"]])
                    if stats["resource_usage"]
                    else 0
                )

        for attack_type, stats in attack_analysis.items():
            if stats["count"] > 0:
                stats["average_intensity"] /= stats["count"]
                stats["avg_spawn_count"] = (
                    np.mean(stats["spawn_counts"]) if stats["spawn_counts"] else 0
                )
                stats["avg_duration"] = (
                    np.mean(stats["durations"]) if stats["durations"] else 0
                )

        self.simulation_data["user_analytics"] = {
            "summary": user_stats,
            "by_type": dict(type_analysis),
            "priority_analysis": self._analyze_priority_distribution(all_users),
            "performance_correlation": self._analyze_user_performance_correlation(
                all_users
            ),
        }

        self.simulation_data["security_analysis"] = {
            "attack_summary": dict(attack_analysis),
            "security_metrics": self._calculate_security_metrics(all_users),
            "threat_assessment": self._assess_threat_levels(attack_analysis),
        }

    def _analyze_priority_distribution(self, users):
        """Analyze request priority distribution and performance"""
        priority_stats = defaultdict(
            lambda: {
                "count": 0,
                "success_rate": 0,
                "avg_response_time": 0,
                "response_times": [],
            }
        )

        for user in users:
            priority = user.priority.value
            priority_stats[priority]["count"] += 1
            priority_stats[priority]["response_times"].append(user.get_response_time())

        for priority, stats in priority_stats.items():
            if stats["count"] > 0:
                stats["avg_response_time"] = np.mean(stats["response_times"])

        return dict(priority_stats)

    def _analyze_user_performance_correlation(self, users):
        """Analyze correlation between user characteristics and performance"""
        if not users:
            return {}

        cpu_reqs = [u.cpu_requirement for u in users]
        memory_reqs = [u.memory_requirement for u in users]
        response_times = [u.get_response_time() for u in users]

        correlations = {}
        try:
            correlations["cpu_response_correlation"] = np.corrcoef(
                cpu_reqs, response_times
            )[0, 1]
            correlations["memory_response_correlation"] = np.corrcoef(
                memory_reqs, response_times
            )[0, 1]
        except:
            correlations["cpu_response_correlation"] = 0
            correlations["memory_response_correlation"] = 0

        return correlations

    def _calculate_security_metrics(self, users):
        """Calculate security-related metrics"""
        total_users = len(users)
        naughty_users = [u for u in users if u.user_type == UserType.NAUGHTY]

        return {
            "attack_percentage": len(naughty_users) / max(1, total_users) * 100,
            "stealth_attack_percentage": len(
                [u for u in naughty_users if getattr(u, "stealth_mode", False)]
            )
            / max(1, len(naughty_users))
            * 100,
            "average_attack_intensity": (
                np.mean([getattr(u, "attack_intensity", 0) for u in naughty_users])
                if naughty_users
                else 0
            ),
            "attack_success_rate": len([u for u in naughty_users if not u.failed])
            / max(1, len(naughty_users)),
        }

    def _assess_threat_levels(self, attack_analysis):
        """Assess threat levels based on attack patterns"""
        threat_levels = {}

        for attack_type, stats in attack_analysis.items():
            if stats["count"] == 0:
                threat_levels[attack_type] = "NONE"
                continue

            threat_score = stats["count"] * stats["average_intensity"]

            if threat_score > 100:
                threat_levels[attack_type] = "CRITICAL"
            elif threat_score > 50:
                threat_levels[attack_type] = "HIGH"
            elif threat_score > 20:
                threat_levels[attack_type] = "MEDIUM"
            else:
                threat_levels[attack_type] = "LOW"

        return threat_levels

    def collect_load_balancer_performance(self, load_balancer):
        """Collect load balancer performance metrics"""
        algo_stats = load_balancer.get_algorithm_stats()
        performance = load_balancer.evaluate_performance()

        lb_data = {
            "algorithm_info": {
                "current_algorithm": load_balancer.algorithm.value,
                "switch_count": load_balancer.algorithm_switch_count,
                "last_switch_time": getattr(load_balancer, "last_algorithm_switch", 0),
            },
            "request_handling": {
                "total_received": load_balancer.total_requests_received,
                "total_routed": load_balancer.total_requests_routed,
                "dropped_requests": load_balancer.dropped_requests,
                "routing_success_rate": load_balancer.total_requests_routed
                / max(1, load_balancer.total_requests_received),
            },
            "algorithm_performance": algo_stats or {},
            "current_performance": performance or {},
            "decision_analysis": self._analyze_routing_decisions(load_balancer),
            "efficiency_metrics": self._calculate_lb_efficiency(load_balancer),
        }

        self.simulation_data["load_balancer_performance"] = lb_data

    def _analyze_routing_decisions(self, load_balancer):
        """Analyze load balancer routing decision patterns"""
        if (
            not hasattr(load_balancer, "routing_decisions")
            or not load_balancer.routing_decisions
        ):
            return {"status": "no_decisions"}

        decisions = list(load_balancer.routing_decisions)

        method_counts = defaultdict(int)
        success_by_method = defaultdict(list)

        for decision in decisions:
            method = decision.get("method", "unknown")
            method_counts[method] += 1
            success_by_method[method].append(decision.get("success", False))

        method_analysis = {}
        for method, successes in success_by_method.items():
            method_analysis[method] = {
                "count": method_counts[method],
                "success_rate": np.mean(successes) if successes else 0,
            }

        return {
            "total_decisions": len(decisions),
            "method_breakdown": dict(method_counts),
            "method_success_rates": method_analysis,
            "overall_decision_success_rate": np.mean(
                [d.get("success", False) for d in decisions]
            ),
        }

    def _calculate_lb_efficiency(self, load_balancer):
        """Calculate load balancer efficiency metrics"""
        if load_balancer.total_requests_received == 0:
            return {"status": "no_requests"}

        duration = (self.end_time or time.time()) - (self.start_time or time.time())

        return {
            "requests_per_second": load_balancer.total_requests_received
            / max(1, duration),
            "routing_efficiency": load_balancer.total_requests_routed
            / load_balancer.total_requests_received,
            "drop_rate": load_balancer.dropped_requests
            / load_balancer.total_requests_received,
            "throughput_score": (load_balancer.total_requests_routed / max(1, duration))
            * 100,
        }

    def collect_system_statistics(self, visualization_obj):
        """Collect system-wide statistics and performance indicators"""
        stats = visualization_obj.get_system_stats()
        perf_summary = visualization_obj.performance_monitor.get_performance_summary()

        system_data = {
            "overall_stats": stats,
            "performance_summary": perf_summary or {},
            "simulation_config": {
                "traffic_pattern": visualization_obj.current_traffic_pattern.name,
                "simulation_duration": getattr(
                    visualization_obj, "simulation_duration", 0
                ),
                "spawn_rate": getattr(visualization_obj, "simulation_spawn_rate", 0),
            },
            "infrastructure_summary": {
                "total_servers": len(visualization_obj.servers),
                "server_types": [
                    s.server_type.value for s in visualization_obj.servers
                ],
                "total_capacity": self._calculate_total_capacity(
                    visualization_obj.servers
                ),
            },
            "performance_trends": self._analyze_performance_trends(
                visualization_obj.performance_monitor
            ),
        }

        self.simulation_data["system_statistics"] = system_data

    def _calculate_total_capacity(self, servers):
        """Calculate total system capacity"""
        return {
            "total_cpu_cores": sum(s.cpu_cores for s in servers),
            "total_memory_gb": sum(s.memory_gb for s in servers),
            "theoretical_max_requests": sum(
                getattr(s, "weight", 1) * 50 for s in servers
            ),
        }

    def _analyze_performance_trends(self, performance_monitor):
        """Analyze performance trends over time"""
        if (
            not hasattr(performance_monitor, "metrics")
            or not performance_monitor.metrics["response_times"]
        ):
            return {"status": "insufficient_data"}

        response_times = list(performance_monitor.metrics["response_times"])

        if len(response_times) > 10:

            mid_point = len(response_times) // 2
            first_half = response_times[:mid_point]
            second_half = response_times[mid_point:]

            trend = {
                "response_time_trend": (
                    "improving"
                    if np.mean(second_half) < np.mean(first_half)
                    else "degrading"
                ),
                "first_half_avg": np.mean(first_half),
                "second_half_avg": np.mean(second_half),
                "overall_variance": np.var(response_times),
                "performance_stability": 1.0 / (1.0 + np.var(response_times)),
            }
        else:
            trend = {"status": "insufficient_data_for_trend"}

        return trend

    def generate_comprehensive_report(self, output_dir="reports"):
        """Generate comprehensive report in multiple formats"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"load_balancer_report_{timestamp}"

        json_path = self._generate_json_report(output_dir, base_filename)

        csv_paths = self._generate_csv_reports(output_dir, base_filename)

        html_path = self._generate_html_report(output_dir, base_filename)

        txt_path = self._generate_summary_report(output_dir, base_filename)

        return {
            "json_report": json_path,
            "csv_reports": csv_paths,
            "html_report": html_path,
            "summary_report": txt_path,
            "report_timestamp": timestamp,
        }

    def _generate_json_report(self, output_dir, base_filename):
        """Generate detailed JSON report"""
        json_path = os.path.join(output_dir, f"{base_filename}.json")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.simulation_data, f, indent=2, default=str)

        return json_path

    def _generate_csv_reports(self, output_dir, base_filename):
        """Generate CSV reports for different data categories"""
        csv_paths = {}

        if "server_metrics" in self.simulation_data:
            server_csv_path = os.path.join(output_dir, f"{base_filename}_servers.csv")
            self._write_server_csv(server_csv_path)
            csv_paths["servers"] = server_csv_path

        if "user_analytics" in self.simulation_data:
            user_csv_path = os.path.join(output_dir, f"{base_filename}_users.csv")
            self._write_user_csv(user_csv_path)
            csv_paths["users"] = user_csv_path

        return csv_paths

    def _write_server_csv(self, file_path):
        """Write server metrics to CSV"""
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "server_name",
                "server_type",
                "status",
                "total_requests",
                "cpu_utilization_percent",
                "memory_utilization_percent",
                "avg_response_time",
                "efficiency_score",
                "load_score",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for server_name, data in self.simulation_data["server_metrics"].items():
                row = {
                    "server_name": server_name,
                    "server_type": data["basic_info"]["type"],
                    "status": data["basic_info"]["status"],
                    "total_requests": data["performance_metrics"][
                        "total_requests_processed"
                    ],
                    "cpu_utilization_percent": data["performance_metrics"][
                        "cpu_utilization_percent"
                    ],
                    "memory_utilization_percent": data["performance_metrics"][
                        "memory_utilization_percent"
                    ],
                    "avg_response_time": data["performance_metrics"][
                        "average_response_time"
                    ],
                    "efficiency_score": data.get("efficiency_metrics", {}).get(
                        "overall_efficiency_score", 0
                    ),
                    "load_score": data["performance_metrics"]["load_score"],
                }
                writer.writerow(row)

    def _write_user_csv(self, file_path):
        """Write user analytics to CSV"""
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "user_type",
                "count",
                "success_rate",
                "failure_rate",
                "avg_response_time",
                "avg_cpu_usage",
                "avg_memory_usage",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for user_type, data in self.simulation_data["user_analytics"][
                "by_type"
            ].items():
                row = {
                    "user_type": user_type,
                    "count": data["count"],
                    "success_rate": data.get("success_rate", 0),
                    "failure_rate": data.get("failure_rate", 0),
                    "avg_response_time": data.get("avg_response_time", 0),
                    "avg_cpu_usage": data.get("avg_cpu_usage", 0),
                    "avg_memory_usage": data.get("avg_memory_usage", 0),
                }
                writer.writerow(row)

    def _generate_html_report(self, output_dir, base_filename):
        """Generate comprehensive HTML report"""
        html_path = os.path.join(output_dir, f"{base_filename}.html")

        html_content = self._create_html_content()

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path

    def _create_html_content(self):
        """Create HTML report content"""
        metadata = self.simulation_data.get("metadata", {})

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Load Balancer Simulation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: 
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .section {{ margin-bottom: 25px; }}
        .section h2 {{ color: 
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .metric-card {{ background: 
        .metric-value {{ font-size: 24px; font-weight: bold; color: 
        .metric-label {{ color: 
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid 
        th {{ background-color: 
        .status-healthy {{ color: 
        .status-failed {{ color: 
        .status-degraded {{ color: 
        .threat-critical {{ color: 
        .threat-high {{ color: 
        .threat-medium {{ color: 
        .threat-low {{ color: 
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Load Balancer Simulation Report</h1>
            <p>Simulation ID: {metadata.get('simulation_id', 'N/A')}</p>
            <p>Generated: {metadata.get('start_time', 'N/A')} - {metadata.get('end_time', 'N/A')}</p>
            <p>Duration: {metadata.get('duration_seconds', 0):.2f} seconds</p>
        </div>
        
        {self._generate_system_overview_html()}
        {self._generate_server_metrics_html()}
        {self._generate_user_analytics_html()}
        {self._generate_load_balancer_html()}
        {self._generate_security_analysis_html()}
    </div>
</body>
</html>"""
        return html

    def _generate_system_overview_html(self):
        """Generate system overview section for HTML report"""
        system_stats = self.simulation_data.get("system_statistics", {}).get(
            "overall_stats", {}
        )

        return f"""
        <div class="section">
            <h2>System Overview</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{system_stats.get('total_spawned', 0)}</div>
                    <div class="metric-label">Total Users</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{system_stats.get('success_rate', 0):.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{system_stats.get('active_users', 0)}</div>
                    <div class="metric-label">Active Users</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{system_stats.get('algorithm', 'N/A')}</div>
                    <div class="metric-label">Load Balancing Algorithm</div>
                </div>
            </div>
        </div>"""

    def _generate_server_metrics_html(self):
        """Generate server metrics section for HTML report"""
        server_metrics = self.simulation_data.get("server_metrics", {})

        html = """
        <div class="section">
            <h2>Server Performance Metrics</h2>
            <table>
                <thead>
                    <tr>
                        <th>Server</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Requests</th>
                        <th>CPU Usage</th>
                        <th>Memory Usage</th>
                        <th>Avg Response</th>
                        <th>Efficiency</th>
                    </tr>
                </thead>
                <tbody>"""

        for server_name, data in server_metrics.items():
            basic_info = data.get("basic_info", {})
            perf_metrics = data.get("performance_metrics", {})
            efficiency = data.get("efficiency_metrics", {})

            status_class = f"status-{basic_info.get('status', '').lower()}"

            html += f"""
                    <tr>
                        <td>{server_name}</td>
                        <td>{basic_info.get('type', 'N/A')}</td>
                        <td class="{status_class}">{basic_info.get('status', 'N/A')}</td>
                        <td>{perf_metrics.get('total_requests_processed', 0)}</td>
                        <td>{perf_metrics.get('cpu_utilization_percent', 0):.1f}%</td>
                        <td>{perf_metrics.get('memory_utilization_percent', 0):.1f}%</td>
                        <td>{perf_metrics.get('average_response_time', 0):.2f}s</td>
                        <td>{efficiency.get('overall_efficiency_score', 0):.1f}/100</td>
                    </tr>"""

        html += """
                </tbody>
            </table>
        </div>"""

        return html

    def _generate_user_analytics_html(self):
        """Generate user analytics section for HTML report"""
        user_analytics = self.simulation_data.get("user_analytics", {})
        by_type = user_analytics.get("by_type", {})

        html = """
        <div class="section">
            <h2>User Analytics</h2>
            <table>
                <thead>
                    <tr>
                        <th>User Type</th>
                        <th>Count</th>
                        <th>Success Rate</th>
                        <th>Avg Response Time</th>
                        <th>Avg CPU Usage</th>
                        <th>Avg Memory Usage</th>
                    </tr>
                </thead>
                <tbody>"""

        for user_type, data in by_type.items():
            html += f"""
                    <tr>
                        <td>{user_type.title()}</td>
                        <td>{data.get('count', 0)}</td>
                        <td>{data.get('success_rate', 0):.1%}</td>
                        <td>{data.get('avg_response_time', 0):.2f}s</td>
                        <td>{data.get('avg_cpu_usage', 0):.2f}</td>
                        <td>{data.get('avg_memory_usage', 0):.2f}</td>
                    </tr>"""

        html += """
                </tbody>
            </table>
        </div>"""

        return html

    def _generate_load_balancer_html(self):
        """Generate load balancer performance section for HTML report"""
        lb_perf = self.simulation_data.get("load_balancer_performance", {})
        request_handling = lb_perf.get("request_handling", {})

        return f"""
        <div class="section">
            <h2>Load Balancer Performance</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{request_handling.get('total_received', 0)}</div>
                    <div class="metric-label">Total Requests Received</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{request_handling.get('total_routed', 0)}</div>
                    <div class="metric-label">Successfully Routed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{request_handling.get('dropped_requests', 0)}</div>
                    <div class="metric-label">Dropped Requests</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{request_handling.get('routing_success_rate', 0):.1%}</div>
                    <div class="metric-label">Routing Success Rate</div>
                </div>
            </div>
        </div>"""

    def _generate_security_analysis_html(self):
        """Generate security analysis section for HTML report"""
        security = self.simulation_data.get("security_analysis", {})
        threat_assessment = security.get("threat_assessment", {})

        html = """
        <div class="section">
            <h2>Security Analysis</h2>
            <h3>Threat Assessment</h3>
            <table>
                <thead>
                    <tr>
                        <th>Attack Type</th>
                        <th>Threat Level</th>
                    </tr>
                </thead>
                <tbody>"""

        for attack_type, threat_level in threat_assessment.items():
            threat_class = f"threat-{threat_level.lower()}"
            html += f"""
                    <tr>
                        <td>{attack_type.replace('_', ' ').title()}</td>
                        <td class="{threat_class}">{threat_level}</td>
                    </tr>"""

        html += """
                </tbody>
            </table>
        </div>"""

        return html

    def _generate_summary_report(self, output_dir, base_filename):
        """Generate text summary report"""
        txt_path = os.path.join(output_dir, f"{base_filename}_summary.txt")

        metadata = self.simulation_data.get("metadata", {})
        system_stats = self.simulation_data.get("system_statistics", {}).get(
            "overall_stats", {}
        )

        summary = f"""
LOAD BALANCER SIMULATION SUMMARY REPORT
========================================

Simulation Information:
- Simulation ID: {metadata.get('simulation_id', 'N/A')}
- Start Time: {metadata.get('start_time', 'N/A')}
- End Time: {metadata.get('end_time', 'N/A')}
- Duration: {metadata.get('duration_seconds', 0):.2f} seconds

System Performance:
- Total Users Processed: {system_stats.get('total_spawned', 0)}
- Overall Success Rate: {system_stats.get('success_rate', 0):.1f}%
- Load Balancing Algorithm: {system_stats.get('algorithm', 'N/A')}
- Traffic Pattern: {system_stats.get('traffic_pattern', 'N/A')}

Server Summary:
{self._generate_server_summary_text()}

Load Balancer Performance:
{self._generate_lb_summary_text()}

Security Analysis:
{self._generate_security_summary_text()}

Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(summary)

        return txt_path

    def _generate_server_summary_text(self):
        """Generate server summary for text report"""
        server_metrics = self.simulation_data.get("server_metrics", {})

        summary = ""
        for server_name, data in server_metrics.items():
            basic_info = data.get("basic_info", {})
            perf_metrics = data.get("performance_metrics", {})

            summary += f"- {server_name} ({basic_info.get('type', 'N/A')}): "
            summary += f"Status={basic_info.get('status', 'N/A')}, "
            summary += f"Requests={perf_metrics.get('total_requests_processed', 0)}, "
            summary += f"CPU={perf_metrics.get('cpu_utilization_percent', 0):.1f}%\n"

        return summary

    def _generate_lb_summary_text(self):
        """Generate load balancer summary for text report"""
        lb_perf = self.simulation_data.get("load_balancer_performance", {})
        request_handling = lb_perf.get("request_handling", {})

        return f"""- Requests Received: {request_handling.get('total_received', 0)}
- Requests Routed: {request_handling.get('total_routed', 0)}
- Requests Dropped: {request_handling.get('dropped_requests', 0)}
- Routing Success Rate: {request_handling.get('routing_success_rate', 0):.1%}"""

    def _generate_security_summary_text(self):
        """Generate security summary for text report"""
        security = self.simulation_data.get("security_analysis", {})
        threat_assessment = security.get("threat_assessment", {})

        if not threat_assessment:
            return "- No security threats detected"

        summary = ""
        for attack_type, threat_level in threat_assessment.items():
            summary += f"- {attack_type.replace('_', ' ').title()}: {threat_level}\n"

        return summary
