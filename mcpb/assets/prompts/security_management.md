# Security Management Guide - System Admin MCP

## Windows Security Model Overview

### Access Control Lists (ACLs)
```
ACL Components:
- **DACL** (Discretionary ACL): Who can access
- **SACL** (System ACL): Audit logging
- **ACE** (Access Control Entry): Individual permission

Permission Types:
- Read (view files/folders)
- Write (create files, modify)
- Modify (read + write + delete)
- Read & Execute (read + run programs)
- Full Control (all permissions + change permissions)
```

### Security Principals
```
Types:
- **Users**: Individual accounts (Sandra, Administrator, Guest)
- **Groups**: Collections (Administrators, Users, Power Users)
- **System Accounts**: SYSTEM, Network Service, Local Service
- **SIDs**: Security Identifiers (unique IDs)

Best Practice:
- Assign permissions to groups, not individual users
- Use built-in groups when possible
- Create custom groups for specific needs
```

## Permission Management

### Setting Folder Permissions
```python
# Grant user read access
set_permissions(
    path="D:/Documents/Project",
    principal="DOMAIN\\Sandra",
    rights="Read",
    inheritance="This folder, subfolders and files"
)

# Grant group modify access
set_permissions(
    path="D:/Shared",
    principal="BUILTIN\\Users",
    rights="Modify",
    inheritance="This folder and subfolders"
)

# Full control for administrators
set_permissions(
    path="D:/Critical",
    principal="BUILTIN\\Administrators",
    rights="FullControl",
    inheritance="This folder, subfolders and files"
)
```

### Removing Permissions
```python
# Remove specific permission
remove_permission(
    path="D:/Private",
    principal="DOMAIN\\OldUser",
    confirm=True  # Safety confirmation
)

# Clear all permissions (dangerous!)
remove_all_permissions(
    path="D:/Reset",
    keep_owner=True,  # Keep owner intact
    confirm=True
)
```

### Permission Inheritance
```
Inheritance Options:
1. "This folder only"
2. "This folder, subfolders and files" (most common)
3. "This folder and subfolders"
4. "This folder and files"
5. "Subfolders and files only"

Blocking Inheritance:
- Stops permissions from parent
- Use cautiously (can break access)
- Often needed for sensitive folders
```

## Ownership Management

### Taking Ownership
```python
# Take ownership of file/folder
take_ownership(
    path="D:/LostAccess/file.txt",
    new_owner="DOMAIN\\Sandra",
    recursive=False  # Just this file
)

# Take ownership recursively
take_ownership(
    path="D:/LostAccess",
    new_owner="BUILTIN\\Administrators",
    recursive=True  # All subfolders and files
)
```

### Why Ownership Matters
```
Owner can:
- Always change permissions (even if no current access)
- Delete object
- Grant/revoke access to others
- Transfer ownership

Common scenarios:
- Access denied to own files (wrong owner)
- Files from old user account
- Network share permission issues
- Locked system files
```

## Permission Auditing

### Current Permissions Review
```python
# Get effective permissions for user
effective_permissions = get_effective_permissions(
    path="D:/Shared/Document.docx",
    principal="DOMAIN\\Sandra"
)

Returns:
- Read: Yes/No
- Write: Yes/No
- Modify: Yes/No
- Full Control: Yes/No
- Source of permissions (direct, group, inherited)
```

### Permission Comparison
```python
# Compare permissions between files/folders
comparison = compare_permissions(
    path1="D:/Folder1",
    path2="D:/Folder2"
)

Returns:
- Differences in ACLs
- Missing/extra permissions
- Inheritance differences
- Recommendations for alignment
```

### Audit Access
```python
# Review who has access to resource
access_list = audit_access(
    path="D:/Sensitive"
)

Returns for each principal:
- User/group name
- Permission level
- Inherited or explicit
- Effective access
```

## Security Hardening

### Least Privilege Principle
```
Best Practices:
✅ Users get minimum required permissions
✅ Use read-only when write not needed
✅ Temporary elevated access (not permanent)
✅ Regular permission audits
✅ Remove unused user permissions

Example:
- Finance folder: Finance group = Modify, Others = No Access
- Public docs: Users = Read, Authors = Modify
- System files: Administrators = Full Control, Users = Read
```

### Sensitive Data Protection
```
Layered Security:
1. **File System**: NTFS permissions (prevent access)
2. **Encryption**: EFS or BitLocker (protect data at rest)
3. **Application**: Password-protect documents
4. **Network**: Firewall rules (limit network access)
5. **Audit**: Log access attempts

Critical Folders:
- Personal data: Encrypt + strict ACLs
- Financial records: Administrator-only
- Passwords/keys: Separate encrypted volume
- Backups: Offsite + encrypted
```

### Permission Templates
```
Standard Templates:

1. **Public Read-Only**:
   - Users: Read & Execute
   - Administrators: Full Control

2. **Department Share**:
   - Department Group: Modify
   - Managers: Full Control
   - Others: No Access

3. **Collaborative Folder**:
   - Team Members: Modify
   - Team Lead: Full Control
   - Others: Read (if needed)

4. **Secure Archive**:
   - Archive Admins: Read & Execute
   - Administrators: Full Control
   - Others: No Access

5. **Drop Box** (Submit Only):
   - Users: Write (can add, can't read others)
   - Administrators: Full Control
```

## Common Permission Issues

### "Access Denied" Troubleshooting
```
Checklist:
1. Check effective permissions (may differ from expected)
2. Review inheritance (parent folder may block)
3. Verify ownership (not the owner?)
4. Check group membership (are you in expected group?)
5. UAC elevation (need administrator rights?)
6. File in use (locked by another process?)
7. Encrypted file (need certificate?)
```

### Fixing Broken Permissions
```python
# Reset to default Windows permissions
reset_permissions_to_default(
    path="C:/Windows/System32/file.dll",
    confirm=True
)

# Inherit from parent
reset_to_inherited(
    path="D:/Folder/Subfolder",
    confirm=True
)

# Apply standard template
apply_permission_template(
    path="D:/NewShare",
    template="department_share",
    department_group="DOMAIN\\Finance"
)
```

## Security Scenarios

### Scenario: Securing Confidential Documents
```
Requirements:
- Only specific users should access
- Audit all access attempts
- Encrypt files
- Prevent copying to USB

Implementation:
1. Create security group (Confidential_Access)
2. Set NTFS permissions (group only)
3. Enable auditing (log all access)
4. Apply EFS encryption
5. Group Policy: Disable USB storage for this group
6. Regular permission reviews
```

### Scenario: Shared Team Folder
```
Requirements:
- Team can read/write/delete
- Others can read only
- Manager has full control
- Track changes

Implementation:
1. Team Group: Modify permission
2. Others Group: Read permission
3. Manager: Full Control
4. Enable shadow copies (version history)
5. Audit significant operations (delete, permission change)
```

### Scenario: Locked Out of Own Files
```
Problem:
- Permissions changed (malware, mistake, etc.)
- Owner can't access

Solution:
1. Boot to Safe Mode or use admin account
2. Take ownership (right-click → Properties → Security → Advanced)
3. Grant yourself Full Control
4. Access files normally
5. Review why permissions changed (security incident?)
```

---

## Security Best Practices

### DO:
- ✅ Regular permission audits (quarterly)
- ✅ Remove old user accounts from ACLs
- ✅ Use groups, not individual users
- ✅ Document permission structure
- ✅ Test before applying to production
- ✅ Backup before major permission changes
- ✅ Enable auditing on sensitive resources
- ✅ Follow least privilege principle

### DON'T:
- ❌ Give "Everyone" full control
- ❌ Disable inheritance without reason
- ❌ Grant more permissions than needed
- ❌ Leave old employee accounts active
- ❌ Ignore permission errors (investigate!)
- ❌ Use simple passwords for admin accounts
- ❌ Share admin credentials

---

## Compliance and Auditing

### Regulatory Requirements
```
GDPR, HIPAA, SOX may require:
- Access controls on sensitive data
- Audit trails of data access
- Regular permission reviews
- Data encryption
- Access revocation procedures
```

### Audit Logging
```python
# Enable auditing on folder
enable_audit_logging(
    path="D:/Regulated_Data",
    audit_events=["FileRead", "FileWrite", "FileDelete", "PermissionChange"],
    audit_principal="Everyone"
)

# Review audit logs
audit_events = get_audit_log(
    path="D:/Regulated_Data",
    start_date="2025-10-01",
    end_date="2025-10-25"
)
```

---

**Austrian Security**: Precise permissions, minimal access, maximum protection! 🇦🇹🔒

