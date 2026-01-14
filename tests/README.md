# System Admin MCP Test Suite

Comprehensive test harness for System Admin MCP server.

## Test Structure

- `test_portmanteau.py` - Tests for the `system_admin` portmanteau tool (22 operations)
- `test_system_ops.py` - Tests for individual system operation tools
- `test_implementations.py` - Tests for implementation functions
- `test_integration.py` - Integration tests for tool registration and execution
- `test_edge_cases.py` - Edge cases and boundary condition tests
- `conftest.py` - Pytest fixtures and configuration

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=system_admin_mcp --cov-report=html

# Run specific test file
pytest tests/test_portmanteau.py

# Run specific test class
pytest tests/test_portmanteau.py::TestFileRecovery

# Run specific test
pytest tests/test_portmanteau.py::TestFileRecovery::test_scan_volume

# Run with verbose output
pytest -v

# Run only fast tests (exclude slow markers)
pytest -m "not slow"
```

## Test Coverage

The test suite covers:

1. **All 22 Portmanteau Operations:**
   - File Recovery (4): scan_volume, recover_file, validate_recovery, batch_recover
   - Security Management (6): get_permissions, set_permissions, remove_permission, take_ownership, audit_permissions, modify_acl
   - Volume Maintenance (6): check_disk_health, analyze_disk_usage, disk_cleanup, defragment_disk, optimize_ssd, get_volume_info
   - System Diagnostics (6): get_hardware_info, get_os_info, get_installed_software, get_performance_metrics, get_event_log, health_check

2. **Individual Tools:**
   - list_volumes, get_file_owner, recover_file, get_disk_usage, get_process_info, get_system_info, ping, help, status

3. **Error Handling:**
   - Missing parameters
   - Invalid parameters
   - Permission errors
   - Service unavailable
   - File not found
   - Network errors

4. **Edge Cases:**
   - Empty strings
   - Very long paths
   - Special characters
   - Unicode paths
   - Boundary values
   - Concurrent operations

## Fixtures

- `temp_dir` - Temporary directory for test files
- `temp_file` - Temporary file for testing
- `mock_bridge` - Mock UserBridge instance
- `mock_wmi` - Mock WMI for hardware tests
- `mock_psutil` - Mock psutil for system metrics
- `mock_win32` - Mock win32api functions
- `mock_win32security` - Mock win32security functions
- `mock_subprocess` - Mock subprocess for PowerShell
- `mock_win32evtlog` - Mock win32evtlog for event logs
- `mock_platform` - Mock platform module
- `mock_is_admin` - Mock admin privileges (True)
- `mock_is_not_admin` - Mock admin privileges (False)

## Notes

- Most tests use mocks to avoid requiring actual admin privileges
- Integration tests may require the service to be installed (marked appropriately)
- Some tests may fail on non-Windows systems (Windows-specific functionality)
- Tests are designed to be fast and isolated

