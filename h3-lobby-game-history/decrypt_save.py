"""
HoTA HD Mod - Tournament Save File Decryptor
=============================================
Bypasses the password-protected save encryption used by the "Misc.TournamentSaver"
feature in HD_HOTA.dll.

The encryption is fundamentally flawed: the XOR decryption key is derivable entirely
from data stored in the same file it protects. All passwords (per-player) are stored
in the save header, obfuscated only with fixed XOR constants.

Save files on disk are gzip-compressed (Heroes III uses zlib gzopen). The tournament
encryption operates on the decompressed logical stream.

Usage:
    python decrypt_save.py <input_save> [output_save]

If output_save is not specified, writes to <input_save>.decrypted
"""

import gzip
import struct
import sys
import os


# XOR key table from sub_1099650: key[i] = (4*i) ^ ((i%2) ^ ((i+1)%3)) ^ 0xBF
PASSWORD_XOR_TABLE = [0xBE, 0xB8, 0xB7, 0xB3, 0xAD, 0xAA, 0xA6, 0xA0,
                      0x9F, 0x9B, 0x95, 0x92, 0x8E, 0x88, 0x87, 0x83]

# Magic constants from the save format
HEADER_MAGIC = 0xCCCCCCCC
OFFSET_XOR = 0x1284F
SIZE_XOR = 0x2507A
COUNT_XOR = 0xBE
PLAYER_ID_XOR = 0xDC
PASSWORD_BYTE_XOR = 0x8E


def derive_key_from_entries(entries):
    """
    Derive the 16-byte XOR decryption key from password entries.
    
    key[i] = XOR of all (obf_password[i] ^ player_index ^ 0xFE)
    for each active player entry.
    """
    key = bytearray(16)
    for player_index, obf_password in entries:
        for i in range(16):
            key[i] ^= obf_password[i] ^ player_index ^ 0xFE
    return bytes(key)


def decrypt_region(data, key):
    """
    Decrypt using the HD tournament save XOR scheme.
    
    Key indexing: for byte position j, uses key[(j & 0xF) - (j & 1)]
    Pattern: key[0], key[0], key[2], key[2], key[4], key[4], ...
    Only even-indexed key bytes are used, each for pairs of consecutive bytes.
    """
    result = bytearray(len(data))
    for j in range(len(data)):
        key_index = (j & 0xF) - (j & 1)
        result[j] = data[j] ^ key[key_index]
    return bytes(result)


def recover_plaintext_passwords(entries):
    """
    Recover plaintext passwords from obfuscated entries.
    plaintext[i] = obf_password[i] ^ PASSWORD_XOR_TABLE[i]
    """
    passwords = []
    for player_index, obf_password in entries:
        plaintext = bytearray(16)
        for i in range(16):
            plaintext[i] = obf_password[i] ^ PASSWORD_XOR_TABLE[i]
        # Trim at null terminator
        try:
            null_pos = plaintext.index(0)
            plaintext = plaintext[:null_pos]
        except ValueError:
            pass
        passwords.append((player_index, plaintext.decode('ascii', errors='replace')))
    return passwords


def decrypt_save(input_path, output_path=None):
    if output_path is None:
        output_path = input_path + '.decrypted'

    with open(input_path, 'rb') as f:
        raw = f.read()

    # Check if file is gzip-compressed (magic: 1F 8B)
    is_gzipped = raw[:2] == b'\x1f\x8b'
    if is_gzipped:
        print("Detected gzip-compressed save file, decompressing...")
        data = gzip.decompress(raw)
        print(f"  Compressed: {len(raw)} bytes → Decompressed: {len(data)} bytes")
    else:
        data = raw
        print("File is not gzip-compressed, processing raw data...")

    file_size = len(data)
    if file_size < 8:
        print("ERROR: Decompressed data too small to contain footer")
        return False

    # Step 1: Read footer (last 8 bytes)
    footer = data[-8:]
    encrypted_offset = struct.unpack_from('<I', footer, 0)[0] ^ OFFSET_XOR
    encrypted_size = struct.unpack_from('<I', footer, 4)[0] ^ SIZE_XOR

    print(f"File size: {file_size} bytes")
    print(f"Encrypted region offset (from game data start): {encrypted_offset}")
    print(f"Encrypted region size: {encrypted_size}")

    # Step 2: Parse the password block header
    pos = 0

    # Check for the magic header (0xCCCCCCCC)
    # The file starts either with:
    #   - [magic:4][version:4] for multiplayer saves
    #   - [magic:4][magic:4][version:4] for other saves
    magic1 = struct.unpack_from('<I', data, pos)[0]
    pos += 4

    if magic1 != HEADER_MAGIC:
        print(f"ERROR: Expected magic 0x{HEADER_MAGIC:08X}, got 0x{magic1:08X}")
        print("This file may not be a tournament-encrypted save.")
        return False

    # Check if next 4 bytes are also magic (8-byte header) or version (4-byte header)
    next_val = struct.unpack_from('<I', data, pos)[0]
    pos += 4

    if next_val == HEADER_MAGIC:
        # 8-byte magic header, next is version
        version = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        print(f"Header: 8-byte magic, version = {version} (0x{version:02X})")
    else:
        version = next_val
        print(f"Header: 4-byte magic, version = {version} (0x{version:02X})")

    # Version range check (must be 7 < version <= 0x90)
    if version - 7 > 0x89:
        print(f"ERROR: Version {version} out of valid range")
        return False

    # Optional 4 bytes if version > 0x55
    if version > 0x55:
        extra_val = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        print(f"Extra field (version > 0x55): 0x{extra_val:08X}")

    # Read player count (1 byte XOR'd with 0xBE)
    player_count = data[pos] ^ COUNT_XOR
    pos += 1
    print(f"Player count: {player_count}")

    if player_count < 2:
        print("ERROR: Player count < 2, not a valid encrypted save")
        return False

    # Read password entries (17 bytes each: 1 byte player_id + 16 bytes password)
    entries = []
    for entry_idx in range(player_count):
        if pos + 17 > file_size:
            print(f"ERROR: Unexpected EOF reading entry {entry_idx}")
            return False

        player_index = data[pos] ^ PLAYER_ID_XOR
        pos += 1

        obf_password = bytearray(16)
        for i in range(16):
            obf_password[i] = data[pos] ^ PASSWORD_BYTE_XOR
            pos += 1

        entries.append((player_index, obf_password))
        print(f"  Entry {entry_idx}: player_index={player_index}")

    # Optional 4 bytes if version >= 0x7D
    if version >= 0x7D:
        extra_val2 = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        print(f"Extra field (version >= 0x7D): 0x{extra_val2:08X}")

    # pos now points to the start of game data
    game_data_start = pos
    print(f"\nGame data starts at file offset: {game_data_start}")

    # Step 3: Recover and display plaintext passwords
    passwords = recover_plaintext_passwords(entries)
    print("\nRecovered passwords:")
    for player_idx, password in passwords:
        print(f"  Player {player_idx}: \"{password}\"")

    # Step 4: Derive XOR key
    key = derive_key_from_entries(entries)
    print(f"\nDerived XOR key: {key.hex()}")
    print(f"Effective key (even indices only): {bytes(key[i] for i in range(0, 16, 2)).hex()}")

    # Step 5: Locate encrypted region in file
    enc_start = game_data_start + encrypted_offset
    enc_end = enc_start + encrypted_size

    if enc_end > file_size - 8:  # -8 for footer
        print(f"ERROR: Encrypted region extends beyond file data")
        print(f"  enc_start={enc_start}, enc_end={enc_end}, file_size={file_size}")
        return False

    print(f"\nEncrypted region: file offset {enc_start} to {enc_end} ({encrypted_size} bytes)")

    # Step 6: Decrypt
    encrypted_data = data[enc_start:enc_end]
    decrypted_data = decrypt_region(encrypted_data, key)

    # Step 7: Reconstruct decrypted file
    # Output = password_block + unencrypted_prefix + decrypted_region + unencrypted_suffix
    output_data = bytearray()
    output_data += data[:enc_start]              # everything before encrypted region
    output_data += decrypted_data                # decrypted region
    output_data += data[enc_end:file_size - 8]   # everything after encrypted region (minus footer)
    output_data += data[file_size - 8:]          # keep footer as-is

    # Re-compress with gzip if the original was compressed
    if is_gzipped:
        print("Re-compressing with gzip...")
        final_data = gzip.compress(bytes(output_data), compresslevel=6)
        print(f"  Decrypted: {len(output_data)} bytes → Compressed: {len(final_data)} bytes")
    else:
        final_data = bytes(output_data)

    with open(output_path, 'wb') as f:
        f.write(final_data)

    print(f"\nDecrypted save written to: {output_path}")
    print(f"Output size: {len(final_data)} bytes")
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nOptions:")
        print("  python decrypt_save.py <save_file>              - Decrypt to <save_file>.decrypted")
        print("  python decrypt_save.py <save_file> <output>     - Decrypt to specified output")
        print("  python decrypt_save.py --info <save_file>       - Inspect only (no output)")
        sys.exit(1)

    if sys.argv[1] == '--info':
        input_path = sys.argv[2]
        if not os.path.exists(input_path):
            print(f"ERROR: File not found: {input_path}")
            sys.exit(1)
        inspect_save(input_path)
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        if not os.path.exists(input_path):
            print(f"ERROR: File not found: {input_path}")
            sys.exit(1)
        success = decrypt_save(input_path, output_path)
        sys.exit(0 if success else 1)


def inspect_save(input_path):
    """Just inspect the save without writing output."""
    with open(input_path, 'rb') as f:
        raw = f.read()

    is_gzipped = raw[:2] == b'\x1f\x8b'
    if is_gzipped:
        print(f"File: {input_path}")
        print(f"Format: gzip-compressed ({len(raw)} bytes on disk)")
        data = gzip.decompress(raw)
        print(f"Decompressed size: {len(data)} bytes")
    else:
        print(f"File: {input_path} (uncompressed, {len(raw)} bytes)")
        data = raw

    print(f"First 16 bytes (decompressed): {data[:16].hex(' ')}")

    # Check for tournament encryption magic
    if len(data) >= 4:
        magic = struct.unpack_from('<I', data, 0)[0]
        if magic == HEADER_MAGIC:
            print("\n*** TOURNAMENT ENCRYPTED SAVE DETECTED ***")
            print("This save has password-protected encryption.")
            # Parse and show info
            pos = 4
            next_val = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            if next_val == HEADER_MAGIC:
                version = struct.unpack_from('<I', data, pos)[0]
                pos += 4
            else:
                version = next_val
            print(f"Version: {version} (0x{version:02X})")

            if version > 0x55:
                pos += 4
            player_count = data[pos] ^ COUNT_XOR
            pos += 1
            print(f"Player count: {player_count}")

            if player_count >= 2:
                entries = []
                for i in range(player_count):
                    pi = data[pos] ^ PLAYER_ID_XOR
                    pos += 1
                    obf = bytearray(data[pos:pos+16])
                    for j in range(16):
                        obf[j] ^= PASSWORD_BYTE_XOR
                    pos += 16
                    entries.append((pi, obf))

                passwords = recover_plaintext_passwords(entries)
                print("\nRecovered passwords:")
                for pi, pw in passwords:
                    print(f"  Player {pi}: \"{pw}\"")

                key = derive_key_from_entries(entries)
                print(f"\nXOR key: {key.hex()}")

                # Footer
                footer = data[-8:]
                enc_off = struct.unpack_from('<I', footer, 0)[0] ^ OFFSET_XOR
                enc_sz = struct.unpack_from('<I', footer, 4)[0] ^ SIZE_XOR
                print(f"\nEncrypted offset: {enc_off}, size: {enc_sz}")
        else:
            print(f"\nFirst DWORD: 0x{magic:08X} — not tournament-encrypted")
            print("This appears to be a regular (unencrypted) save file.")


if __name__ == '__main__':
    main()
