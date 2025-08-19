import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import struct
import math

class DD2Packer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Destruction Derby 2 - DIRINFO Packer")
        self.geometry("750x500")
        self.resizable(False, False)

        self.input_dir_var = tk.StringVar()
        self.output_file_var = tk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="1. Select the main folder with game data", padding="10")
        input_frame.pack(fill="x", pady=5)
        
        input_entry = ttk.Entry(input_frame, textvariable=self.input_dir_var, state="readonly", width=80)
        input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_input_btn = ttk.Button(input_frame, text="Browse...", command=self.select_input_dir)
        browse_input_btn.pack(side="left")

        output_frame = ttk.LabelFrame(main_frame, text="2. Select the output file (e.g., DIRINFO)", padding="10")
        output_frame.pack(fill="x", pady=5)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_file_var, state="readonly", width=80)
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_output_btn = ttk.Button(output_frame, text="Save As...", command=self.select_output_file)
        browse_output_btn.pack(side="left")

        self.pack_button = ttk.Button(main_frame, text="Build File", command=self.pack_files, state="disabled")
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
        directory = filedialog.askdirectory(title="Select Main Folder")
        if directory:
            self.input_dir_var.set(directory)
            self._log(f"Selected input folder: {directory}")
            self.check_paths()

    def select_output_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Save Archive File As",
            defaultextension="",
            initialfile="DIRINFO",
            filetypes=[("DIRINFO File", "DIRINFO"), ("All Files", "*.*")]
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
        
        SECTOR_SIZE = 2048
        HEADER_END_OFFSET = 0xAA0

        self._log("Step 1: Finding and sorting files...")
        all_files = []
        try:
            for root, dirs, files in os.walk(input_dir):
                dirs.sort()
                files.sort()
                for file in files:
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, input_dir)
                    formatted_path = relative_path.replace(os.path.sep, '\\').upper()
                    all_files.append((formatted_path, full_path))
            
            if not all_files:
                messagebox.showerror("Error", f"No files found in the folder:\n{input_dir}")
                return
            
            self._log(f"Found {len(all_files)} files to pack.")
        except Exception as e:
            messagebox.showerror("Error", f"Error while reading the input folder: {e}")
            return

        self._log("Step 2: Generating header and data write plan...")
        header_data = bytearray()
        write_tasks = []
        
        current_sector = math.ceil(HEADER_END_OFFSET / SECTOR_SIZE)
        self._log(f"Header ends at 0x{HEADER_END_OFFSET:X}. First available sector: {current_sector}")

        for i, (formatted_path, full_path) in enumerate(all_files):
            block_number = i + 1
            
            try:
                data_size = os.path.getsize(full_path)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot read the size of file {full_path}: {e}")
                return

            if block_number in [1, 2]:
                filename_len, padding_len = 17, 1
            elif block_number == 12:
                filename_len, padding_len = 16, 2
            else:
                filename_len, padding_len = 14, 4

            filename_bytes = formatted_path.encode('ascii')
            if len(filename_bytes) > filename_len:
                filename_bytes = filename_bytes[:filename_len]
            else:
                filename_bytes = filename_bytes.ljust(filename_len, b'\x00')

            sector_index = current_sector
            metadata_bytes = struct.pack('<HI', sector_index, data_size)

            header_block = filename_bytes + (b'\x00' * padding_len) + metadata_bytes
            header_data.extend(header_block)

            write_offset = sector_index * SECTOR_SIZE
            write_tasks.append((write_offset, full_path))
            
            self._log(f" - {formatted_path} -> Size: {data_size} B, Sector: {sector_index} (Offset: 0x{write_offset:X})")

            sectors_needed = math.ceil(data_size / SECTOR_SIZE)
            current_sector += sectors_needed

        self._log(f"Step 3: Writing the output file...")
        try:
            with open(output_file, 'wb') as f_out:
                f_out.write(header_data)
                
                if f_out.tell() < HEADER_END_OFFSET:
                    padding_to_add = HEADER_END_OFFSET - f_out.tell()
                    f_out.write(b'\x00' * padding_to_add)
                
                for offset, path in write_tasks:
                    f_out.seek(offset)
                    with open(path, 'rb') as f_in:
                        f_out.write(f_in.read())
            
            self._log("Done! The archive file was created successfully.")
            messagebox.showinfo("Success", "The archive file was created successfully!")

        except Exception as e:
            messagebox.showerror("Write Error", f"Failed to write the output file:\n{e}")

if __name__ == "__main__":
    app = DD2Packer()
    app.mainloop()
