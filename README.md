# Backup Automation Tool

This is a Python-based backup automation tool graphical user interface (GUI). It allows users to back up files from a source directory to a destination directory, with features like incremental backups, compression, and retention management.

## Features

- **Incremental Backups**: Only backs up files that have changed or are new since the last backup.
- **Compression**: Compresses backup files into `.zip` archives to save space.
- **Retention Management**: Automatically deletes old backups to keep only the latest `MAX_BACKUPS` archives.
- **Logging**: Records all backup activities for monitoring and troubleshooting.
- **GUI Interface**: Provides a simple graphical interface for easier configuration and management.

## Clone the Repository

```bash
git clone https://github.com/MALTOisHERE/backup-automation-tool.git
cd backup-automation-tool
```

## Run the Script :

```bash
python backup_gui.py
```



