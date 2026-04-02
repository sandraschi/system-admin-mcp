import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from system_admin_mcp.tools.portmanteau import system_admin, get_comprehensive_diagnostics

async def run_tests():
    print("=== Testing System Admin Diagnostics ===\n")
    
    # 1. Test get_comprehensive_diagnostics
    print("Testing get_comprehensive_diagnostics...")
    diag_result = await get_comprehensive_diagnostics()
    print(f"Status: {diag_result.get('status')}")
    if diag_result.get("status") == "success":
        print(f"Timestamp: {diag_result.get('timestamp')}")
        print(f"Health Uptime: {diag_result.get('health', {}).get('uptime_human')}")
        print(f"Top Processes: {len(diag_result.get('top_processes', {}).get('top_cpu', []))} CPU, {len(diag_result.get('top_processes', {}).get('top_memory', []))} Memory")
        print(f"Recent Errors: {len(diag_result.get('recent_errors', {}).get('errors', []))}")
        print(f"Volume Usage status: {diag_result.get('volume_usage', {}).get('status')}")
    else:
        print(f"Error: {diag_result.get('error')}")
    print("-" * 40)

    # 2. Test system_admin: get_recent_event_errors
    print("\nTesting system_admin('get_recent_event_errors')...")
    events = await system_admin("get_recent_event_errors", log_name="System", max_results=3)
    print(f"Status: {events.get('status')}")
    if events.get("status") == "success":
        print(f"Errors found: {len(events.get('errors', []))}")
    print("-" * 40)

    # 3. Test system_admin: check_system_health_status
    print("\nTesting system_admin('check_system_health_status')...")
    health = await system_admin("check_system_health_status")
    print(f"Status: {health.get('status')}")
    if health.get("status") == "success":
        print(f"Uptime: {health.get('uptime_human')}")
        print(f"Pending reboot: {health.get('pending_reboot')}")
    print("-" * 40)

    # 4. Test system_admin: get_top_resource_processes
    print("\nTesting system_admin('get_top_resource_processes')...")
    top_procs = await system_admin("get_top_resource_processes", max_results=3)
    print(f"Status: {top_procs.get('status')}")
    if top_procs.get("status") == "success":
        print(f"Found {len(top_procs.get('top_cpu', []))} top CPU processes")
    print("-" * 40)

    # 5. Test system_admin: audit_network_ports
    print("\nTesting system_admin('audit_network_ports')...")
    ports = await system_admin("audit_network_ports", include_system=True)
    print(f"Status: {ports.get('status')}")
    if ports.get("status") == "success":
        print(f"Found {len(ports.get('connections', []))} active connections")
    print("-" * 40)

    # 6. Test system_admin: analyze_top_folder_sizes
    print("\nTesting system_admin('analyze_top_folder_sizes')...")
    # Test with project directory for speed
    test_path = str(Path(__file__).parent.parent)
    folder_analysis = await system_admin("analyze_top_folder_sizes", path=test_path)
    print(f"Status: {folder_analysis.get('status')}")
    if folder_analysis.get("status") == "success":
        print(f"Root path: {folder_analysis.get('root_path')}")
        print(f"Top folders found: {len(folder_analysis.get('top_folders', []))}")
        if folder_analysis.get('top_folders'):
            print(f"Largest: {folder_analysis.get('top_folders')[0].get('name')} ({folder_analysis.get('top_folders')[0].get('size_gb')} GB)")
    print("-" * 40)

if __name__ == "__main__":
    asyncio.run(run_tests())
