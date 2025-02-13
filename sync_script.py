import time
import sys
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, source_path, destination_path):
        self.source_path = source_path
        self.destination_path = destination_path

    def on_created(self, event):
        if event.is_directory:
            return
        
        rel_path = os.path.relpath(event.src_path, self.source_path)
        dest_path = os.path.join(self.destination_path, rel_path)
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        try:
            shutil.copy2(event.src_path, dest_path)
            logging.info(f"Created: {rel_path}")
        except Exception as e:
            logging.error(f"Error creating {rel_path}: {str(e)}")

    def on_modified(self, event):
        if event.is_directory:
            return
            
        rel_path = os.path.relpath(event.src_path, self.source_path)
        dest_path = os.path.join(self.destination_path, rel_path)
        
        try:
            shutil.copy2(event.src_path, dest_path)
            logging.info(f"Modified: {rel_path}")
        except Exception as e:
            logging.error(f"Error modifying {rel_path}: {str(e)}")

    def on_deleted(self, event):
        try:
            rel_path = os.path.relpath(event.src_path, self.source_path)
            dest_path = os.path.join(self.destination_path, rel_path)
            
            if os.path.exists(dest_path):
                if event.is_directory:
                    shutil.rmtree(dest_path)
                    logging.info(f"Deleted directory: {rel_path}")
                else:
                    os.remove(dest_path)
                    logging.info(f"Deleted file: {rel_path}")
                
                # Clean up empty parent directories
                parent_dir = os.path.dirname(dest_path)
                while parent_dir != self.destination_path:
                    if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
                        logging.info(f"Removed empty directory: {os.path.relpath(parent_dir, self.destination_path)}")
                    parent_dir = os.path.dirname(parent_dir)
            
        except Exception as e:
            logging.error(f"Error during deletion of {rel_path}: {str(e)}")

    def on_moved(self, event):
        try:
            # Handle source path
            rel_src_path = os.path.relpath(event.src_path, self.source_path)
            src_dest_path = os.path.join(self.destination_path, rel_src_path)
            
            # Handle destination path
            rel_dest_path = os.path.relpath(event.dest_path, self.source_path)
            dest_dest_path = os.path.join(self.destination_path, rel_dest_path)
            
            if os.path.exists(src_dest_path):
                # Create destination directory if it doesn't exist
                os.makedirs(os.path.dirname(dest_dest_path), exist_ok=True)
                
                # Move the file or directory
                shutil.move(src_dest_path, dest_dest_path)
                logging.info(f"Moved: {rel_src_path} -> {rel_dest_path}")
                
                # Clean up empty directories
                self._cleanup_empty_dirs(os.path.dirname(src_dest_path))
                
        except Exception as e:
            logging.error(f"Error during move operation: {str(e)}")

    def _cleanup_empty_dirs(self, directory):
        while directory != self.destination_path:
            if os.path.exists(directory) and not os.listdir(directory):
                os.rmdir(directory)
                logging.info(f"Removed empty directory: {os.path.relpath(directory, self.destination_path)}")
            directory = os.path.dirname(directory)

def initial_sync(source_path, destination_path):
    """Perform initial synchronization of all files"""
    for root, dirs, files in os.walk(source_path):
        rel_path = os.path.relpath(root, source_path)
        dest_dir = os.path.join(destination_path, rel_path)
        os.makedirs(dest_dir, exist_ok=True)
        
        for file in files:
            source_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, file)
            shutil.copy2(source_file, dest_file)
    
    logging.info("Initial synchronization completed")

def start_sync(source_path, destination_path):
    if not os.path.exists(source_path):
        raise ValueError(f"Source path does not exist: {source_path}")
    if not os.path.exists(destination_path):
        raise ValueError(f"Destination path does not exist: {destination_path}")

    initial_sync(source_path, destination_path)
    
    event_handler = FileChangeHandler(source_path, destination_path)
    observer = Observer()
    observer.schedule(event_handler, source_path, recursive=True)
    observer.start()
    
    logging.info(f"Started watching {source_path}")
    logging.info(f"Syncing to {destination_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Sync stopped by user")
    
    observer.join()

if __name__ == "__main__":
    # Replace these paths with your actual source and destination paths
    SOURCE_PATH = r"E:\work_destination"  # Your SSD path
    DESTINATION_PATH = r"\\user\F\test_server"  # Your network HDD path
    
    start_sync(SOURCE_PATH, DESTINATION_PATH)



    # SOURCE_PATH = r"E:\work_destination"  # Your SSD path
    # DESTINATION_PATH = r"\\user\F\test_server"