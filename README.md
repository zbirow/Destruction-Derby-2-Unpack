# Destruction-Derby-2-Unpack


## Detailed Structure of the Table of Contents (ToC)
The Table of Contents consists of a sequence of file entries. Each entry has the following, repeatable structure:
| Field	| Length (bytes)	| Description |
| ---- | --------------- | ----------- |
| Filename	| Variable |	An ASCII string containing the path and filename (e.g., LEV0\COPYRIGHT.BMP). |
| Name Terminator	| 1+	| One or more bytes with the value 0x00, marking the end of the filename. |
| Padding / Opt. Data	| Variable	| Optional padding bytes or additional markers (e.g., RAW). Often these are 0x00 bytes. |
| File Metadata	| 6	| A fixed, 6-byte block containing key information about the data's location and size. See section 4. |

`4C 45 56 30 5C 46 4F 4E 54 2E 42 4E 4B 00 52 41 57 00 2C 00 9C 5D 00 00`

- **Name:** LEV0\FONT.BNK
- **Terminator:** 00
- **Additional Data:** RAW (52 41 57 00)
- **Metadata:** 2C 00 9C 5D 00 00
## Detailed Structure of the Metadata Block
The 6-byte metadata block is crucial for locating the file's data. All numerical values are stored in Little-Endian format (least significant byte first).

| Field	Offset |	Length (bytes) | Data Type |	Description |
| ------------ | --------------- | --------| -------------- |
| Data Sector Index |	0	| 2	| 16-bit unsigned integer	The number of the sector (block) in the Data Section where the file begins. |
| Data Size |	2	| 4	| 32-bit unsigned integer	The exact size of the file in bytes.|

- **Sector Index:** 2C 00 -> 0x002C -> 44
- **Data Size:** 9C 5D 00 00 -> 0x00005D9C -> 23,964 bytes

## Structure of the Data Section
This section begins immediately after the last entry in the Table of Contents. It is organized into sectors (blocks) of a fixed size.

- **Sector Size:** 2048 bytes (0x800)
- **Start of Data Section:** The first byte after the final 0x00 of the Table of Contents.

To locate the data for a specific file, use the following formula:

File_Offset_in_Archive = Start_of_Data_Section + (Sector_Index * 2048)

## File Extraction Walkthrough (Example: LEV0\COPYRIGHT.BMP)
Find the entry in the ToC:
`4C...50 00 05 00 36 30 01 00`

Read the metadata:
- **Sector Index:** 05 00 -> 0x0005 -> 5
- **Data Size:** 36 30 01 00 -> 0x00013036 -> 77,878 bytes
Locate the start of the Data Section in the archive. For this example, let's assume it begins at address 0x2000.

Calculate the file's relative data offset:
Relative_Offset = 5 * 2048 = 10,240 bytes (0x2800).
Calculate the absolute offset within the archive file:
Absolute_Offset = 0x2000 (data start) + 0x2800 (file offset) = 0x4800.
