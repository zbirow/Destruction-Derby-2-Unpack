import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import struct
from pathlib import Path

class DD2Unpacker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Destruction Derby 2 - DIRINFO Unpacker")
        self.geometry("700x500")
        self.resizable(False, False)

        self.input_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # --- Sekcja Wejścia ---
        input_frame = ttk.LabelFrame(main_frame, text="1. Wybierz plik DIRINFO", padding="10")
        input_frame.pack(fill="x", pady=5)
        
        input_entry = ttk.Entry(input_frame, textvariable=self.input_file_var, state="readonly", width=80)
        input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_input_btn = ttk.Button(input_frame, text="Przeglądaj...", command=self.select_input_file)
        browse_input_btn.pack(side="left")

        # --- Sekcja Wyjścia ---
        output_frame = ttk.LabelFrame(main_frame, text="2. Wybierz folder docelowy", padding="10")
        output_frame.pack(fill="x", pady=5)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, state="readonly", width=80)
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_output_btn = ttk.Button(output_frame, text="Przeglądaj...", command=self.select_output_dir)
        browse_output_btn.pack(side="left")

        # --- Przycisk Wypakowania ---
        self.unpack_button = ttk.Button(main_frame, text="Wypakuj Pliki", command=self.unpack_files, state="disabled")
        self.unpack_button.pack(pady=20, ipady=10, fill="x")
        
        # --- Logi ---
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
            title="Wybierz plik DIRINFO",
            filetypes=[("Plik DIRINFO", "DIRINFO"), ("Wszystkie pliki", "*.*")]
        )
        if filepath:
            self.input_file_var.set(filepath)
            self._log(f"Wybrano plik wejściowy: {filepath}")
            self.check_paths()

    def select_output_dir(self):
        directory = filedialog.askdirectory(title="Wybierz folder docelowy")
        if directory:
            self.output_dir_var.set(directory)
            self._log(f"Wybrano folder wyjściowy: {directory}")
            self.check_paths()

    def unpack_files(self):
        input_file = self.input_file_var.get()
        output_dir = Path(self.output_dir_var.get())

        self.log_text.config(state="normal")
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state="disabled")
        
        try:
            with open(input_file, 'rb') as f:
                block_count = 0
                while f.tell() < 0xAA0:
                    block = f.read(24)
                    if len(block) < 24:
                        break

                    # Logika z Twojego oryginalnego skryptu
                    if block_count < 2:
                        name_length, padding_size = 17, 1
                    elif block_count == 11: # 12-ty blok (indeksowany od 0)
                        name_length, padding_size = 16, 2
                    else:
                        name_length, padding_size = 14, 4

                    name_bytes = bytearray()
                    for i in range(name_length):
                        if block[i] == 0:
                            break
                        name_bytes.append(block[i])
                    name = name_bytes.decode('ascii', errors='replace')

                    index_pos = name_length + padding_size
                    size_pos = index_pos + 2

                    index = struct.unpack('<H', block[index_pos:index_pos+2])[0]
                    size = struct.unpack('<I', block[size_pos:size_pos+4])[0]
                    data_offset = index * 2048

                    if index > 0 and size > 0:
                        current_pos = f.tell()
                        f.seek(data_offset)
                        data = f.read(size)
                        f.seek(current_pos)

                        # Utwórz pełną ścieżkę docelową
                        output_path = output_dir / name
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        with open(output_path, 'wb') as out:
                            out.write(data)

                        log_msg = f"Wypakowano: {name.ljust(30)} (blok: {block_count:2d}, sektor: {index:5d}, rozmiar: {size:8d} B, offset: 0x{data_offset:06X})"
                        self._log(log_msg)
                    else:
                        log_msg = f"Pominięto:  {name.ljust(30)} (blok: {block_count:2d}, błędny sektor lub rozmiar)"
                        self._log(log_msg)

                    block_count += 1
            
            self._log(f"\nZakończono! Pliki zapisano w: {output_dir}")
            messagebox.showinfo("Sukces", "Wszystkie pliki zostały pomyślnie wypakowane!")

        except FileNotFoundError:
            messagebox.showerror("Błąd", f"Nie można znaleźć pliku wejściowego:\n{input_file}")
        except Exception as e:
            messagebox.showerror("Błąd krytyczny", f"Wystąpił nieoczekiwany błąd podczas wypakowywania:\n{e}")

if __name__ == "__main__":
    app = DD2Unpacker()
    app.mainloop()
