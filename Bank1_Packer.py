import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import struct
import wave
import re

class SBKPacker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SBK Sound Bank Packer (Corrected for Large Files)")
        self.geometry("750x500")
        self.resizable(False, False)

        self.input_dir_var = tk.StringVar()
        self.output_file_var = tk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="1. Select folder with WAVE files (e.g., sound_001.wav)", padding="10")
        input_frame.pack(fill="x", pady=5)
        
        input_entry = ttk.Entry(input_frame, textvariable=self.input_dir_var, state="readonly", width=80)
        input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_input_btn = ttk.Button(input_frame, text="Browse...", command=self.select_input_dir)
        browse_input_btn.pack(side="left")

        output_frame = ttk.LabelFrame(main_frame, text="2. Select output file", padding="10")
        output_frame.pack(fill="x", pady=5)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_file_var, state="readonly", width=80)
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_output_btn = ttk.Button(output_frame, text="Save As...", command=self.select_output_file)
        browse_output_btn.pack(side="left")

        self.pack_button = ttk.Button(main_frame, text="Build SBK File", command=self.pack_files, state="disabled")
        self.pack_button.pack(pady=20, ipady=10, fill="x")
        
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill="both", expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)

    def _log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.update_idletasks()
        
    def check_paths(self):
        if self.input_dir_var.get() and self.output_file_var.get():
            self.pack_button.config(state="normal")
        else:
            self.pack_button.config(state="disabled")

    def select_input_dir(self):
        directory = filedialog.askdirectory(title="Select Folder with WAVE Files")
        if directory:
            self.input_dir_var.set(directory)
            self._log(f"Selected input folder: {directory}")
            self.check_paths()

    def select_output_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Save Archive File As",
            defaultextension=".sbk",
            initialfile="BANK1.SBK",
            filetypes=[("SBK Archive", "*.sbk"), ("All Files", "*.*")]
        )
        if filepath:
            self.output_file_var.set(filepath)
            self._log(f"Selected output file: {filepath}")
            self.check_paths()

    def pack_files(self):
        input_dir = self.input_dir_var.get()
        output_file = self.output_file_var.get()
        self.log_text.config(state="normal")
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state="disabled")

        self._log("Step 1: Searching for files...")
        try:
            files_to_pack = []
            for filename in os.listdir(input_dir):
                match = re.match(r"sound_(\d+)\.wav$", filename, re.IGNORECASE)
                if match:
                    file_number = int(match.group(1))
                    files_to_pack.append((file_number, os.path.join(input_dir, filename)))
            
            if not files_to_pack:
                messagebox.showerror("Error", f"No files found with the format 'sound_number.wav' in the folder:\n{input_dir}")
                return
            
            files_to_pack.sort()
            num_files = len(files_to_pack)
            self._log(f"Found {num_files} files to pack.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error while reading the folder: {e}")
            return

        self._log("Step 2: Preparing data...")
        
        HEADER_SIZE = 16
        INDEX_ENTRY_SLOT_SIZE = 28
        index_table_size = num_files * INDEX_ENTRY_SLOT_SIZE
        data_block_start_offset = HEADER_SIZE + index_table_size
        
        index_entries_data = []
        data_block = bytearray()
        
        current_absolute_offset = data_block_start_offset

        for num, path in files_to_pack:
            try:
                with open(path, 'rb') as f_wav:
                    wav_content = f_wav.read()
                
                with wave.open(path, 'rb') as wav_obj:
                    sample_rate = wav_obj.getframerate()
                    num_frames = wav_obj.getnframes()
                    
                    duration_seconds = 0
                    if sample_rate > 0:
                        duration_seconds = num_frames / float(sample_rate)
                    
                    duration_flag = 1 if duration_seconds >= 1.0 else 0

                file_size = len(wav_content)
                data_block.extend(wav_content)

                # --- CRITICAL FIX: Use 4-byte unsigned ints for all fields ---
                # The format string '<5I' means: Little-endian, 5 Unsigned Integers
                entry_bytes = struct.pack('<5I',
                    current_absolute_offset, # Address (4 bytes)
                    file_size,               # Size (4 bytes)
                    duration_flag,           # Duration flag (4 bytes)
                    sample_rate,             # Sample rate (4 bytes)
                    1                        # Unknown flag (4 bytes, default to 1)
                )
                index_entries_data.append(entry_bytes)
                
                self._log(f" - {os.path.basename(path)} -> Offset: 0x{current_absolute_offset:X}, Size: {file_size} B")
                
                current_absolute_offset += file_size
                
            except Exception as e:
                 messagebox.showerror("Error", f"Could not process file {path}:\n{e}")
                 return

        self._log("Step 3: Building header...")
        data_block_size = len(data_block)
        total_archive_size = HEADER_SIZE + index_table_size + data_block_size

        header = bytearray(16)
        struct.pack_into('<H', header, 12, num_files)
        
        byte_lo = total_archive_size & 0xFF
        byte_mid = (total_archive_size >> 8) & 0xFF
        byte_hi = (total_archive_size >> 16) & 0xFF
        
        header[8] = byte_lo
        header[9] = byte_mid
        header[10] = byte_hi
        
        self._log(f"Total archive size: {total_archive_size} bytes.")

        self._log("Step 4: Writing file...")
        try:
            with open(output_file, 'wb') as f_out:
                f_out.write(header)
                for entry_data in index_entries_data:
                    f_out.write(entry_data)
                    f_out.write(b'\x00' * 8) # 8 bytes of padding after each 20-byte entry
                f_out.write(data_block)
            self._log("Done! The archive file was created successfully.")
            messagebox.showinfo("Success", "The archive file was created successfully!")
        except Exception as e:
            messagebox.showerror("Write Error", f"Failed to write the output file:\n{e}")

if __name__ == "__main__":
    app = SBKPacker()
    app.mainloop()
