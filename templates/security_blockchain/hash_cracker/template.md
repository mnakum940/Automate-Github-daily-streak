# {project_name}

{description}

## Security Concepts
- **hashing**: One-way encryption functions
- **brute-force**: Exhaustive key search
- **dictionary-attack**: Using wordlists
- **salt**: Random data added to password before hashing

## Technologies Used
- Python 3.11+
- hashlib
- itertools
- multiprocessing (for performance)

## Core Features
1. **Hash Generator**: Support MD5, SHA-1, SHA-256
2. **Brute Force Mode**: Try all combinations of chars
3. **Dictionary Mode**: Check against wordlist (e.g., rockyou.txt)
4. **Benchmark**: Measure hashrate

## Implementation Guide

### 1. Hash Function
```python
import hashlib

def hash_password(password: str, algo: str = 'sha256') -> str:
    if algo == 'md5':
        return hashlib.md5(password.encode()).hexdigest()
    # ...
```

### 2. Brute Force Logic
Use `itertools.product` to generate combinations.

### 3. Optimization
Use `multiprocessing.Pool` to parallelize the cracking process.

## Safety Warning
This tool is for educational purposes only. Do not use for illegal activities.
