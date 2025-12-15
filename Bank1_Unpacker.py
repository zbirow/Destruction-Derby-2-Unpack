import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import struct
import json
from pathlib import Path

class SBKUnpacker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SBK Sound Bank Unpacker (Index-Based)")
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
            self._log(f"Read {archive_size / 1024:.2f} KB of data. Parsing index...")

            # --- CRITICAL FIX: Read the header and index table ---
            header_data = archive_data[0:16]
            if len(header_data) < 16:
                raise ValueError("File is too small to contain a valid header.")
            
            file_count = struct.unpack('<H', header_data[12:14])[0]
            self._log(f"Found {file_count} entries in the index.")

            os.makedirs(output_dir, exist_ok=True)
            
            index_start_offset = 16
            index_entry_stride = 28 # 20 bytes data + 8 bytes padding
            index_data_size = 20
            extracted_count = 0

            # Przygotuj słownik na konfigurację
            config_data = {}

            for i in range(file_count):
                entry_offset = index_start_offset + (i * index_entry_stride)
                entry_data = archive_data[entry_offset : entry_offset + index_data_size]

                # Unpack the entry using the correct 4-byte integer format
                parts = struct.unpack('<5I', entry_data)
                absolute_offset = parts[0]
                block_size = parts[1]
                duration_flag = parts[2]   # Odczytaj flagę
                sample_rate = parts[3]     # Odczytaj częstotliwość próbkowania
                
                # Sanity checks
                if block_size == 0:
                    self._log(f" - Skipping entry #{i+1} (zero size).")
                    continue
                if absolute_offset + block_size > archive_size:
                    self._log(f" - ERROR: Entry #{i+1} points outside the file. Stopping.")
                    messagebox.showwarning("Warning", f"Entry #{i+1} has invalid data (offset or size is out of bounds). Extraction may be incomplete.")
                    break

                # Slice the exact file data using offset and size from the index
                sound_data = archive_data[absolute_offset : absolute_offset + block_size]
                
                extracted_count += 1
                output_filename = f"sound_{extracted_count:03d}.wav"
                output_path = os.path.join(output_dir, output_filename)

                with open(output_path, 'wb') as f_out:
                    f_out.write(sound_data)

                # Zapisz metadane do słownika konfiguracyjnego
                config_data[output_filename] = {
                    'duration_flag': int(duration_flag),
                    'sample_rate': int(sample_rate),
                    'unknown_flag': int(parts[4])  # Ostatnia flaga (domyślnie 1)
                }

                self._log(f" -> Extracted '{output_filename}' (Size: {block_size} B, Offset: 0x{absolute_offset:X}, Flag: {duration_flag}, Hz: {sample_rate})")

            # Zapisz konfigurację do pliku JSON
            config_path = os.path.join(output_dir, "config.json")
            try:
                with open(config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(config_data, config_file, indent=4, ensure_ascii=False)
                self._log(f"\n  Konfiguracja zapisana do: {config_path}")
            except Exception as e:
                self._log(f"\n  ! Uwaga: Nie udało się zapisać pliku konfiguracyjnego: {e}")

            self._log(f"\nDone! Extracted a total of {extracted_count} files.")
            messagebox.showinfo("Success", f"Extraction complete! {extracted_count} files were saved.")

        except FileNotFoundError:
            messagebox.showerror("Error", f"Could not find the input file:\n{input_file}")
        except Exception as e:
            messagebox.showerror("Critical Error", f"An unexpected error occurred during unpacking:\n{e}")

if __name__ == "__main__":
    app = SBKUnpacker()
    app.mainloop()
