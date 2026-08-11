# Workspace Indexing & Memory Safety Rules

- Do not parse, index, summarize, or stream binary database files (`.db`, `.sqlite`, `.sqlite3`), write-ahead log files (`-wal`, `-shm`), or raw log files into context memory.
- Exclude all runtime caches, virtual environments, and local trajectory stores from agent indexing loops.