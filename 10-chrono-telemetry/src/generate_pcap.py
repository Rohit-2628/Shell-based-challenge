#!/usr/bin/env python3
"""
Generates synthetic Wireshark-compatible chrono_capture.pcap.
Contains Ethernet/IP/TCP packets modeling legitimate CHRONO-STREAM telemetry sessions.
"""
import os
import struct
import time
import zlib

def make_pcap():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    pcap_path = os.path.join(out_dir, "..", "handouts", "chrono_capture.pcap")
    
    # 24-byte PCAP Global Header
    global_hdr = struct.pack(
        "<IHHiIII",
        0xa1b2c3d4, # Magic
        2, 4,       # Version 2.4
        0, 0,       # GMT to local correction, accuracy
        65535,      # Snapshot length
        1           # Link-Layer: Ethernet
    )

    # Construct sample TCP packets
    # Client: 10.13.37.100:45892 -> Server: 10.13.37.1:8043
    packets = []
    
    def pack_tcp_packet(payload, sport=45892, dport=8043, seq=1000, ack=1, flags=0x18):
        # Ethernet header (14 bytes)
        eth = struct.pack("!6s6sH", b"\x02\x42\x0a\x0d\x25\x64", b"\x02\x42\x0a\x0d\x25\x01", 0x0800)
        # IP header (20 bytes)
        total_len = 20 + 20 + len(payload)
        ip = struct.pack(
            "!BBHHHBBH4s4s",
            0x45, 0, total_len, 0x1234, 0x4000, 64, 6, 0,
            b"\x0a\x0d\x25\x64", b"\x0a\x0d\x25\x01"
        )
        # TCP header (20 bytes)
        tcp = struct.pack("!HHIIBBHHH", sport, dport, seq, ack, 0x50, flags, 8192, 0, 0)
        return eth + ip + tcp + payload

    # 1. Heartbeat Query
    crc1 = zlib.crc32(b"PING") & 0xFFFFFFFF
    p1 = struct.pack(">4sHHII", b"CHRN", 0x0301, 0x0003, 4, crc1) + b"PING"
    packets.append(pack_tcp_packet(p1, seq=1001, ack=1))

    # 2. Normal Diagnostics Query
    diag_req = struct.pack(">II", 0x101, 0x00000000)
    crc2 = zlib.crc32(diag_req) & 0xFFFFFFFF
    p2 = struct.pack(">4sHHII", b"CHRN", 0x0301, 0x0002, len(diag_req), crc2) + diag_req
    packets.append(pack_tcp_packet(p2, seq=1050, ack=50))

    # Write PCAP
    now = int(time.time())
    with open(pcap_path, "wb") as f:
        f.write(global_hdr)
        for i, pkt in enumerate(packets):
            pkt_hdr = struct.pack("<IIII", now + i, i * 1000, len(pkt), len(pkt))
            f.write(pkt_hdr)
            f.write(pkt)

    print(f"[+] Generated pcap with {len(packets)} packets at {pcap_path}")

if __name__ == "__main__":
    make_pcap()
