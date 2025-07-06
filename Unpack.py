import os
import struct
from pathlib import Path

def extract_blocks(input_file):
    script_dir = Path(__file__).parent.absolute()
    output_dir = script_dir / 'extracted'
    output_dir.mkdir(exist_ok=True)
    
    with open(input_file, 'rb') as f:
        block_count = 0
        while f.tell() < 0xAA0:
            block = f.read(24)
            if len(block) < 24:
                break

            if block_count < 2:
                name_length = 17
                padding_size = 1
            elif block_count == 11:
                name_length = 16
                padding_size = 2
            else:
                name_length = 14
                padding_size = 4

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

                print(f"Extracted: {name.ljust(30)} (block: {block_count:2d}, index: {index:5d}, size: {size:8d} bytes, offset: 0x{data_offset:06X})")
            else:
                print(f"Skipped:  {name.ljust(30)} (block: {block_count:2d}, invalid index or size)")

            block_count += 1

if __name__ == "__main__":
    input_file = 'C:/Users/zbirow/Downloads/destructionderby2_dirinfo/dirinfo.bin' # Replace with your input file path
    extract_blocks(input_file)
    print(f"Extraction complete! Files saved to: {Path(__file__).parent.absolute() / 'extracted'}")
