# Graphite Theme Patcher - Architecture Overview

## Executive Summary

The Graphite Theme Patcher is a robust Python tool designed to safely update token values in Home Assistant theme YAML files. It provides comprehensive token management with support for both standard themes and auto themes with mode-specific targeting capabilities. The architecture emphasizes security, reliability, and professional YAML handling.

## Core Requirements

### Functional Requirements
- **Token Management**: Update existing tokens or create new ones in YAML theme files
- **Multi-format Support**: Handle RGB/RGBA colors, sizes, opacity, radius, generic values, and card-mod tokens
- **Theme Architecture Support**: Work with both standard themes and auto themes (light/dark modes)
- **Recipe System**: Apply batch changes via YAML recipe files from local files or URLs
- **Atomic Operations**: Ensure file consistency with backup/rollback mechanisms
- **Dry-run Capability**: Preview changes without modifying files

### Non-Functional Requirements
- **Security**: Prevent injection attacks, validate inputs, implement resource limits
- **Reliability**: Atomic file operations with rollback on failure
- **Performance**: Handle up to 50 files with size limits (10MB per file, 5MB recipe downloads)
- **Compatibility**: Support Home Assistant OS, Supervised, and Core installations
- **Maintainability**: Comprehensive logging, version tracking, and error handling

## System Architecture

### Core Components

#### 1. ThemePatcher (Main Class)
**Purpose**: Central orchestrator for theme patching operations
**Responsibilities**:
- Initialize and validate configuration
- Coordinate file processing workflow
- Manage backup/rollback operations
- Apply recipes or single token updates

#### 2. IndentationManager
**Purpose**: Professional YAML indentation handling
**Responsibilities**:
- Detect and maintain consistent YAML indentation
- Calculate proper indentation for different contexts (theme properties, mode sections)
- Validate indentation consistency
- Format indented lines professionally

#### 3. Recipe System
**Purpose**: Batch token updates via structured recipes
**Components**:
- `Recipe` class: Load, validate, and process recipe files
- Recipe metadata validation (name, author, version, patcher compatibility)
- Mode-specific patch filtering
- Support for both file and URL sources

#### 4. TokenType Enumeration
**Purpose**: Define supported token types with validation rules
**Types**:
- `RGB`: Color tokens (comma-separated format for rgb tokens, CSS functions for others)
- `SIZE`: Pixel values (e.g., "20px")
- `OPACITY`: Decimal values 0-1
- `RADIUS`: Pixel values for border radius
- `GENERIC`: Minimal validation for custom tokens
- `CARD_MOD`: Special handling with quotes and YAML scalar blocks

#### 5. Security & Validation Layer
**Purpose**: Ensure safe operations and prevent malicious input
**Features**:
- Token name validation (alphanumeric, hyphens, underscores only)
- File size limits (10MB per YAML file, 5MB for recipe downloads)
- Path traversal prevention
- Resource limits (max 50 files, 10K lines per file)
- YAML injection prevention

## Data Flow Architecture

### Standard Token Update Flow
1. **Initialization**: Validate paths, token names, and configuration
2. **File Discovery**: Locate YAML files (single file or directory-based themes)
3. **Backup Creation**: Create `.backup` files for rollback capability
4. **File Processing**: For each YAML file:
   - Parse file structure (standard vs auto theme)
   - Locate existing tokens
   - Update existing or create new tokens with proper indentation
   - Validate YAML structure integrity
5. **Atomic Write**: Use temporary files for safe file replacement
6. **Cleanup**: Remove backups on success or rollback on failure

### Recipe Processing Flow
1. **Recipe Loading**: Load from file or URL with security validation
2. **Recipe Validation**: Check metadata, version compatibility, patch structure
3. **Variant Processing**: Apply patches to each target theme variant
4. **Mode Filtering**: Apply only patches relevant to target mode (light/dark/all)
5. **Patch Application**: Create individual ThemePatcher instances per patch
6. **Result Aggregation**: Collect results and report overall success/failure

## File Structure Analysis

### Standard Theme Structure
```yaml
theme_name:
  # Standard tokens
  primary-color: "#ff0000"
  
  ##############################################################################
  # User defined entries
  custom-token: "value"
```

### Auto Theme Structure
```yaml
theme_name:
  modes:
    light:
      primary-color: "#000000"
      ##############################################################################
      # User defined entries
      custom-token-light: "value"
    dark:
      primary-color: "#ffffff"
      ##############################################################################
      # User defined entries
      custom-token-dark: "value"
```

### Single File Theme (E-ink)
```yaml
# Direct YAML file instead of directory structure
theme_name:
  primary-color: "#000000"
```

## Recipe System Architecture

### Recipe File Format
```yaml
recipe:
  name: "Recipe Name"
  author: "Author Name"
  version: "1.0.0"
  patcher_version: ">=2.1.0"
  description: "Optional description"
  variants: ["graphite", "other-theme"]  # Default: ["graphite"]
  mode: "all"  # Default: "all" (light/dark/all)

patches:
  - token: "token-name"
    type: "rgb"  # rgb|size|opacity|radius|generic|card-mod
    value: "255, 128, 0"
    mode: "all"  # Optional: light|dark|all
    description: "Optional patch description"
```

### Recipe Processing Logic
- **Version Compatibility**: Validate patcher version requirements
- **Mode Filtering**: Include patches based on target mode:
  - Target "all": Include all patches
  - Target "light": Include patches with mode "all" or "light"
  - Target "dark": Include patches with mode "all" or "dark"
- **Variant Targeting**: Apply to specified theme variants or override theme

## Token Value Validation

### RGB/RGBA Colors
- **Format**: "255, 128, 0" or "255, 128, 0, 0.8"
- **Validation**: RGB values 0-255, alpha 0-1
- **Output**: 
  - RGB tokens: "255, 128, 0" (comma-separated)
  - Other color tokens: "rgb(255, 128, 0)" or "rgba(255, 128, 0, 0.8)"

### Size/Radius Tokens
- **Format**: Integer values
- **Validation**: Must be positive
- **Output**: "20px"

### Opacity Tokens
- **Format**: Decimal 0-1 or percentage
- **Validation**: Range 0-1
- **Output**: "0.8"

### Card-mod Tokens
- **Single-line**: Wrapped in quotes
- **Multi-line**: YAML scalar block format with proper indentation
- **Special handling**: Always created if missing

## Security Considerations

### Input Validation
- **Token Names**: Alphanumeric, hyphens, underscores only (max 100 chars)
- **Dangerous Characters**: Reject tokens with newlines, YAML specials, quotes
- **YAML Injection**: Prevent malicious YAML through token names or values

### File System Security
- **Path Traversal**: Resolve paths and validate within theme directories
- **Symlink Safety**: Handle broken symlinks and circular references
- **Access Control**: Verify write permissions before operations

### Resource Limits
- **File Count**: Maximum 50 YAML files per operation
- **File Size**: 10MB limit per YAML file
- **Line Count**: 10,000 lines maximum per file
- **Recipe Size**: 5MB limit for recipe downloads
- **Download Timeout**: 30 seconds for recipe URLs

## Error Handling & Recovery

### Backup Strategy
- Create `.backup` files before any modifications
- Atomic file operations using temporary files
- Full rollback on any processing failure
- Cleanup backups only on complete success

### Error Categories
1. **Validation Errors**: Invalid inputs, missing files, permission issues
2. **Processing Errors**: YAML parsing failures, indentation issues
3. **Recipe Errors**: Invalid recipe format, version incompatibility
4. **System Errors**: File I/O failures, resource exhaustion

### Recovery Mechanisms
- **Automatic Rollback**: Restore all files from backups on failure
- **Partial Success Handling**: Rollback all changes if any file fails
- **Lock Files**: Prevent concurrent modifications using POSIX file locks

## Edge Cases & Special Handling

### Theme Structure Variations
1. **Single File Themes**: Handle `.yaml` files directly (e-ink themes)
2. **Directory Themes**: Process all `.yaml` files in theme directory
3. **Mixed Indentation**: Detect and maintain existing indentation patterns
4. **Missing Sections**: Create user-defined sections with proper formatting

### Auto Theme Complexities
1. **Mode Detection**: Identify light/dark sections within modes
2. **Section Boundaries**: Properly calculate start/end lines for each mode
3. **Mode Targeting**: Apply patches only to relevant modes
4. **Indentation Context**: Maintain proper indentation within mode sections

### Token Creation Scenarios
1. **Missing User Sections**: Create with proper header formatting
2. **Card-mod Tokens**: Always create at theme property level
3. **Mode-specific Creation**: Add to appropriate light/dark sections
4. **Indentation Consistency**: Match existing file patterns

### File System Edge Cases
1. **Symlink Handling**: Resolve safely, avoid circular references
2. **Concurrent Access**: Use file locks to prevent conflicts
3. **Disk Space**: Ensure sufficient space for backups and temporary files
4. **Permission Changes**: Handle permission modifications during operation

## Quality Assurance Checklist

### Pre-Processing Validation
- [ ] Valid theme directory or file exists
- [ ] Write permissions confirmed
- [ ] Token name passes security validation
- [ ] Token value validates for specified type
- [ ] Resource limits not exceeded (file count, sizes)
- [ ] Recipe format and version compatibility (if using recipes)

### File Processing Verification
- [ ] Backup files created successfully
- [ ] File locks acquired properly
- [ ] YAML structure analysis completed
- [ ] Existing tokens identified correctly
- [ ] Proper indentation calculated and applied
- [ ] Token updates/creations positioned correctly
- [ ] YAML syntax remains valid after modifications

### Mode-Specific Validation
- [ ] Auto theme modes detected correctly
- [ ] Mode sections boundaries identified accurately
- [ ] Target mode filtering applied properly
- [ ] Indentation consistent within mode contexts
- [ ] User-defined sections created in correct locations

### Post-Processing Checks
- [ ] All modified files parse as valid YAML
- [ ] Indentation consistency maintained
- [ ] Token values formatted correctly for their types
- [ ] Comments and headers preserved appropriately
- [ ] File permissions unchanged
- [ ] Backup files present until successful completion

### Error Recovery Testing
- [ ] Rollback works correctly on processing failure
- [ ] Partial failures trigger complete rollback
- [ ] Lock files cleaned up properly
- [ ] Backup files removed only on complete success
- [ ] Error messages provide actionable information

### Recipe-Specific Validation
- [ ] Recipe metadata complete and valid
- [ ] Version compatibility verified
- [ ] Patch structure validated
- [ ] Mode filtering applied correctly
- [ ] Multiple variants processed successfully
- [ ] Recipe source (file/URL) handled securely

### Security Verification
- [ ] No path traversal vulnerabilities
- [ ] Input validation prevents injection attacks
- [ ] Resource limits prevent DoS attacks
- [ ] File operations remain within theme boundaries
- [ ] Recipe downloads respect size and timeout limits

### Performance Validation
- [ ] Processing completes within reasonable time
- [ ] Memory usage remains bounded
- [ ] Large files handled without issues
- [ ] Concurrent access properly serialized
- [ ] Temporary files cleaned up promptly

### Integration Testing
- [ ] Home Assistant theme loading works correctly
- [ ] Theme changes visible in HA interface
- [ ] No YAML syntax errors in HA logs
- [ ] Theme switching between modes works (auto themes)
- [ ] Custom tokens available in HA theme system
