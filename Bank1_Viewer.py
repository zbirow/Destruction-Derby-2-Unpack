import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
import os

class EditWindow(tk.Toplevel):
    def __init__(self, parent, entry_obj):
        super().__init__(parent)
        self.title("Edit Sound Entry")
        self.geometry("300x150")
        self.resizable(False, False)

        self.entry = entry_obj
        self.result = None

        self.sample_rate_var = tk.StringVar(value=str(self.entry.sample_rate))
        self.duration_flag_var = tk.StringVar(value=str(self.entry.duration_flag))
        self.unknown_flag_var = tk.StringVar(value=str(self.entry.unknown_flag))

        self._create_widgets()

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Sample Rate:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=self.sample_rate_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(frame, text="Duration Flag:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=self.duration_flag_var).grid(row=1, column=1, sticky="ew")

        ttk.Label(frame, text="Unknown Flag:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=self.unknown_flag_var).grid(row=2, column=1, sticky="ew")
        
        frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="OK", command=self.apply_changes).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def apply_changes(self):
        try:
            new_rate = int(self.sample_rate_var.get())
            new_duration = int(self.duration_flag_var.get())
            new_unknown = int(self.unknown_flag_var.get())
            
            self.result = (new_rate, new_duration, new_unknown)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "All values must be integers.", parent=self)

class SoundEntry:
    def __init__(self, index, address_prefix, address_low, block_size, duration_flag, sample_rate, flag2):
        self.index = index
        self.absolute_offset = (address_prefix << 16) | address_low
        self.block_size = block_size
        self.duration_flag = duration_flag
        self.sample_rate = sample_rate
        self.unknown_flag = flag2
        
    def to_tuple(self):
        return (
            self.index + 1, f"0x{self.absolute_offset:08X}", f"{self.block_size} B",
            f"{self.block_size / 1024:.2f} KB", f"{self.sample_rate} Hz",
            self.duration_flag, self.unknown_flag
        )

class SBKArchiveEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SBK Archive Editor")
        self.geometry("850x600")

        self.archive_path = None
        self.archive_data = None
        self.sound_entries = []
        self.is_modified = False

        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing) 

    def _create_widgets(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        self.file_menu.add_command(label="Open Archive...", command=self.open_file)
        self.file_menu.add_command(label="Save As...", command=self.save_archive_as, state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Extract Selected Sound...", command=self.extract_selected_sound, state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_closing)

        frame = ttk.Frame(self, padding="10")
        frame.pack(fill="both", expand=True)
        columns = ("#", "Absolute Offset", "Size (Bytes)", "Size (KB)", "Sample Rate", "Duration Flag", "Unknown Flag")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns: self.tree.heading(col, text=col)
        self.tree.column("#", width=50, anchor="center")
        self.tree.column("Absolute Offset", width=110, anchor="center")
        for col in columns[2:]: self.tree.column(col, width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.tree.bind("<Double-1>", self.edit_selected_item)

        self.status_var = tk.StringVar(value="Ready. Please open an archive file.")
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken")
        status_bar.pack(side="bottom", fill="x")

    def update_title(self):
        title = "SBK Archive Editor"
        if self.archive_path:
            title += f" - {os.path.basename(self.archive_path)}"
        if self.is_modified:
            title += " *" 
        self.title(title)

    def open_file(self):
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to discard them and open a new file?"):
                return
        
        path = filedialog.askopenfilename(title="Select SBK Archive File", filetypes=[("SBK Sound Bank", "*.sbk"), ("All Files", "*.*")])
        if not path: return
        self.archive_path = path
        self.update_status(f"Opening and parsing {os.path.basename(path)}...")
        self.load_and_parse_archive()

    def load_and_parse_archive(self):
        try:
            with open(self.archive_path, "rb") as f: self.archive_data = f.read()
            header_data = self.archive_data[0:16]
            if len(header_data) < 16: raise ValueError("File is too small to contain a 16-byte header.")
            file_count = struct.unpack('<H', header_data[12:14])[0]

            self.update_status(f"Header parsed. Expecting {file_count} file entries.")
            self.sound_entries.clear()
            self.tree.delete(*self.tree.get_children())

            index_start = 16
            stride = 28
            data_size = 20

            for i in range(file_count):
                offset = index_start + (i * stride)
                entry_data = self.archive_data[offset : offset + data_size]
                parts = struct.unpack('<10H', entry_data)
                entry = SoundEntry(i, parts[1], parts[0], parts[2], parts[4], parts[6], parts[8])
                self.sound_entries.append(entry)
                self.tree.insert("", "end", values=entry.to_tuple())
            
            self.update_status(f"Successfully loaded {len(self.sound_entries)} entries.")
            self.is_modified = False
            self.file_menu.entryconfig("Save As...", state="normal")
            self.update_title()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse the archive file:\n{e}")
            self.update_status("Error loading file.")

    def on_item_select(self, event):
        state = "normal" if self.tree.selection() else "disabled"
        self.file_menu.entryconfig("Extract Selected Sound...", state=state)

    def edit_selected_item(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        item_id = selected_items[0]
        item_index = self.tree.item(item_id)['values'][0] - 1
        entry_to_edit = self.sound_entries[item_index]

        editor = EditWindow(self, entry_to_edit)
        if editor.result:
            new_rate, new_duration, new_unknown = editor.result
            
            entry_to_edit.sample_rate = new_rate
            entry_to_edit.duration_flag = new_duration
            entry_to_edit.unknown_flag = new_unknown
            
            self.tree.item(item_id, values=entry_to_edit.to_tuple())
            
            self.is_modified = True
            self.update_title()
            self.update_status(f"Entry #{entry_to_edit.index + 1} updated.")

    def save_archive_as(self):
        if not self.archive_data: return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".sbk",
            initialfile=os.path.basename(self.archive_path),
            filetypes=[("SBK Sound Bank", "*.sbk"), ("All Files", "*.*")]
        )
        if not save_path: return

        self.update_status(f"Saving archive to {os.path.basename(save_path)}...")
        try:
            with open(save_path, "wb") as f_out:
                f_out.write(self.archive_data[0:16])
                for entry in self.sound_entries:
                    addr_low = entry.absolute_offset & 0xFFFF
                    addr_high = (entry.absolute_offset >> 16) & 0xFFFF
                    
                    entry_bytes = struct.pack('<HHHHHHHHHH',
                        addr_low, addr_high, entry.block_size, 0,
                        entry.duration_flag, 0, entry.sample_rate, 0,
                        entry.unknown_flag, 0
                    )
                    f_out.write(entry_bytes)
                    f_out.write(b'\x00' * 8)

                data_start = 16 + (len(self.sound_entries) * 28)
                f_out.write(self.archive_data[data_start:])

            self.is_modified = False
            self.update_title()
            self.update_status(f"Archive saved successfully.")
            messagebox.showinfo("Success", "Archive saved successfully!")

        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred while saving the file:\n{e}")

    def on_closing(self):
        if self.is_modified:
            response = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Do you want to save them before quitting?")
            if response is True:
                self.save_archive_as()
                if not self.is_modified:
                    self.destroy()
            elif response is False:
                self.destroy()
        else:
            self.destroy()

    def extract_selected_sound(self):
        selected_items = self.tree.selection()
        if not selected_items: return
        item_index = self.tree.item(selected_items[0])['values'][0] - 1
        entry_to_extract = self.sound_entries[item_index]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            initialfile=f"sound_{entry_to_extract.index + 1:03d}.wav",
            filetypes=[("WAVE files", "*.wav")]
        )
        if not save_path: return
        try:
            sound_data = self.archive_data[entry_to_extract.absolute_offset : entry_to_extract.absolute_offset + entry_to_extract.block_size]
            with open(save_path, "wb") as f:
                f.write(sound_data)
            messagebox.showinfo("Success", f"File was saved successfully to:\n{save_path}")
            self.update_status(f"Successfully extracted sound to {os.path.basename(save_path)}.")
        except Exception as e:
            messagebox.showerror("Extraction Error", f"An error occurred while saving the file:\n{e}")

    def update_status(self, message):
        self.status_var.set(message)
        self.update_idletasks()

if __name__ == "__main__":
    app = SBKArchiveEditor()
    app.mainloop()
