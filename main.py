import pygame
import sys
from load_balancer_viz import LoadBalancerVisualization


def main():
    pygame.init()

    display_info = pygame.display.Info()
    WIDTH, HEIGHT = display_info.current_w, display_info.current_h
    FPS = 60

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("Load Balancer System")
    clock = pygame.time.Clock()

    viz = LoadBalancerVisualization(WIDTH, HEIGHT)

    simulation_config = {
        "screen_resolution": f"{WIDTH}x{HEIGHT}",
        "initial_algorithm": viz.load_balancer.algorithm.value,
        "server_count": len(viz.servers),
        "server_types": [s.server_type.value for s in viz.servers],
        "traffic_pattern": viz.current_traffic_pattern.name,
        "auto_algorithm_cycling": viz.algorithm_cycle_enabled,
    }
    viz.report_generator.initialize_simulation(simulation_config)

    print("🚀 Advanced Load Balancer System Started")
    print("=" * 60)
    print("Features:")
    print("• 7 Load Balancing Algorithms (Round Robin, Least Connections, etc.)")
    print("• 4 Server Types (Standard, High-Performance, Memory/CPU Optimized)")
    print("• 4 User Types (Light, Standard, Heavy, Burst)")
    print("• 4 Traffic Patterns (Steady, Wave, Spike, Random)")
    print("• Real-time Performance Monitoring")
    print("• Server Failure Simulation")
    print("• Resource-based Request Routing")
    print("• Comprehensive Metrics Tracking")
    print("• Detailed Report Generation")
    print("=" * 60)
    print("\nControls:")
    print("SPACE      - Spawn single user")
    print("B          - Spawn burst traffic (8 users)")
    print("A          - Toggle auto algorithm cycling")
    print("1-7        - Switch algorithms (Round Robin, Least Conn, etc.)")
    print("Q/W/E/R    - Traffic patterns (Steady/Wave/Spike/Random)")
    print("F          - Toggle fullscreen")
    print("P          - Print performance report")
    print("S          - Start/Stop simulation")
    print("ESC        - Quit and save reports")
    print("=" * 60)

    fullscreen = False
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_f:
                        fullscreen = not fullscreen
                        if fullscreen:
                            screen = pygame.display.set_mode(
                                (WIDTH, HEIGHT), pygame.FULLSCREEN
                            )
                        else:
                            screen = pygame.display.set_mode(
                                (WIDTH, HEIGHT), pygame.NOFRAME
                            )
                    elif event.key == pygame.K_p:
                        print_performance_report(viz)
                    else:
                        viz.handle_keypress(event.key)
                elif event.type == pygame.TEXTINPUT:
                    viz.handle_text_input(event.text)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        viz.handle_mouse_click(event.pos)

            viz.update()

            viz.draw(screen)

            pygame.display.flip()
            clock.tick(FPS)

    except KeyboardInterrupt:
        print("\nShutdown requested by user...")
    finally:

        print("\n" + "=" * 60)
        print("GENERATING COMPREHENSIVE SIMULATION REPORTS...")
        print("=" * 60)

        try:

            viz.report_generator.finalize_simulation()

            viz.report_generator.collect_server_metrics(viz.servers)
            viz.report_generator.collect_user_analytics(viz.completed_users, viz.users)
            viz.report_generator.collect_load_balancer_performance(viz.load_balancer)
            viz.report_generator.collect_system_statistics(viz)

            report_files = viz.report_generator.generate_comprehensive_report()

            print("✅ Reports successfully generated:")
            print(f"📊 JSON Report: {report_files['json_report']}")
            print(f"📈 CSV Reports: {list(report_files['csv_reports'].values())}")
            print(f"🌐 HTML Report: {report_files['html_report']}")
            print(f"📝 Summary Report: {report_files['summary_report']}")
            print(f"⏰ Report Timestamp: {report_files['report_timestamp']}")

        except Exception as e:
            print(f"❌ Error generating reports: {e}")
            print(
                "Report generation failed, but simulation data is preserved in memory."
            )

        print("=" * 60)
        pygame.quit()
        sys.exit()


def print_performance_report(viz):
    """Print detailed performance report to console"""
    print("\n" + "=" * 80)
    print("LIVE PERFORMANCE REPORT")
    print("=" * 80)

    stats = viz.get_system_stats()
    print(f"System Uptime: {stats['uptime']:.2f} seconds")
    print(f"Current Algorithm: {stats['algorithm']}")
    print(f"Traffic Pattern: {stats['traffic_pattern']}")
    print(f"Active Users: {stats['active_users']}")
    print(f"Total Spawned: {stats['total_spawned']}")
    print(f"Success Rate: {stats['success_rate']:.1f}%")
    print(f"Healthy Servers: {stats['healthy_servers']}")

    print("\nSERVER STATUS:")
    print("-" * 40)
    for server in viz.servers:
        info = server.get_server_info()
        print(f"{info['name']} ({info['type']}):")
        print(f"  Status: {info['status']}")
        print(f"  Connections: {info['connections']}")
        print(f"  CPU: {info['cpu_usage']} | Memory: {info['memory_usage']}")
        print(f"  Load Score: {info['load_score']}")
        print(f"  Avg Response: {info['avg_response_time']}")
        print(f"  Total Requests: {info['total_requests']}")

    print("\nLOAD BALANCER PERFORMANCE:")
    print("-" * 40)
    lb_stats = viz.load_balancer.get_algorithm_stats()
    if lb_stats:
        print(f"Algorithm: {lb_stats['algorithm']}")
        print(f"Success Rate: {lb_stats['success_rate']:.1%}")
        print(f"Total Decisions: {lb_stats['total_decisions']}")
        print(f"Requests Received: {lb_stats['requests_received']}")
        print(f"Requests Routed: {lb_stats['requests_routed']}")
        print(f"Dropped Requests: {lb_stats['dropped_requests']}")

    print("\nPERFORMANCE METRICS:")
    print("-" * 40)
    perf_summary = viz.performance_monitor.get_performance_summary()
    if perf_summary:
        print(f"Average Response Time: {perf_summary.get('avg_response_time', 0):.2f}s")
        print(f"P95 Response Time: {perf_summary.get('p95_response_time', 0):.2f}s")
        print(f"P99 Response Time: {perf_summary.get('p99_response_time', 0):.2f}s")
        print(f"Total Processed Requests: {perf_summary.get('total_requests', 0)}")

        if "user_type_breakdown" in perf_summary:
            print("\nUSER TYPE BREAKDOWN:")
            for user_type, type_stats in perf_summary["user_type_breakdown"].items():
                print(f"  {user_type.title()}:")
                print(f"    Count: {type_stats['count']}")
                print(f"    Success Rate: {type_stats['success_rate']:.1%}")
                print(f"    Avg Response: {type_stats['avg_response_time']:.2f}s")

    if viz.simulation_running:
        print("\nSIMULATION STATUS:")
        print("-" * 40)
        print(f"Status: RUNNING")
        print(f"Elapsed: {viz.simulation_elapsed:.1f}s / {viz.simulation_duration}s")
        print(f"Spawn Rate: {viz.simulation_spawn_rate:.1f} users/second")
        print(f"Total Users: {viz.simulation_total_users}")
        print(f"Success: {viz.simulation_success_users}")
        print(f"Failed: {viz.simulation_failed_users}")
        if viz.simulation_total_users > 0:
            sim_success_rate = (
                viz.simulation_success_users / viz.simulation_total_users
            ) * 100
            print(f"Simulation Success Rate: {sim_success_rate:.1f}%")
    else:
        print("\nSIMULATION STATUS: STOPPED")

    print("=" * 80)


if __name__ == "__main__":
    main()
