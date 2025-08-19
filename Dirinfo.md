## The Heather section consists of blocks of 24 bytes, where there are names and meta. They end in address AA0

- First 2 blocks: 17-byte filename + 1-byte padding + 6-byte meta
- 12th block : 16-byte filename + 2-byte padding + 6-byte meta
- All other blocks: 14-byte filename + 4-byte padding + 6-byte meta

## Read the metadata:
- **Sector Index:** 05 00 -> 0x0005 -> 5
- **Data Size:** 36 30 01 00 -> 0x00013036 -> 77,878 bytes


## Calculate the file's data offset:
Offset = 5 * 2048 = 10,240 bytes (0x2800).
