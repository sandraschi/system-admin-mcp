# Troubleshooting Guide - System Admin MCP

## Common Administrator Privilege Issues

### Problem: "Access Denied" Despite Admin Account

**Causes**:
- UAC (User Account Control) not elevated
- Process not running as administrator
- Virtual environment without admin rights
- Network share permissions different

**Solutions**:
1. ✅ Run PowerShell/Command Prompt as Administrator
2. ✅ Run Python script with elevated privileges
3. ✅ Check "Run as administrator" for shortcuts
4. ✅ Verify `whoami /groups` shows admin SID

### Problem: MCP Server Can't Execute Privileged Operations

**Solutions**:
```powershell
# Run MCP server as administrator
Start-Process python -ArgumentList "-m system_admin_mcp" -Verb RunAs

# Or from elevated PowerShell:
python -m system_admin_mcp
```

## File Recovery Issues

### Problem: Cannot Find Deleted File

**Troubleshooting**:
1. Verify deletion was recent (<24 hours better)
2. Check Recycle Bin first (easiest recovery)
3. Confirm file was on NTFS volume (not FAT32)
4. Verify not on network drive (different recovery method)
5. Check Shadow Copies (Previous Versions)

**If still not found**:
- File may be completely overwritten
- MFT entry may be reused
- Name may be partially corrupted (try partial search)
- Wrong drive scanned

### Problem: Recovered File is Corrupted

**Causes**:
- Partial overwriting before recovery
- Fragmented file with missing clusters
- File header/footer damaged
- Wrong file type detected

**Solutions**:
- Try file repair tools (Office Repair, JPEG repair, etc.)
- Use hex editor to inspect file structure
- Attempt partial data extraction
- Consider file unrecoverable if severely damaged

### Problem: Recovery Hangs or Freezes

**Solutions**:
- Increase timeout settings
- Check drive is responsive (not failing)
- Verify sufficient RAM available
- Try smaller batch sizes
- Check disk for errors (may be failing drive)

## Permission and Security Issues

### Problem: Permission Changes Don't Take Effect

**Troubleshooting**:
1. Check inheritance (parent may be overriding)
2. Verify "Replace all child permissions" if needed
3. Check if permissions are denied (deny overrides allow)
4. Log out and back in (permissions cache)
5. Restart Explorer.exe (shell cache)

### Problem: Cannot Take Ownership

**Solutions**:
- Must be administrator or have "Take ownership" privilege
- Enable "Take Ownership" right-click menu (registry)
- Use TAKEOWN command from elevated prompt
- Boot to Safe Mode if file locked
- Check if file is in use (close applications)

### Problem: Permission Inheritance Confusing

**Understanding Inheritance**:
```
Explicit permissions: Set directly on object
Inherited permissions: From parent folder

Resolution order:
1. Explicit Deny (highest priority)
2. Explicit Allow
3. Inherited Deny
4. Inherited Allow (lowest priority)

Troubleshooting:
- Check parent folder permissions
- Disable inheritance to see explicit only
- Use "Effective Access" tab to see final result
```

## Volume and Disk Issues

### Problem: Disk Defragmentation Fails

**Solutions**:
- Ensure not an SSD (don't defragment SSDs!)
- Free up space (need >15% free)
- Run chkdsk first (fix errors)
- Disable system restore temporarily
- Boot to Safe Mode and try again
- Check for disk errors (failing drive?)

### Problem: CHKDSK Finds Errors But Can't Fix

**Causes**:
- Volume is in use (system drive)
- Severe corruption
- Hardware failure

**Solutions**:
- Schedule chkdsk on reboot (for C:)
- Boot to Safe Mode
- Use Windows Recovery Environment
- If hardware failure: Clone drive immediately

### Problem: Cannot Shrink Volume

**Solutions**:
- Defragment first (moves unmovable files)
- Disable system restore temporarily
- Disable page file temporarily
- Disable hibernation (powercfg /h off)
- Use Disk Management's max shrink value
- Some files truly unmovable (may need imaging)

## Performance Issues

### Problem: Disk Usage 100% Constant

**Common Causes**:
- Windows Search indexing (disable or limit)
- Windows Update downloading
- Antivirus scanning
- Superfetch/SysMain (disable on SSD)
- Failing drive (check SMART!)

**Diagnosis**:
```powershell
# Find what's using disk
Get-Process | Sort-Object -Property TotalProcessorTime -Descending | Select -First 10
# Or use Resource Monitor (resmon.exe)
```

### Problem: High CPU Usage, Unknown Cause

**Investigation Steps**:
1. Task Manager → Sort by CPU
2. Identify process name
3. Research process (legitimate or malware?)
4. If legitimate: Update or configure
5. If malware: Run antivirus, remove
6. Check for Windows Update in background
7. Review startup programs

### Problem: Running Out of RAM

**Solutions**:
- Close unnecessary programs
- Increase page file size (short-term)
- Add physical RAM (long-term)
- Check for memory leaks (process RAM grows continuously)
- Restart problematic applications
- Consider 64-bit applications (vs 32-bit)

## Diagnostic Tool Issues

### Problem: PowerShell Execution Policy Blocks Scripts

**Solutions**:
```powershell
# Check current policy
Get-ExecutionPolicy

# Set to allow scripts (elevated PowerShell)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or bypass for single script
powershell -ExecutionPolicy Bypass -File script.ps1
```

### Problem: WMI Service Not Running

**Solutions**:
```powershell
# Check WMI service
Get-Service Winmgmt

# Start WMI service
Start-Service Winmgmt

# If won't start: Rebuild WMI repository
# (Advanced: Run from elevated cmd)
# winmgmt /resetrepository
```

## System Admin MCP Specific

### Problem: MCP Server Won't Start

**Checklist**:
1. Python 3.8+ installed
2. Dependencies: `pip install -r requirements.txt`
3. Administrator privileges
4. Port not in use (default MCP ports)
5. Check server logs for errors

### Problem: Commands Return "Insufficient Privileges"

**Solutions**:
- Run MCP server as administrator (always!)
- Verify UAC elevation worked
- Check Windows Security settings
- Confirm user in Administrators group

### Problem: File Recovery Returns No Results

**Debugging**:
- Verify drive letter correct
- Check drive is NTFS (not FAT32, exFAT)
- Confirm deletion timeframe
- Try broader search criteria
- Check if file was on network drive (different method)

---

## Emergency Procedures

### System Won't Boot
```
Recovery steps:
1. Boot to Windows Recovery Environment
2. Advanced options → Startup Repair
3. If fails: Command Prompt
4. Run: chkdsk C: /f /r
5. Run: sfc /scannow /offbootdir=C:\ /offwindir=C:\Windows
6. If still fails: System Restore or Reset
```

### Data Loss Emergency
```
Priority actions:
1. STOP all activity on affected drive
2. Power down if severe (prevent further damage)
3. Image drive (exact copy) if possible
4. Work on image, not original
5. Professional data recovery if critical
```

### Ransomware Incident
```
IMMEDIATE actions:
1. Disconnect from network (prevent spread)
2. Power down affected systems
3. DO NOT pay ransom (usually doesn't help)
4. Contact security professional
5. Restore from offline backup
6. Scan all systems
7. Change all passwords
```

### Blue Screen of Death (BSOD)
```
Diagnostic steps:
1. Note error code (e.g., "SYSTEM_SERVICE_EXCEPTION")
2. Check Event Viewer (Event ID 1001, System log)
3. Review recently installed software/drivers
4. Boot to Safe Mode
5. Uninstall problematic driver/software
6. Run memory diagnostic
7. Check for Windows updates
8. If recurring: Hardware issue (test RAM, drive, etc.)
```

---

## Getting Help

### Resources (In Order):
1. **This troubleshooting guide** - Common Windows issues
2. **System Admin MCP docs** - README, documentation
3. **Windows Event Viewer** - System and Application logs
4. **Microsoft Docs** - Official documentation
5. **Community Forums** - Answers to specific issues
6. **Professional Support** - For critical systems

### When Reporting Issues

**Include**:
- Windows version and build number
- System Admin MCP version
- Error messages (exact text)
- Event log entries (relevant errors)
- Steps to reproduce
- Hardware specs (if performance issue)
- Recent changes (software, updates, config)

### Debug Mode
```powershell
# Enable verbose logging
$env:LOG_LEVEL = "DEBUG"
python -m system_admin_mcp

# Check logs for diagnostic info
# Typically in: AppData/Local/system-admin-mcp/logs
```

---

## Prevention Best Practices

### Before Making Changes:
- ✅ Create system restore point
- ✅ Backup critical data
- ✅ Document current state
- ✅ Test in non-production first
- ✅ Have rollback plan

### Regular Maintenance:
- ✅ Weekly: Event log review
- ✅ Monthly: Disk cleanup
- ✅ Quarterly: Full health check
- ✅ Annually: Hardware refresh planning

### Security Hygiene:
- ✅ Keep Windows updated
- ✅ Keep antivirus updated
- ✅ Regular password changes
- ✅ Review user accounts (disable old)
- ✅ Audit folder permissions

### Data Protection:
- ✅ Automated backups (daily)
- ✅ Test backup restoration (monthly)
- ✅ Offsite backup (weekly)
- ✅ Shadow copies enabled
- ✅ Important files: cloud sync (OneDrive, etc.)

---

**Austrian Reliability**: Prevent problems through preparation, solve issues methodically, document everything! 🇦🇹🔧

