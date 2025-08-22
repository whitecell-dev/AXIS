# AXIS Conventions & Design Rules

## Core Philosophy
**JSON → α-conversion → β-reduction → Side Effects**

AXIS implements a functional programming model for data processing with cryptographic verification at each stage.

## Design Principles

### 1. Deterministic Canonicalization
- All objects must be canonically sortable
- No `NaN`, `Infinity`, or non-finite numbers
- Consistent key ordering in dictionaries
- Reproducible hashing across platforms

### 2. Pure Functions First
- **PIPES** (α-conversion): Data normalization only
- **RULES** (β-reduction): Logic without side effects  
- **ADAPTERS**: Controlled side effects with audit trails

### 3. Template Safety
- Use `{{variable}}` syntax for substitution
- Sanitize filenames: `tr ' ' '_' | tr -cd '[:alnum:]_-'`
- Quote CSV fields containing spaces or special chars
- Never trust user input in shell commands

## YAML Configuration Rules

### PIPES Configuration
```yaml
pipeline:
  - rename: {old_field: new_field}     # Field renaming
  - validate: {field: "type"}          # Type coercion
  - enrich: {new_field: "value"}       # Add computed fields
  - transform: {field: "{{template}}"} # Template expansion
  - extract: {new_key: "path"}         # Field extraction
  - filter: {field: {gt: 100}}         # Conditional filtering
```

**Rules:**
- Don't set defaults that RULES will override (causes conflicts)
- Use `now()` and `timestamp()` for time enrichment
- Keep transformations simple and deterministic

### RULES Configuration
```yaml
component: ComponentName
rules:
  - if: "condition"           # AST-parsed boolean expression
    priority: 10              # Higher = wins conflicts (optional)
    then: {field: value}      # State changes
    else: {field: other}      # Alternative (optional)
```

**Rules:**
- Use priorities for mutually exclusive rules
- Design non-overlapping conditions when possible
- Use `field+: [item]` for additive changes (lists)
- Keep expressions simple: `age >= 18 and role == 'admin'`
- Prefer explicit over implicit logic

### ADAPTERS Configuration  
```yaml
adapters:
  - name: descriptive_name
    command: unix_command
    args: ["--flag", "{{template}}"]
    input: "{{stdin_template}}"    # Optional stdin content
```

**Rules:**
- Always use `mkdir -p` before file operations
- Sanitize filenames from user data
- Use absolute paths or create directories first
- Timeout protection (scripts have 30s limit)
- Log operations for audit trails

## Security Guidelines

### Template Injection Prevention
- Never use `eval()` or `exec()` on user data
- Whitelist allowed operations in AST parser
- Validate all file paths before creation
- Use shell escaping for dynamic arguments

### Audit Trail Requirements
- Every stage must generate content hashes
- Log all rule conflicts and resolutions  
- Track iteration counts and timeouts
- Preserve input/output relationships

### File System Safety
- Only write to designated output directories
- Use `tee` and `cat` for safe file operations
- Avoid recursive operations on user paths
- Check available disk space for large operations

## Performance Patterns

### Rule Engine Optimization
- Put high-priority rules first
- Use specific conditions before general ones
- Limit fixpoint iterations (current: 50)
- Monitor conflict generation rates

### Template Efficiency  
- Cache compiled templates when possible
- Minimize string substitutions in loops
- Use batch operations for file I/O
- Prefer streaming over loading full datasets

## Error Handling

### Graceful Degradation
```yaml
# Good: Additive errors
- if: "invalid_condition"
  then:
    errors+: ["Specific error message"]

# Bad: Failing fast without context
- if: "invalid_condition"  
  then:
    status: "failed"
```

### Conflict Resolution
- Use priority systems over arbitrary ordering
- Log all conflicts for debugging
- Provide meaningful conflict descriptions
- Allow partial success with error accumulation

## Integration Patterns

### Unix Tool Chains
```bash
# Good: Composable pipeline
cat data.json | axis_pipes.py run normalize.yaml | 
               axis_rules.py apply logic.yaml |
               axis_adapters.py exec outputs.yaml

# Good: With existing tools  
nmap -oJ scan.json target | axis_pipes.py run security.yaml |
                           axis_rules.py apply threat_detection.yaml |
                           axis_adapters.py exec alerts.yaml
```

### Data Validation
- Validate at pipeline entry (PIPES stage)
- Use type coercion before logic rules
- Accumulate validation errors, don't fail fast
- Provide clear error messages with context

## Testing Strategies

### Deterministic Testing
- Use fixed timestamps in test data
- Test with canonical input ordering
- Verify hash consistency across runs
- Test conflict resolution edge cases

### Edge Case Coverage
- Empty datasets and null values
- Special characters in field names
- Very large numbers and precision limits
- Unicode handling in templates

## Scaling Considerations

### When to Harden
- Replace YAML with compiled configs for production
- Add schema validation for configuration files
- Implement connection pooling for external systems
- Use proper logging frameworks instead of echo

### Performance Monitoring
- Track rule evaluation times
- Monitor memory usage in large datasets
- Set appropriate timeouts for external commands
- Log adapter execution statistics

## Common Anti-Patterns

### ❌ Don't Do This
```yaml
# Conflicting defaults
pipeline:
  - enrich: {status: "pending"}
rules:
  - if: "true"
    then: {status: "active"}  # Always conflicts!

# Unsafe file operations  
adapters:
  - command: "rm"
    args: ["-rf", "{{user_path}}"]  # Dangerous!

# Complex logic in templates
transform:
  result: "{{if condition then value1 else value2}}"  # Too complex
```

### ✅ Do This Instead
```yaml
# Clean separation
pipeline:
  - enrich: {timestamp: "now()"}  # Non-conflicting enrichment
rules:
  - if: "validated == true"
    then: {status: "active"}     # Conditional only

# Safe operations
adapters:
  - command: "mkdir"
    args: ["-p", "output/{{safe_name}}"]

# Simple templates
transform:
  display_name: "{{first}} {{last}}"  # Simple concatenation
```

## Future Evolution

This system is designed for rapid prototyping and edge case discovery. Production hardening should include:

- Compiled configuration validation
- Advanced type systems (beyond basic validation)  
- Distributed execution capabilities
- Advanced conflict resolution strategies
- Integration with monitoring and alerting systems

The goal is to maintain the elegant simplicity while adding robustness through battle-testing in real scenarios.
