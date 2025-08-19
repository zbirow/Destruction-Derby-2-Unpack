# Destruction Derby 2 Unpack / Pack | Dirinfo / Bank1

* Dirinfo [Documentation](https://github.com/zbirow/Destruction-Derby-2-Unpack/blob/main/Dirinfo.md)
* Bank1 [Documentation](https://github.com/zbirow/Destruction-Derby-2-Unpack/blob/main/Bank1.md)




The tools support two distinct formats:
1.  **SBK Sound Banks** (`.sbk` files with an internal header and index).
2.  **Destruction Derby 2 DIRINFO Archives** (sector-based archives with a detailed header).

## Requirements

*   **Python 3.x**
*   **Tkinter library** (this is usually included with standard Python installations on Windows and macOS).

---

## 1. SBK Sound Bank Unpacker (`Bank1_Unpacker.py`)

This tool extracts individual `sound_xxx.wav` files from a `.sbk` sound bank archive. It reads the custom RIFF-based header for each sound to determine its size.

### How to Use
1.  Run the script: `python Bank1_Unpacker.py`
2.  Click **"Browse..."** next to "Select SBK file" and choose your `.sbk` file (e.g., `BANK1.SBK`).
3.  Click **"Browse..."** next to "Select destination folder" to choose where the extracted sounds will be saved.
4.  Click the **"Unpack Files"** button.
5.  Progress will be shown in the log window, and a success message will appear upon completion.

---

## 2. SBK Sound Bank Packer (`Bank1_Packer.py`)

This tool packs multiple `.wav` files from a folder into a single `.sbk` sound bank archive, correctly building the header and index table based on the provided files.

**Important:** Your input files must be named sequentially using leading zeros, for example: `sound_001.wav`, `sound_002.wav`, `sound_003.wav`, etc. The tool sorts them numerically.

### How to Use
1.  Run the script: `python Bank1_packer.py`
2.  Select the input folder containing your `.wav` files.
3.  Select the output file path and name (e.g., `BANK1.SBK`).
4.  Click the **"Build SBK File"** button.
5.  The tool will process each file, calculate metadata (like the duration flag), and build the final archive.

---

## 3. Destruction Derby 2 DIRINFO Unpacker (`Dirinfo_Unpacker.py`)

This tool unpacks all files from a Destruction Derby 2 `DIRINFO` archive, reading the header to determine file names, offsets, and sizes, and recreating the original directory structure.

### How to Use
1.  Run the script: `python Dirinfo_Unpacker.py`
2.  Select the input `DIRINFO` file.
3.  Select an empty folder where the files and subfolders will be extracted.
4.  Click the **"Unpack Files"** button.
5.  The log window will show each file as it is extracted.

---

## 4. Destruction Derby 2 DIRINFO Packer (`Dirinfo_Packer.py`)

This tool packs a folder structure (containing subfolders and files) into a single `DIRINFO` archive compatible with Destruction Derby 2. It automatically calculates sector offsets and builds the complex header.

**Input Structure:** The tool recursively scans the input folder. The subfolder structure inside your selected input folder will be preserved in the final archive (e.g., a file at `input_folder\LEV0\TRACK.DAT` will be packed with the path `LEV0\TRACK.DAT`).

### How to Use
1.  Run the script: `python Dirinfo_Packer.py`
2.  Select the **root input folder** that contains your game data (e.g., a folder containing the `LEV0`, `LEV1`, etc. subdirectories).
3.  Select the output file path and name (e.g., `DIRINFO`).
4.  Click the **"Build File"** button.
