# Volume Maintenance Guide - System Admin MCP

## Disk Health Monitoring

### SMART Status
```python
# Check disk health
smart_status = check_disk_health(drive="C:")

Critical metrics:
- Reallocated sectors (bad blocks)
- Pending sectors (going bad)
- Temperature
- Power-on hours
- Read error rate

Warning signs:
⚠️ Reallocated sectors > 0 (drive degrading)
⚠️ Pending sectors > 0 (imminent failure)
⚠️ Temperature > 50°C (overheating)
⚠️ Read errors increasing (failing drive)
```

### Disk Space Management
```python
# Analyze disk usage
usage = analyze_disk_usage(drive="C:")

Returns:
- Total capacity
- Used space
- Free space
- Largest folders
- File type breakdown
- Temp file size

Recommendations:
- Free space < 10%: Urgent cleanup needed
- Free space < 20%: Cleanup recommended
- Free space > 30%: Healthy
```

## Maintenance Operations

### Disk Cleanup
```python
# Safe cleanup operations
cleanup_result = disk_cleanup(
    drive="C:",
    targets=[
        "temp_files",          # AppData/Local/Temp
        "windows_temp",        # Windows/Temp
        "recycle_bin",         # Deleted items
        "downloads_folder",    # Old downloads (confirm!)
        "browser_cache",       # Browser temp files
        "update_cleanup"       # Old Windows updates
    ],
    dry_run=True  # Preview first!
)

Space recovered:
- Temp files: Usually 1-10 GB
- Recycle bin: Variable
- Browser cache: 500 MB - 5 GB
- Update cleanup: 1-20 GB (major space saver!)
```

### Disk Optimization

#### **HDD (Hard Disk Drive)**
```python
# Defragmentation (HDDs only!)
defrag_result = defragment_disk(
    drive="C:",
    thorough=False  # Quick defrag, or True for deep
)

When to defragment:
- Fragmentation > 10% (check with analyze)
- After large deletions
- Monthly for active drives
- During low-activity periods

Benefits:
- Faster file access
- Improved performance
- Better disk longevity
```

#### **SSD (Solid-State Drive)**
```python
# TRIM operation (SSDs only!)
trim_result = optimize_ssd(
    drive="C:"
)

SSD Maintenance:
- Enable TRIM (usually automatic)
- DO NOT defragment SSDs!
- Monitor write endurance
- Keep 10-20% free space
- Firmware updates periodically

TRIM benefits:
- Maintains write performance
- Extends SSD lifespan
- Frees NAND cells
```

### Volume Analysis
```python
# Comprehensive volume check
volume_info = analyze_volume(
    drive="C:",
    include_health=True,
    include_fragmentation=True,
    include_errors=True
)

Returns:
- File system type (NTFS, FAT32, exFAT)
- Total/used/free space
- Cluster size
- Fragmentation level
- Error count (bad sectors)
- SMART status
- Recommendations
```

## Error Checking and Repair

### Check Disk (CHKDSK)
```python
# Scan for file system errors
chkdsk_result = check_disk_errors(
    drive="C:",
    fix_errors=False,  # Scan only
    scan_bad_sectors=True
)

Error types detected:
- Orphaned files (in lost+found)
- Cross-linked files (sharing clusters)
- Invalid file size
- Incorrect timestamps
- Bad sectors (physical damage)

When to run:
- After unexpected shutdown
- Suspicion of file system corruption
- Unexplained errors accessing files
- Monthly maintenance (scan only)
```

### Repair Operations
```python
# Fix file system errors (requires reboot)
repair_result = repair_disk(
    drive="C:",
    fix_errors=True,
    recover_bad_sectors=True,
    schedule_on_reboot=True  # C: requires offline scan
)

Safety notes:
⚠️ Backup critical data first
⚠️ May take hours for large drives
⚠️ System drive scans on next boot
⚠️ Don't interrupt repair process
```

## Space Reclamation

### Finding Large Files
```python
# Locate space hogs
large_files = find_large_files(
    drive="C:",
    min_size_mb=100,  # Files > 100 MB
    top_n=50
)

Common culprits:
- Old installers (.exe, .msi) in Downloads
- Video files (.mp4, .avi, .mkv)
- Disk images (.iso, .vhd)
- Archives (.zip, .rar, .7z)
- Database files (.db, .mdf)
- Virtual machines (.vhd, .vmdk)
```

### Duplicate File Detection
```python
# Find duplicate files (same content)
duplicates = find_duplicate_files(
    path="D:/Documents",
    recursive=True,
    min_size_kb=100  # Ignore tiny files
)

Duplicate sources:
- Multiple downloads
- Copy-paste errors
- Sync conflicts (OneDrive, Dropbox)
- Backup copies forgotten
- Photo imports (same file, different folders)

Action: Keep one copy, delete duplicates (carefully!)
```

### Old File Cleanup
```python
# Find files not accessed in months
old_files = find_old_files(
    path="D:/Archive",
    days_not_accessed=365,  # 1 year
    min_size_mb=1
)

Candidates for:
- Archiving (move to cold storage)
- Compression (reduce size)
- Deletion (if truly unused)

Verify before deleting!
```

## Volume Management

### Resizing Volumes
```
Growing Volume:
1. Check unallocated space available
2. Backup important data
3. Use Disk Management (diskmgmt.msc)
4. Extend volume
5. Verify file system intact

Shrinking Volume:
1. Defragment first (move files)
2. Backup important data
3. Use Disk Management
4. Shrink volume (Windows calculates max)
5. Verify file system intact
```

### Volume Shadow Copies (VSS)
```python
# Enable shadow copies
enable_shadow_copies(
    drive="D:",
    max_storage_gb=10,  # Storage limit
    schedule="daily_at_midnight"
)

# List available shadow copies
shadow_copies = list_shadow_copies(drive="D:")

# Restore from shadow copy
restore_from_shadow(
    source_shadow_id="shadow_123",
    file_path="D:/Documents/file.docx",
    destination="D:/Recovered/file.docx"
)

Benefits:
- Automatic file versioning
- Quick recovery of changed/deleted files
- No third-party software needed
- User-accessible (Previous Versions tab)
```

---

## Maintenance Schedules

### Daily Automation
```
Automated tasks:
- Temp file cleanup (Windows/Temp, user temps)
- Recycle bin check (empty if > 10 GB)
- Event log review (errors/warnings)
- Backup verification
```

### Weekly Automation
```
Scheduled tasks:
- Disk usage report
- Large file analysis
- Security scan (malware check)
- Update installation (if configured)
- Shadow copy creation
```

### Monthly Automation
```
Maintenance tasks:
- Disk error scan (chkdsk /scan)
- Defragmentation analysis (HDD)
- Permission audit
- Software update review
- Disk space trend analysis
```

### Quarterly Tasks
```
Deep maintenance:
- Full disk error check (chkdsk /f)
- SMART status review
- Drive health assessment
- Consider disk replacement if issues
- Major cleanup (old installers, archives)
```

---

## Emergency Procedures

### Disk Running Out of Space
```
Priority order:
1. Empty Recycle Bin (instant, safe)
2. Delete temp files (safe)
3. Run Windows Disk Cleanup (guided, safe)
4. Find and remove large files (review first!)
5. Uninstall unused programs
6. Move files to other drives
7. External storage if needed
```

### Disk Errors Detected
```
Actions:
1. Backup immediately (if possible)
2. Run chkdsk /scan (online scan)
3. Schedule offline scan (chkdsk /f /r)
4. Monitor SMART status
5. Prepare for disk replacement if many errors
6. Don't ignore (errors typically worsen)
```

### Drive Failure Imminent
```
SMART reports failure:
1. STOP using drive (read-only if possible)
2. Backup EVERYTHING immediately
3. Clone drive to new drive (disk imaging)
4. Replace drive
5. Restore from backup or clone
6. Dispose of failed drive securely
```

---

## Best Practices

### Disk Health:
- ✅ Monitor SMART status monthly
- ✅ Keep 20%+ free space
- ✅ Run error checks quarterly
- ✅ Defragment HDDs monthly (not SSDs!)
- ✅ TRIM enabled for SSDs
- ✅ Replace drives >5 years old proactively

### Performance:
- ✅ Regular temp file cleanup
- ✅ Uninstall unused software
- ✅ Disable unnecessary startup programs
- ✅ Keep drivers updated
- ✅ Monitor disk queue length

### Data Safety:
- ✅ Regular backups (automated)
- ✅ Shadow copies enabled
- ✅ Test backup restoration
- ✅ Monitor backup status
- ✅ Offsite backup copy

---

**Austrian Precision**: Proactive maintenance prevents expensive emergencies! 🇦🇹💾

