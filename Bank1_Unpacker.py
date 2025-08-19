import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import struct
from pathlib import Path

class SBKUnpacker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SBK Sound Bank Unpacker")
        self.geometry("750x500")
        self.resizable(False, False)

        self.input_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="1. Select SBK file", padding="10")
        input_frame.pack(fill="x", pady=5)
        
        input_entry = ttk.Entry(input_frame, textvariable=self.input_file_var, state="readonly", width=80)
        input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_input_btn = ttk.Button(input_frame, text="Browse...", command=self.select_input_file)
        browse_input_btn.pack(side="left")

        output_frame = ttk.LabelFrame(main_frame, text="2. Select destination folder", padding="10")
        output_frame.pack(fill="x", pady=5)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, state="readonly", width=80)
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_output_btn = ttk.Button(output_frame, text="Browse...", command=self.select_output_dir)
        browse_output_btn.pack(side="left")

        self.unpack_button = ttk.Button(main_frame, text="Unpack Files", command=self.unpack_files, state="disabled")
        self.unpack_button.pack(pady=20, ipady=10, fill="x")
        
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
        if self.input_file_var.get() and self.output_dir_var.get():
            self.unpack_button.config(state="normal")
        else:
            self.unpack_button.config(state="disabled")

    def select_input_file(self):
        filepath = filedialog.askopenfilename(
            title="Select SBK File",
            filetypes=[("SBK Sound Bank", "*.sbk"), ("All Files", "*.*")]
        )
        if filepath:
            self.input_file_var.set(filepath)
            self._log(f"Selected input file: {filepath}")
            self.check_paths()

    def select_output_dir(self):
        directory = filedialog.askdirectory(title="Select Destination Folder")
        if directory:
            self.output_dir_var.set(directory)
            self._log(f"Selected output folder: {directory}")
            self.check_paths()

    def unpack_files(self):
        input_file = self.input_file_var.get()
        output_dir = self.output_dir_var.get()

        self.log_text.config(state="normal")
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state="disabled")
        
        try:
            with open(input_file, 'rb') as f:
                archive_data = f.read()
            
            archive_size = len(archive_data)
            self._log(f"Read {archive_size / 1024:.2f} KB of data.")

            os.makedirs(output_dir, exist_ok=True)
            self._log(f"Files will be saved to the folder: '{output_dir}'")
            
            extracted_count = 0
            current_pos = 0
            RIFF_SIGNATURE = b'RIFF'
            
            while current_pos < archive_size:
                riff_offset = archive_data.find(RIFF_SIGNATURE, current_pos)
                if riff_offset == -1:
                    break

                size_field_offset = riff_offset + 4
                
                if size_field_offset + 4 > archive_size:
                    self._log(f"Found a 'RIFF' at offset 0x{riff_offset:X}, but not enough data for a header. Stopping.")
                    break
                    
                data_size = struct.unpack('<H', archive_data[size_field_offset : size_field_offset + 2])[0]
                total_chunk_size = 8 + data_size

                if riff_offset + total_chunk_size > archive_size:
                    self._log(f"WARNING: Chunk at offset 0x{riff_offset:X} has a declared size ({data_size} bytes) that exceeds file boundaries. Skipping.")
                    current_pos = riff_offset + 1
                    continue

                wave_data = archive_data[riff_offset : riff_offset + total_chunk_size]
                
                extracted_count += 1
                output_filename = f"sound_{extracted_count:03d}.wav"
                output_path = os.path.join(output_dir, output_filename)

                with open(output_path, 'wb') as f_out:
                    f_out.write(wave_data)

                self._log(f" -> Extracted '{output_filename}' (Data size: {data_size} bytes, Total size: {len(wave_data)} bytes)")

                current_pos = riff_offset + total_chunk_size

            if extracted_count == 0:
                self._log("\nNo WAVE files were found or extracted.")
            else:
                self._log(f"\nDone! Extracted a total of {extracted_count} files.")
            
            messagebox.showinfo("Success", f"Extraction complete! {extracted_count} files were saved.")

        except FileNotFoundError:
            messagebox.showerror("Error", f"Could not find the input file:\n{input_file}")
        except Exception as e:
            messagebox.showerror("Critical Error", f"An unexpected error occurred during unpacking:\n{e}")

if __name__ == "__main__":
    app = SBKUnpacker()
    app.mainloop()
