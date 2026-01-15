import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
from pathlib import Path
import json
import shutil
import re
from typing import List, Dict, Any, Optional

try:
    from moviepy.editor import VideoFileClip  # type: ignore[import]
    MOVIEPY_AVAILABLE: bool = True
except ImportError:
    MOVIEPY_AVAILABLE: bool = False

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE: bool = True
except ImportError:
    PILLOW_AVAILABLE: bool = False

class MediaOrganizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Media File Organizer & Renamer")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        self.source_folder: str = ""
        self.files_data: List[Dict[str, Any]] = []
        self.backup_data: List[Dict[str, Any]] = []
        self.filtered_files: List[Dict[str, Any]] = []
        self.settings_file: str = "organizer_settings.json"
        self.sort_order: tk.StringVar
        
        self.create_ui()
        self.load_settings()
    
    def create_ui(self) -> None:
        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="📁 Media File Organizer", 
                              font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(pady=15)
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Folder selection
        folder_frame = tk.LabelFrame(main_frame, text="📂 Folder Selection", 
                                     font=('Arial', 10, 'bold'), bg='#f0f0f0', padx=10, pady=10)
        folder_frame.pack(fill='x', pady=(0, 15))
        
        self.folder_label = tk.Label(folder_frame, text="No folder selected", 
                                     bg='#f0f0f0', fg='#7f8c8d', font=('Arial', 9))
        self.folder_label.pack(side='left', fill='x', expand=True)
        
        select_btn = tk.Button(folder_frame, text="Select Folder", command=self.select_folder,
                              bg='#3498db', fg='white', font=('Arial', 10, 'bold'), 
                              cursor='hand2', padx=15, pady=5)
        select_btn.pack(side='right', padx=5)
        
        # Rename settings
        settings_frame = tk.LabelFrame(main_frame, text="⚙️ Rename Settings", 
                                       font=('Arial', 10, 'bold'), bg='#f0f0f0', padx=10, pady=10)
        settings_frame.pack(fill='x', pady=(0, 15))
        
        # Custom prefix
        prefix_frame = tk.Frame(settings_frame, bg='#f0f0f0')
        prefix_frame.pack(fill='x', pady=5)
        
        tk.Label(prefix_frame, text="Custom Prefix:", bg='#f0f0f0', 
                font=('Arial', 9)).pack(side='left', padx=(0, 10))
        self.prefix_entry = tk.Entry(prefix_frame, font=('Arial', 9), width=25)
        self.prefix_entry.pack(side='left', padx=(0, 20))
        self.prefix_entry.insert(0, "Trip")
        
        # Add date checkbox
        self.add_date_var = tk.BooleanVar(value=False)
        date_check = tk.Checkbutton(prefix_frame, text="Add Date", variable=self.add_date_var,
                                   bg='#f0f0f0', font=('Arial', 9))
        date_check.pack(side='left', padx=10)
        
        # Add time checkbox
        self.add_time_var = tk.BooleanVar(value=False)
        time_check = tk.Checkbutton(prefix_frame, text="Add Time", variable=self.add_time_var,
                                   bg='#f0f0f0', font=('Arial', 9))
        time_check.pack(side='left', padx=10)
        
        # Counter digits
        counter_frame = tk.Frame(settings_frame, bg='#f0f0f0')
        counter_frame.pack(fill='x', pady=5)
        
        tk.Label(counter_frame, text="Counter Digits:", bg='#f0f0f0', 
                font=('Arial', 9)).pack(side='left', padx=(0, 10))
        self.counter_var = tk.StringVar(value="3")
        counter_combo = ttk.Combobox(counter_frame, textvariable=self.counter_var, 
                                    values=['2', '3', '4', '5'], width=10, state='readonly')
        counter_combo.pack(side='left')
        
        # Start counter
        tk.Label(counter_frame, text="Start From:", bg='#f0f0f0', 
                font=('Arial', 9)).pack(side='left', padx=(20, 10))
        self.start_counter_var = tk.StringVar(value="1")
        start_entry = tk.Entry(counter_frame, textvariable=self.start_counter_var, width=8, font=('Arial', 9))
        start_entry.pack(side='left')
        
        # Organize by type checkbox
        organize_frame = tk.Frame(settings_frame, bg='#f0f0f0')
        organize_frame.pack(fill='x', pady=5)
        
        self.organize_var = tk.BooleanVar(value=False)
        organize_check = tk.Checkbutton(organize_frame, text="Organize by File Type (Separate Folders)",
                                       variable=self.organize_var, bg='#f0f0f0', font=('Arial', 9))
        organize_check.pack(side='left')
        
        # Handle duplicates
        tk.Label(organize_frame, text="Duplicates:", bg='#f0f0f0', 
                font=('Arial', 9)).pack(side='left', padx=(20, 10))
        self.duplicate_var = tk.StringVar(value="skip")
        dup_combo = ttk.Combobox(organize_frame, textvariable=self.duplicate_var, 
                                values=['skip', 'overwrite', 'rename'], width=12, state='readonly')
        dup_combo.pack(side='left')
        
        # Sort order
        sort_frame = tk.Frame(settings_frame, bg='#f0f0f0')
        sort_frame.pack(fill='x', pady=5)
        
        tk.Label(sort_frame, text="Sort Files By:", bg='#f0f0f0', 
                font=('Arial', 9)).pack(side='left', padx=(0, 10))
        self.sort_order = tk.StringVar(value="creation_time")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_order, 
                                 values=['creation_time', 'original_date', 'filename', 'size'], 
                                 width=15, state='readonly')
        sort_combo.pack(side='left')
        
        info_label = tk.Label(sort_frame, text="ℹ️ 'original_date' extracts from EXIF/metadata",
                            bg='#f0f0f0', fg='#7f8c8d', font=('Arial', 8))
        info_label.pack(side='left', padx=10)
        
        # Filter and settings buttons
        button_row = tk.Frame(settings_frame, bg='#f0f0f0')
        button_row.pack(fill='x', pady=10)
        
        preview_btn = tk.Button(button_row, text="🔍 Preview Changes", command=self.preview_changes,
                               bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), 
                               cursor='hand2', padx=20, pady=5)
        preview_btn.pack(side='left', padx=5)
        
        filter_btn = tk.Button(button_row, text="🔎 Filter Files", command=self.show_filter_dialog,
                              bg='#9b59b6', fg='white', font=('Arial', 10, 'bold'), 
                              cursor='hand2', padx=20, pady=5)
        filter_btn.pack(side='left', padx=5)
        
        save_settings_btn = tk.Button(button_row, text="💾 Save Settings", command=self.save_settings,
                                     bg='#f39c12', fg='white', font=('Arial', 10, 'bold'), 
                                     cursor='hand2', padx=20, pady=5)
        save_settings_btn.pack(side='left', padx=5)
        
        # Preview area
        preview_frame = tk.LabelFrame(main_frame, text="👁️ Preview", 
                                     font=('Arial', 10, 'bold'), bg='#f0f0f0', padx=10, pady=10)
        preview_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Scrollbar
        scroll = tk.Scrollbar(preview_frame)
        scroll.pack(side='right', fill='y')
        
        self.preview_text = tk.Text(preview_frame, height=15, font=('Consolas', 9),
                                   yscrollcommand=scroll.set, wrap='none')
        self.preview_text.pack(fill='both', expand=True)
        scroll.config(command=self.preview_text.yview)
        
        # Status bar
        self.status_label = tk.Label(main_frame, text="Ready", bg='#ecf0f1', 
                                     font=('Arial', 9), anchor='w', padx=10, pady=5)
        self.status_label.pack(fill='x', pady=(0, 10))
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        apply_btn = tk.Button(button_frame, text="✅ Apply Changes", command=self.apply_changes,
                             bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'), 
                             cursor='hand2', padx=30, pady=8)
        apply_btn.pack(side='left', padx=5)
        
        undo_btn = tk.Button(button_frame, text="↶ Undo Last", command=self.undo_changes,
                            bg='#95a5a6', fg='white', font=('Arial', 11, 'bold'), 
                            cursor='hand2', padx=30, pady=8)
        undo_btn.pack(side='left', padx=5)
        
        export_btn = tk.Button(button_frame, text="📤 Export Preview", command=self.export_preview,
                              bg='#16a085', fg='white', font=('Arial', 11, 'bold'), 
                              cursor='hand2', padx=30, pady=8)
        undo_btn.pack(side='left', padx=5)
    
    def select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Folder with Media Files")
        if folder:
            self.source_folder = folder
            self.folder_label.config(text=folder, fg='#2c3e50')
            self.status_label.config(text=f"Folder selected: {folder}")
            self.load_files()
    
    def load_files(self) -> None:
        if not self.source_folder:
            return
        
        self.files_data = []
        extensions = {'.jpg', '.jpeg', '.png', '.mp4', '.mov', '.avi', '.mkv', '.3gp', '.heic', '.gif', '.webp'}
        
        for file in os.listdir(self.source_folder):
            file_path = os.path.join(self.source_folder, file)
            if os.path.isfile(file_path):
                ext = Path(file).suffix.lower()
                if ext in extensions:
                    # Get file info
                    try:
                        stat = os.stat(file_path)
                        created_time = stat.st_mtime  # Using modification time as proxy
                        file_size = stat.st_size
                        duration = 0
                        
                        # Try to get original date from EXIF/metadata
                        original_date = self.get_original_date(file_path, ext)
                        
                        # Get video duration if it's a video file
                        if self.get_file_type(ext) == 'Video' and MOVIEPY_AVAILABLE:
                            try:
                                clip: Any = VideoFileClip(file_path)  # type: ignore[name-defined]
                                duration = clip.duration
                                clip.close()
                            except:
                                duration = 0
                        
                        self.files_data.append({
                            'original': file,
                            'path': file_path,
                            'ext': ext,
                            'time': created_time,
                            'original_time': original_date if original_date else created_time,
                            'size': file_size,
                            'type': self.get_file_type(ext),
                            'duration': duration
                        })
                    except Exception as e:
                        print(f"Error loading {file}: {e}")
        
        # Sort based on selected option
        sort_by = self.sort_order.get()
        if sort_by == 'original_date':
            self.files_data.sort(key=lambda x: x['original_time'])
        elif sort_by == 'filename':
            self.files_data.sort(key=lambda x: x['original'])
        elif sort_by == 'size':
            self.files_data.sort(key=lambda x: x['size'])
        else:  # creation_time
            self.files_data.sort(key=lambda x: x['time'])
        
        self.filtered_files = self.files_data.copy()
        
        total_size = sum(f['size'] for f in self.files_data)
        size_mb = total_size / (1024 * 1024)
        
        # Calculate total video duration
        video_files = [f for f in self.files_data if f['type'] == 'Video']
        total_duration = sum(f.get('duration', 0) for f in video_files)
        duration_str = self.format_duration(total_duration)
        
        status_msg = f"Loaded {len(self.files_data)} files ({size_mb:.2f} MB)"
        if video_files:
            status_msg += f" | {len(video_files)} videos ({duration_str})"
        
        self.status_label.config(text=status_msg)
    
    def get_file_type(self, ext: str) -> str:
        video_ext = {'.mp4', '.mov', '.avi', '.mkv', '.3gp'}
        photo_ext = {'.jpg', '.jpeg', '.png', '.heic', '.gif', '.webp'}
        
        if ext in video_ext:
            return 'Video'
        elif ext in photo_ext:
            return 'Photo'
        return 'Other'
    
    def get_original_date(self, file_path: str, ext: str) -> Optional[float]:
        """Extract original creation date from EXIF data for photos/videos"""
        try:
            # For photos - try EXIF data
            if ext.lower() in {'.jpg', '.jpeg', '.png', '.heic'} and PILLOW_AVAILABLE:
                try:
                    image = Image.open(file_path)
                    exif_data = image._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            if tag == 'DateTimeOriginal' or tag == 'DateTime':
                                # Parse datetime string like '2023:12:01 14:30:00'
                                dt = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                                return dt.timestamp()
                except:
                    pass
            
            # For videos - try to get metadata
            if ext.lower() in {'.mp4', '.mov', '.avi', '.mkv'} and MOVIEPY_AVAILABLE:
                try:
                    clip: Any = VideoFileClip(file_path)  # type: ignore[name-defined]
                    # Check if creation time is available in metadata
                    if hasattr(clip, 'metadata') and clip.metadata:
                        creation_date = clip.metadata.get('creation_time')
                        if creation_date:
                            dt = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                            clip.close()
                            return dt.timestamp()
                    clip.close()
                except:
                    pass
        except:
            pass
        
        return None
    
    def format_size(self, size_bytes: float) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def format_duration(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        if seconds == 0:
            return "0:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def preview_changes(self) -> None:
        files_to_process = self.filtered_files if self.filtered_files else self.files_data
        
        if not files_to_process:
            messagebox.showwarning("Warning", "No files to preview!")
            return
        
        self.preview_text.delete('1.0', 'end')
        prefix = self.prefix_entry.get().strip()
        add_date = self.add_date_var.get()
        add_time = self.add_time_var.get()
        counter_digits = int(self.counter_var.get())
        organize = self.organize_var.get()
        
        try:
            start_counter = int(self.start_counter_var.get())
        except ValueError:
            start_counter = 1
            self.start_counter_var.set("1")
        
        preview = "ORIGINAL → NEW NAME (Size | Type | Duration)\n"
        preview += "=" * 90 + "\n\n"
        
        counter = start_counter
        total_video_duration = 0
        sort_by = self.sort_order.get()
        
        for file_data in files_to_process:
            original = file_data['original']
            ext = file_data['ext']
            file_type = file_data['type']
            size = self.format_size(file_data['size'])
            duration = file_data.get('duration', 0)
            
            # Build new name - use original_time for date if using original_date sort
            date_time_to_use = file_data['original_time'] if sort_by == 'original_date' else file_data['time']
            
            # Build new name
            new_name = prefix if prefix else "File"
            
            if add_date:
                date_str = datetime.fromtimestamp(date_time_to_use).strftime('%Y%m%d')
                new_name += f"_{date_str}"
            
            if add_time:
                time_str = datetime.fromtimestamp(date_time_to_use).strftime('%H%M%S')
                new_name += f"_{time_str}"
            
            new_name += f"_{str(counter).zfill(counter_digits)}{ext}"
            
            if organize:
                new_name = f"{file_type}/{new_name}"
            
            duration_info = ""
            if file_type == 'Video' and duration > 0:
                duration_info = f" | {self.format_duration(duration)}"
                total_video_duration += duration
            
            preview += f"{original}\n  → {new_name} ({size} | {file_type}{duration_info})\n\n"
            counter += 1
        
        self.preview_text.insert('1.0', preview)
        total_size = sum(f['size'] for f in files_to_process)
        size_mb = total_size / (1024 * 1024)
        
        status_msg = f"Preview: {len(files_to_process)} files ({size_mb:.2f} MB)"
        if total_video_duration > 0:
            status_msg += f" | Total video duration: {self.format_duration(total_video_duration)}"
        
        self.status_label.config(text=status_msg)
    
    def apply_changes(self) -> None:
        files_to_process = self.filtered_files if self.filtered_files else self.files_data
        
        if not files_to_process:
            messagebox.showwarning("Warning", "No files to process!")
            return
        
        confirm = messagebox.askyesno("Confirm", 
                                      f"Are you sure you want to rename {len(files_to_process)} files?\n\n"
                                      "This action can be undone using 'Undo Last' button.")
        if not confirm:
            return
        
        prefix = self.prefix_entry.get().strip()
        add_date = self.add_date_var.get()
        add_time = self.add_time_var.get()
        counter_digits = int(self.counter_var.get())
        organize = self.organize_var.get()
        duplicate_action = self.duplicate_var.get()
        
        try:
            start_counter = int(self.start_counter_var.get())
        except ValueError:
            start_counter = 1
        
        self.backup_data = []
        counter = start_counter
        success_count = 0
        skipped_count = 0
        errors: List[str] = []
        sort_by = self.sort_order.get()
        
        try:
            for file_data in files_to_process:
                original_path = file_data['path']
                ext = file_data['ext']
                file_type = file_data['type']
                
                # Use original_time for date if using original_date sort
                date_time_to_use = file_data['original_time'] if sort_by == 'original_date' else file_data['time']
                
                # Build new name
                new_name = prefix if prefix else "File"
                
                if add_date:
                    date_str = datetime.fromtimestamp(date_time_to_use).strftime('%Y%m%d')
                    new_name += f"_{date_str}"
                
                if add_time:
                    time_str = datetime.fromtimestamp(date_time_to_use).strftime('%H%M%S')
                    new_name += f"_{time_str}"
                
                new_name += f"_{str(counter).zfill(counter_digits)}{ext}"
                
                # Handle folder organization
                if organize:
                    type_folder = os.path.join(self.source_folder, file_type)
                    os.makedirs(type_folder, exist_ok=True)
                    new_path = os.path.join(type_folder, new_name)
                else:
                    new_path = os.path.join(self.source_folder, new_name)
                
                # Handle duplicates
                if os.path.exists(new_path) and original_path != new_path:
                    if duplicate_action == 'skip':
                        skipped_count += 1
                        counter += 1
                        continue
                    elif duplicate_action == 'rename':
                        base, ext_part = os.path.splitext(new_path)
                        dup_counter = 1
                        while os.path.exists(new_path):
                            new_path = f"{base}_{dup_counter}{ext_part}"
                            dup_counter += 1
                    # 'overwrite' will just proceed
                
                # Backup info for undo
                self.backup_data.append({
                    'old': original_path,
                    'new': new_path,
                    'was_created_folder': organize and not os.path.exists(os.path.dirname(new_path))
                })
                
                # Rename
                try:
                    os.rename(original_path, new_path)
                    success_count += 1
                except Exception as e:
                    errors.append(f"{file_data['original']}: {str(e)}")
                
                counter += 1
            
            msg = f"Successfully renamed {success_count} files!"
            if skipped_count > 0:
                msg += f"\n{skipped_count} files skipped (duplicates)."
            if errors:
                msg += f"\n{len(errors)} errors occurred."
            
            messagebox.showinfo("Complete", msg)
            
            if errors:
                error_msg = "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more errors"
                messagebox.showwarning("Errors Occurred", error_msg)
            
            self.status_label.config(text=f"Completed: {success_count} renamed, {skipped_count} skipped")
            self.load_files()  # Reload
            self.preview_changes()  # Update preview
            
        except Exception as e:
            messagebox.showerror("Error", f"Critical error occurred: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)}")
    
    def undo_changes(self) -> None:
        if not self.backup_data:
            messagebox.showinfo("Info", "No changes to undo!")
            return
        
        confirm = messagebox.askyesno("Confirm Undo", 
                                      "Are you sure you want to undo the last renaming operation?")
        if not confirm:
            return
        
        success_count = 0
        errors: List[str] = []
        
        try:
            for backup in reversed(self.backup_data):
                try:
                    if os.path.exists(backup['new']):
                        os.rename(backup['new'], backup['old'])
                        success_count += 1
                except Exception as e:
                    errors.append(f"{backup['new']}: {str(e)}")
            
            msg = f"Successfully undone {success_count} changes!"
            if errors:
                msg += f"\n{len(errors)} errors occurred."
            
            messagebox.showinfo("Undo Complete", msg)
            
            if errors:
                error_msg = "\n".join(errors[:10])
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more errors"
                messagebox.showwarning("Errors During Undo", error_msg)
            
            self.backup_data = []
            self.load_files()
            self.preview_changes()
            self.status_label.config(text=f"Undo completed: {success_count} restored")
            
        except Exception as e:
            messagebox.showerror("Error", f"Critical error during undo: {str(e)}")
    
    def show_filter_dialog(self) -> None:
        """Show dialog to filter files"""
        if not self.files_data:
            messagebox.showwarning("Warning", "Please select a folder first!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Filter Files")
        dialog.geometry("500x400")
        dialog.configure(bg='#f0f0f0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Filter by type
        type_frame = tk.LabelFrame(dialog, text="File Type", bg='#f0f0f0', padx=10, pady=10)
        type_frame.pack(fill='x', padx=20, pady=10)
        
        video_var = tk.BooleanVar(value=True)
        photo_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(type_frame, text="Videos", variable=video_var, bg='#f0f0f0').pack(anchor='w')
        tk.Checkbutton(type_frame, text="Photos", variable=photo_var, bg='#f0f0f0').pack(anchor='w')
        
        # Filter by extension
        ext_frame = tk.LabelFrame(dialog, text="File Extension (comma-separated)", bg='#f0f0f0', padx=10, pady=10)
        ext_frame.pack(fill='x', padx=20, pady=10)
        
        ext_entry = tk.Entry(ext_frame, font=('Arial', 9))
        ext_entry.pack(fill='x')
        ext_entry.insert(0, "e.g., .mp4, .jpg, .png")
        
        # Filter by filename pattern
        pattern_frame = tk.LabelFrame(dialog, text="Filename Pattern (regex)", bg='#f0f0f0', padx=10, pady=10)
        pattern_frame.pack(fill='x', padx=20, pady=10)
        
        pattern_entry = tk.Entry(pattern_frame, font=('Arial', 9))
        pattern_entry.pack(fill='x')
        
        # Filter by size
        size_frame = tk.LabelFrame(dialog, text="File Size (MB)", bg='#f0f0f0', padx=10, pady=10)
        size_frame.pack(fill='x', padx=20, pady=10)
        
        size_row = tk.Frame(size_frame, bg='#f0f0f0')
        size_row.pack(fill='x')
        
        tk.Label(size_row, text="Min:", bg='#f0f0f0').pack(side='left')
        min_size_entry = tk.Entry(size_row, width=10)
        min_size_entry.pack(side='left', padx=5)
        
        tk.Label(size_row, text="Max:", bg='#f0f0f0').pack(side='left', padx=(20, 0))
        max_size_entry = tk.Entry(size_row, width=10)
        max_size_entry.pack(side='left', padx=5)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='#f0f0f0')
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        def apply_filter():
            self.filtered_files = []
            
            for file_data in self.files_data:
                # Type filter
                if file_data['type'] == 'Video' and not video_var.get():
                    continue
                if file_data['type'] == 'Photo' and not photo_var.get():
                    continue
                
                # Extension filter
                ext_text = ext_entry.get().strip()
                if ext_text and not ext_text.startswith('e.g.'):
                    exts = [e.strip().lower() for e in ext_text.split(',')]
                    if file_data['ext'] not in exts:
                        continue
                
                # Pattern filter
                pattern_text = pattern_entry.get().strip()
                if pattern_text:
                    try:
                        if not re.search(pattern_text, file_data['original'], re.IGNORECASE):
                            continue
                    except re.error:
                        pass
                
                # Size filter
                file_size_mb = file_data['size'] / (1024 * 1024)
                
                min_text = min_size_entry.get().strip()
                if min_text:
                    try:
                        if file_size_mb < float(min_text):
                            continue
                    except ValueError:
                        pass
                
                max_text = max_size_entry.get().strip()
                if max_text:
                    try:
                        if file_size_mb > float(max_text):
                            continue
                    except ValueError:
                        pass
                
                self.filtered_files.append(file_data)
            
            messagebox.showinfo("Filter Applied", 
                              f"Filtered to {len(self.filtered_files)} of {len(self.files_data)} files")
            self.status_label.config(text=f"Filtered: {len(self.filtered_files)} files")
            dialog.destroy()
            self.preview_changes()
        
        def reset_filter():
            self.filtered_files = self.files_data.copy()
            self.status_label.config(text=f"Filter reset: {len(self.files_data)} files")
            dialog.destroy()
            self.preview_changes()
        
        tk.Button(btn_frame, text="Apply Filter", command=apply_filter,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), 
                 cursor='hand2', padx=20, pady=5).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Reset Filter", command=reset_filter,
                 bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'), 
                 cursor='hand2', padx=20, pady=5).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'), 
                 cursor='hand2', padx=20, pady=5).pack(side='left', padx=5)
    
    def export_preview(self) -> None:
        """Export preview to text file"""
        content = self.preview_text.get('1.0', 'end-1c')
        if not content.strip():
            messagebox.showwarning("Warning", "No preview to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Preview",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Preview exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def save_settings(self) -> None:
        """Save current settings to file"""
        settings = {
            'prefix': self.prefix_entry.get(),
            'add_date': self.add_date_var.get(),
            'add_time': self.add_time_var.get(),
            'counter_digits': self.counter_var.get(),
            'start_counter': self.start_counter_var.get(),
            'organize_by_type': self.organize_var.get(),
            'duplicate_action': self.duplicate_var.get(),
            'sort_order': self.sort_order.get()
        }
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def load_settings(self) -> None:
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                self.prefix_entry.delete(0, 'end')
                self.prefix_entry.insert(0, settings.get('prefix', 'Trip'))
                self.add_date_var.set(settings.get('add_date', False))
                self.add_time_var.set(settings.get('add_time', False))
                self.counter_var.set(settings.get('counter_digits', '3'))
                self.start_counter_var.set(settings.get('start_counter', '1'))
                self.organize_var.set(settings.get('organize_by_type', False))
                self.duplicate_var.set(settings.get('duplicate_action', 'skip'))
                self.sort_order.set(settings.get('sort_order', 'creation_time'))
            except Exception as e:
                print(f"Error loading settings: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MediaOrganizerApp(root)
    root.mainloop()