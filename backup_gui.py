import os
import shutil
import hashlib
import logging
from datetime import datetime
import zipfile
from pathlib import Path
from dotenv import load_dotenv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Load environment variables from .env file
load_dotenv()

# Configuration
SOURCE_DIR = os.getenv('SOURCE_DIR', './source')
BACKUP_DIR = os.getenv('BACKUP_DIR', './backup')
LOG_FILE = os.getenv('LOG_FILE', 'backup.log')
MAX_BACKUPS = int(os.getenv('MAX_BACKUPS', 5))  # Maximum number of backup archives to keep

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_file_hash(filepath):
    """Generate MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def create_backup(source_dir, backup_dir):
    """Create a backup of files that have changed or are new."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = os.path.join(backup_dir, f'backup_{timestamp}')
    os.makedirs(backup_folder, exist_ok=True)
    
    # File to store hashes of backed-up files
    hash_file = os.path.join(backup_dir, 'file_hashes.txt')
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            existing_hashes = dict(line.strip().split('|', 1) for line in f)
    else:
        existing_hashes = {}
    
    new_hashes = {}
    changes = False
    
    for root, _, files in os.walk(source_dir):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, source_dir)
            dest_path = os.path.join(backup_folder, rel_path)
            
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            current_hash = get_file_hash(src_path)
            new_hashes[rel_path] = current_hash
            
            if rel_path not in existing_hashes or existing_hashes[rel_path] != current_hash:
                shutil.copy2(src_path, dest_path)  # Preserves metadata
                logging.info(f'Copied: {src_path} -> {dest_path}')
                changes = True
            else:
                logging.info(f'Skipped (unchanged): {src_path}')
    
    if changes:
        # Update the hash file with new hashes
        with open(hash_file, 'w') as f:
            for path, hash_val in new_hashes.items():
                f.write(f'{path}|{hash_val}\n')
        
        # Compress the backup folder
        zip_path = os.path.join(backup_dir, f'backup_{timestamp}.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(backup_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_folder)
                    zipf.write(file_path, arcname)
        logging.info(f'Backup compressed to: {zip_path}')
        
        # Remove the uncompressed backup folder
        shutil.rmtree(backup_folder)
        
        # Manage the number of backup archives
        manage_backups(backup_dir)
        return f"Backup completed successfully. Archive saved at: {zip_path}"
    else:
        logging.info('No changes detected. Backup skipped.')
        # Clean up empty backup folder
        shutil.rmtree(backup_folder)
        return "No changes detected. Backup skipped."

def manage_backups(backup_dir):
    """Keep only the latest MAX_BACKUPS archives."""
    backup_files = sorted(
        Path(backup_dir).glob('backup_*.zip'),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    while len(backup_files) > MAX_BACKUPS:
        oldest = backup_files.pop()
        oldest.unlink()
        logging.info(f'Removed old backup: {oldest}')

class BackupApp:
    def __init__(self, master):
        self.master = master
        master.title("Backup Automation Tool")

        # Source Directory
        self.label_source = tk.Label(master, text="Source Directory:")
        self.label_source.grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.entry_source = tk.Entry(master, width=50)
        self.entry_source.insert(0, SOURCE_DIR)
        self.entry_source.grid(row=0, column=1, padx=10, pady=5)
        
        self.button_source = tk.Button(master, text="Browse", command=self.browse_source)
        self.button_source.grid(row=0, column=2, padx=10, pady=5)

        # Backup Directory
        self.label_backup = tk.Label(master, text="Backup Directory:")
        self.label_backup.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.entry_backup = tk.Entry(master, width=50)
        self.entry_backup.insert(0, BACKUP_DIR)
        self.entry_backup.grid(row=1, column=1, padx=10, pady=5)
        
        self.button_backup = tk.Button(master, text="Browse", command=self.browse_backup)
        self.button_backup.grid(row=1, column=2, padx=10, pady=5)

        # Backup Button
        self.button_backup_run = tk.Button(master, text="Run Backup", command=self.run_backup)
        self.button_backup_run.grid(row=2, column=1, pady=20)

        # Status Label
        self.status_label = tk.Label(master, text="", fg="green")
        self.status_label.grid(row=3, column=0, columnspan=3, pady=10)

    def browse_source(self):
        """Open a dialog to select the source directory."""
        dirname = filedialog.askdirectory(initialdir=self.entry_source.get(), title="Select Source Directory")
        if dirname:
            self.entry_source.delete(0, tk.END)
            self.entry_source.insert(0, dirname)

    def browse_backup(self):
        """Open a dialog to select the backup directory."""
        dirname = filedialog.askdirectory(initialdir=self.entry_backup.get(), title="Select Backup Directory")
        if dirname:
            self.entry_backup.delete(0, tk.END)
            self.entry_backup.insert(0, dirname)

    def run_backup(self):
        """Trigger the backup process."""
        source_dir = self.entry_source.get()
        backup_dir = self.entry_backup.get()

        if not os.path.isdir(source_dir):
            messagebox.showerror("Error", "Source directory does not exist.")
            return
        
        if not os.path.isdir(backup_dir):
            messagebox.showerror("Error", "Backup directory does not exist.")
            return

        try:
            self.status_label.config(text="Backup in progress...", fg="blue")
            self.master.update_idletasks()  # Refresh the GUI

            result = create_backup(source_dir, backup_dir)
            self.status_label.config(text=result, fg="green")
        except Exception as e:
            logging.error(f'Error during backup: {e}')
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

if __name__ == '__main__':
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()