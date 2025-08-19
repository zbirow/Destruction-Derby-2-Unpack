### BLOK1.SBK

## Structures

| Type | Size |
| ---- | ---- |
| Header | 16 bytes |
| Index Table | 28 * number of files |
| Data Blocks | 8 metadata bytes + data |


## Header

`00 00 00 00 00 00 00 00` `A0 17 09 00` `2D 00` `00 00`

| Offset (Hex) | Size | Data Type | Description | Value |
| ------------ | ---- | --------- | ----------- | ----- |
| 0x00 - 0x07 | 8 bytes | - | Unused, padded with null bytes (0x00). | 0 |
| 0x08 - 0x0B | 4 bytes | Mixed | Total size of the archive file. | 0917A0 |
| 0x0C - 0x0D | 2 bytes | ushort | The number of files contained in the archive. | 45 |
| 0x0E - 0x0F | 2 bytes | - | 	Unused, padded with null bytes (0x00). | 0 |



## Index Table

The Index Table begins immediately after the header, at offset 0x10 (16). It consists of a series of entries, where each entry describes a single sound file.

Total size of a single entry 'slot': 28 bytes.

Slot Structure:

20 bytes: Actual data describing the file.

* 8 bytes: Empty padding.
* 20-byte Entry Structure

All multi-byte values are stored in Little Endian format.


`FC 04` `00 00` `9E 6C` `00 00` `01 00` `00 00` `11 2B` `00 00` `01 00` `00 00`

| Offset (Hex) | Size | Data Type | Description | Value |
| ------------ | ---- | --------- | ----------- | ----- |
| 0x00 - 0x01 | 2 | ushort | Relative Address (The end of the address). | FC 04 |
| 0x02 - 0x03 | 2 | ushort | Relative Address (The start of the address). | e.g., 0, 1, 2 |
| 0x04 - 0x05 | 2 | ushort | Size of the data block. | 27806 bytes| 
| 0x06 - 0x07 | 2 | ushort | Padding. | 0 |
| 0x08 - 0x09	| 2 | ushort | Duration | e.g., 0, 1 |
| 0x0A - 0x0B | 2 | ushort | Padding. | 0 |
| 0x0C - 0x0D | 2 | ushort | Sample Rate in Hz. | e.g., 11025, 22050 |
| 0x0E - 0x0F | 2 | ushort | Padding. | 0 |
| 0x10 - 0x11 | 2 | ushort | unknown |  e.g., 0, 1 |
| 0x12 - 0x13 | 2 | ushort | Padding. | 0 |

### Assembling the Relative Address
The full relative address is a 4-byte number, but it has been split into two separate 2-byte pieces in the file. To get the complete address, we just need to put them back together.
Think of it like a full hexadecimal address, for example, 0x1234ABCD. In the file, it would be stored like this:

The end of the address: Stored at offset 0x00 within the entry would be the value A075.
The start of the address : Stored at offset 0x02 within the entry would be the value 1.

To reconstruct the full address, you simply take the start part and place it in front of the end part:

1 + A075 = 1A075.
That's all there is to it. The program reads these two small numbers and combines them to form the one, correct address.



## Data Block

The first 8 bytes form the main RIFF chunk header:

Offset 0x00 (4 bytes): The "RIFF" signature. This tells the system it's a RIFF container file.

Offset 0x04 (4 bytes): The size of the rest of the file. This number indicates how many bytes follow after this field.


`52 49 46 46` `96 6C 00 00` `57 41 56 45 66 6D 74 *`

| Offset | Size | Data Type | Value |
| ------ | ---- | --------- | ----- |
| 0x00 - 0x03 | 4 | ANSII | RIFF |
| 0x04 - 0x07 | 4 | ushort | 27798 bytes |
| 0x08 - * | * | Data | file data |



