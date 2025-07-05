import os
import struct

# ==========================================================
# SET YOUR CONFIGURATION HERE
# ==========================================================

# 1. Path to the archive file you want to unpack.
#    Examples:
#    - Windows: "C:\\Games\\MyGame\\LEVEL1.DAT"
#    - Linux/macOS: "/home/user/games/LEVEL1.DAT"
#    - If the file is in the same folder as the script: "LEVEL1.DAT"
ARCHIVE_FILE_PATH = "YOUR_FILE.DAT"  # <--- CHANGE THIS!

# 2. Name of the folder where the files will be extracted.
#    The folder will be created in the same location where you run the script.
OUTPUT_DIRECTORY = "unpacked_files"  # <--- CHANGE THIS!

# ==========================================================
# FILE FORMAT CONFIGURATION (do not change unless you know what you're doing)
# ==========================================================
SECTOR_SIZE = 2048
TOC_END_OFFSET = 0xAA0
# ==========================================================

def parse_toc(toc_data):
    """Parses the Table of Contents data block and returns a list of files to extract."""
    files_to_extract = []
    cursor = 0
    
    print(f"[*] Parsing Table of Contents (up to offset 0x{TOC_END_OFFSET:X})...")

    while cursor < len(toc_data):
        try:
            null_pos = toc_data.index(b'\x00', cursor)
        except ValueError:
            # No more null terminators found, end of ToC
            break

        filename_bytes = toc_data[cursor:null_pos]
        
        if not filename_bytes:
            # This is likely padding, skip it
            cursor += 1
            continue

        # Decode filename and handle path separators for the current OS
        filename = filename_bytes.decode('ascii', errors='ignore').replace('\\', os.path.sep)
        
        # Move cursor past the filename and its null terminator
        cursor = null_pos + 1

        # Skip any subsequent padding bytes (0x00)
        while cursor < len(toc_data) and toc_data[cursor] == 0:
            cursor += 1

        # Check if there's enough room left for metadata
        if cursor + 6 > len(toc_data):
            break
            
        # The next 6 bytes are the metadata: 2 bytes for index, 4 for size
        meta_bytes = toc_data[cursor:cursor+6]
        
        # Unpack metadata (Little-Endian format)
        # '<' = Little-Endian
        # 'H' = Unsigned Short (2 bytes) - for the index
        # 'I' = Unsigned Int (4 bytes) - for the size
        sector_index, file_size = struct.unpack('<HI', meta_bytes)
        
        if file_size > 0:
            files_to_extract.append({
                "name": filename,
                "index": sector_index,
                "size": file_size
            })
        
        # Move cursor past the metadata
        cursor += 6

    print(f"[+] Found {len(files_to_extract)} files to unpack.")
    return files_to_extract

def find_data_start(archive_data, search_start_offset):
    """Finds the start of the data section by looking for the first non-zero byte."""
    cursor = search_start_offset
    while cursor < len(archive_data):
        if archive_data[cursor] != 0:
            print(f"[*] Data section start found at offset: 0x{cursor:X}")
            return cursor
        cursor += 1
    return -1

def main():
    """Main function to perform the unpacking."""
    
    if not os.path.exists(ARCHIVE_FILE_PATH):
        print(f"[!] Error: Archive file '{ARCHIVE_FILE_PATH}' does not exist.")
        print("[!] Please make sure you have entered the correct path in the 'ARCHIVE_FILE_PATH' variable.")
        return

    print(f"[*] Archive file: {ARCHIVE_FILE_PATH}")
    print(f"[*] Output directory: {OUTPUT_DIRECTORY}")

    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    try:
        with open(ARCHIVE_FILE_PATH, 'rb') as f:
            archive_data = f.read()

            toc_data = archive_data[:TOC_END_OFFSET]
            files_info = parse_toc(toc_data)

            if not files_info:
                print("[!] No files found in the Table of Contents. Aborting.")
                return
            
            data_start_offset = find_data_start(archive_data, TOC_END_OFFSET)
            if data_start_offset == -1:
                print("[!] Could not find the start of the data section. The format might be incorrect.")
                return

            print("\n[*] Starting file extraction...")
            for file_info in files_info:
                name = file_info["name"]
                index = file_info["index"]
                size = file_info["size"]
                
                data_offset = data_start_offset + (index * SECTOR_SIZE)
                
                if data_offset + size > len(archive_data):
                    print(f"[!] Error for file '{name}': Calculated offset ({data_offset}) and size ({size}) are out of bounds of the archive file!")
                    continue
                
                file_data = archive_data[data_offset : data_offset + size]
                
                output_path = os.path.join(OUTPUT_DIRECTORY, name)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                try:
                    with open(output_path, 'wb') as out_f:
                        out_f.write(file_data)
                    print(f"  -> Saved: {name} ({size} bytes)")
                except IOError as e:
                    print(f"[!] Error writing file '{name}': {e}")

            print("\n[+] Done! All files have been extracted to the '{}' folder.".format(OUTPUT_DIRECTORY))

    except IOError as e:
        print(f"[!] Error reading archive file: {e}")
    except Exception as e:
        print(f"[!] An unexpected error occurred: {e}")

# This line starts the script
if __name__ == "__main__":
    main()
