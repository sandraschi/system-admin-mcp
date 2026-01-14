# File Recovery Guide - System Admin MCP

## NTFS File Recovery Fundamentals

### How NTFS Deletion Works

**When a file is deleted:**
1. MFT (Master File Table) entry marked as "free"
2. File data clusters marked as available
3. **File data NOT immediately erased**
4. File name may be partially overwritten
5. Recoverable until clusters reused

**Recovery Time Window:**
- **Immediately**: 95%+ success rate
- **Hours later**: 70-90% success (depends on disk activity)
- **Days later**: 30-70% success
- **Weeks later**: 10-30% success
- **Months later**: Usually unrecoverable

### Critical Actions After Deletion

#### **IMMEDIATE (Within Minutes)**
```
DO:
✅ STOP using the affected drive immediately
✅ Note file name, location, approximate size
✅ Note deletion time
✅ Begin recovery process ASAP

DON'T:
❌ Save any files to the affected drive
❌ Install software to the affected drive
❌ Download files to the affected drive
❌ Wait ("I'll do it later" = lower success rate)
```

#### **Why Speed Matters**
```
Every operation on a drive:
- Windows creates temp files
- Applications write cache
- System creates logs
- Page file updates
- Each write may overwrite deleted file clusters

Result: Recovery chance decreases rapidly
```

## Recovery Process

### Step 1: Assessment
```python
# Gather information
recovery_assessment(
    drive="C:",
    file_name="important_document.docx",
    deletion_time="approximately 30 minutes ago",
    file_size="approximately 2 MB"
)

Returns:
- Recovery probability estimate
- Recommended approach
- Required tools
- Expected time
```

### Step 2: Volume Scanning
```python
# Scan NTFS volume for deleted files
scan_results = scan_volume(
    drive="C:",
    file_pattern="*.docx",
    max_results=100
)

Returns list of:
- File names (may be partial)
- Deletion timestamps
- File sizes
- MFT entry numbers
- Recovery probability
```

### Step 3: File Recovery
```python
# Recover specific file
recovery_result = recover_file(
    source_drive="C:",
    mft_entry=12345,
    destination="D:/Recovery/recovered_file.docx",
    verify_integrity=True
)

Returns:
- Success status
- Recovered file location
- Integrity check result
- File size and hash
```

### Step 4: Verification
```python
# Verify recovered file
verification = verify_recovered_file(
    file_path="D:/Recovery/recovered_file.docx"
)

Checks:
- File opens without errors
- File size matches expected
- No corruption detected
- Content appears complete
```

## Recovery Scenarios

### Scenario 1: Recently Deleted Document
```
Context:
- Deleted 10 minutes ago
- From Documents folder
- .docx file, ~2 MB
- Drive has moderate activity

Process:
1. Stop using drive NOW
2. Scan volume for .docx files
3. Locate file by name/time/size
4. Recover to different drive (D:, E:, external)
5. Verify file opens in Word
6. Create backup immediately

Expected: 95% success
```

### Scenario 2: Emptied Recycle Bin
```
Context:
- Recycle bin emptied 2 hours ago
- Multiple files deleted
- Not sure of exact file names
- Drive has been used since deletion

Process:
1. Minimize further disk activity
2. Scan entire volume
3. Filter by deletion timestamp
4. Review candidates (may have truncated names)
5. Recover all candidates to safe location
6. Review recovered files
7. Keep useful files, delete rest

Expected: 60-80% success for larger files
```

### Scenario 3: Accidental Format
```
Context:
- Drive accidentally quick-formatted
- Need to recover data
- Format was recent (within hours)

Process:
1. CRITICAL: Do NOT use the formatted drive
2. Use specialized recovery tools (beyond basic MCP)
3. Image the drive first (create exact copy)
4. Work on image, not original drive
5. Scan image for file systems
6. Recover files from found filesystems

Expected: Variable (30-90%) depending on format type
Note: Full format (not quick format) = much lower chance
```

## Advanced Recovery Techniques

### Recovering Files Without Names
```
When file name is overwritten:
- Search by file signature (magic numbers)
- Filter by file size range
- Sort by deletion time
- Check file headers for type
- Use context clues (modified date, etc.)

File Signatures:
- PDF: %PDF (starts with)
- DOCX: PK (ZIP container)
- JPEG: FF D8 FF
- PNG: 89 50 4E 47
- Excel: PK or D0 CF
```

### Partial Recovery
```
If file partially overwritten:
- Recover what remains
- Assess damage extent
- Attempt file repair tools
- Extract salvageable content
- Rebuild if possible

File Types with Good Repair:
- Text files (.txt, .log)
- Office documents (built-in repair)
- Some image formats
```

### Recovery from Shadow Copies
```
Windows Volume Shadow Copies (if enabled):
- Automatic system restore points
- Previous versions of files/folders
- Often overlooked recovery method
- Built into Windows (no special tools)

Access:
- Right-click file/folder → Properties → Previous Versions
- Or use PowerShell: Get-VShadowCopy
- Can restore entire file or specific version
```

## Best Practices

### Prevention (Better Than Recovery!)
```
DO:
✅ Enable automatic backups (File History, OneDrive)
✅ Use version control (Git for code/documents)
✅ Enable Shadow Copies on important volumes
✅ Regular backup schedule (3-2-1 rule)
✅ Test backup restoration periodically

3-2-1 Rule:
- 3 copies of data
- 2 different media types
- 1 offsite backup
```

### During Recovery
```
DO:
✅ Work methodically and carefully
✅ Recover to DIFFERENT drive
✅ Verify each recovered file
✅ Document what was recovered
✅ Keep original drive intact until verified

DON'T:
❌ Panic and make hasty decisions
❌ Recover to same drive
❌ Overwrite other important data
❌ Use drive after deletion
❌ Skip verification step
```

### After Recovery
```
✅ Backup recovered files immediately
✅ Verify all important content present
✅ Update backup strategy to prevent recurrence
✅ Document incident (what, when, how recovered)
✅ Consider why deletion occurred (user error, malware, etc.)
```

## Recovery Limitations

### Cannot Recover If:
```
❌ File clusters completely overwritten
❌ Drive was securely wiped (multiple passes)
❌ Solid-state drive with TRIM enabled (data erased immediately)
❌ File was on RAM disk or temp file system
❌ Encrypted drive and encryption key lost
❌ Physical drive damage
```

### Reduced Recovery Chance If:
```
⚠️ Long time since deletion (weeks/months)
⚠️ Heavy disk activity after deletion
⚠️ Small file (more likely to be overwritten)
⚠️ Fragmented file (scattered clusters)
⚠️ System drive (high write activity)
⚠️ SSD with TRIM (even recent deletions may be unrecoverable)
```

## NTFS-Specific Knowledge

### Master File Table (MFT)
```
MFT stores:
- File names and paths
- File sizes and timestamps
- Cluster locations (data addresses)
- File attributes and permissions
- Alternate data streams

For recovery:
- MFT entry must still exist
- Cluster addresses must be valid
- Clusters must not be reallocated
```

### File System Structure
```
NTFS Components:
- Boot sector (volume info)
- MFT (file records)
- Data clusters (actual file content)
- System files ($MFT, $LogFile, etc.)
- Metadata (attributes, indexes)

Recovery focuses on:
- MFT analysis (finding deleted entries)
- Cluster reconstruction
- Data carving (finding file patterns)
```

## Recovery Tools Integration

### Built-in Windows Tools
```
PowerShell:
- Get-Item, Get-ChildItem (current files)
- Get-VShadowCopy (shadow copies)
- Get-Acl (permissions)

Third-party (recommended):
- Recuva (free, user-friendly)
- PhotoRec (free, powerful)
- R-Studio (professional, paid)
- TestDisk (free, advanced)
```

### System Admin MCP Recovery Commands
```python
# Scan for deleted files
deleted_files = scan_deleted_files(
    drive="C:",
    file_pattern="*.docx",
    deleted_since="2025-10-25 10:00:00"
)

# Recover specific file
recover_file(
    mft_entry=12345,
    destination="D:/Recovery/"
)

# Batch recovery
recover_multiple_files(
    mft_entries=[12345, 12346, 12347],
    destination="D:/Recovery/",
    preserve_structure=True
)
```

---

## Recovery Checklist

**Before Recovery**:
- ✅ Assess deletion timeframe and activity
- ✅ Verify destination drive has space
- ✅ Administrator privileges available
- ✅ Understand recovery probability
- ✅ Stop using source drive

**During Recovery**:
- ✅ Monitor progress
- ✅ Handle errors gracefully
- ✅ Don't interrupt process
- ✅ Verify each recovered file
- ✅ Keep source drive untouched

**After Recovery**:
- ✅ Verify all files recovered successfully
- ✅ Test critical files (open, check content)
- ✅ Backup recovered files
- ✅ Analyze why deletion occurred
- ✅ Implement prevention measures

---

## Recovery Success Factors

### Higher Success:
- ✅ Recent deletion (minutes to hours)
- ✅ Low disk activity after deletion
- ✅ Large files (less likely fully overwritten)
- ✅ HDD (not SSD with TRIM)
- ✅ Non-system drive
- ✅ Immediate action

### Lower Success:
- ⚠️ Old deletion (days to months)
- ⚠️ High disk activity
- ⚠️ Small files (<1 MB)
- ⚠️ SSD with TRIM enabled
- ⚠️ System drive (C:)
- ⚠️ Delayed action

---

**Austrian Precision**: Act fast, work carefully, verify thoroughly. File recovery is science + art! 🇦🇹

