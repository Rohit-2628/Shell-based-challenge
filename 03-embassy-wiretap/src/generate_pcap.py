#!/usr/bin/env python3
"""
Generates the latverian_embassy.pcap capture file with pure Python.
Simulates:
1. Syslog notification leaking the pre-shared key (PSK).
2. TCP handshake and DOOM-NET exchange between client (10.0.4.15) and embassy server (10.0.4.1:8042).
"""
import struct
import time
import hmac
import hashlib
from embassy_relay import (
    build_packet, MSG_HELLO_REQ, MSG_HELLO_RESP,
    MSG_AUTH_REQ, MSG_AUTH_RESP, MSG_QUERY_REQ, MSG_QUERY_RESP,
    SHARED_PSK, CMD_ORBITAL_TELEMETRY
)

PCAP_GLOBAL_HEADER = struct.pack(
    "<IHHiIII",
    0xa1b2c3d4, # magic number
    2, 4,       # version 2.4
    0, 0,       # thiszone, sigfigs
    65535,      # snaplen
    1           # LINKTYPE_ETHERNET
)

def ip_checksum(header: bytes) -> int:
    if len(header) % 2 == 1:
        header += b"\x00"
    words = struct.unpack(f"!{len(header)//2}H", header)
    s = sum(words)
    while (s >> 16) > 0:
        s = (s & 0xFFFF) + (s >> 16)
    return (~s) & 0xFFFF

def make_ipv4(src_ip: str, dst_ip: str, proto: int, payload: bytes, ip_id=1) -> bytes:
    src_bytes = bytes(map(int, src_ip.split('.')))
    dst_bytes = bytes(map(int, dst_ip.split('.')))
    total_len = 20 + len(payload)
    hdr = struct.pack("!BBHHHBBH4s4s", 0x45, 0, total_len, ip_id, 0x4000, 64, proto, 0, src_bytes, dst_bytes)
    csum = ip_checksum(hdr)
    return struct.pack("!BBHHHBBH4s4s", 0x45, 0, total_len, ip_id, 0x4000, 64, proto, csum, src_bytes, dst_bytes) + payload

def make_udp(src_port: int, dst_port: int, payload: bytes) -> bytes:
    length = 8 + len(payload)
    # Checksum 0 is allowed in IPv4 UDP
    return struct.pack("!HHHH", src_port, dst_port, length, 0) + payload

def make_tcp(src_port: int, dst_port: int, seq: int, ack_seq: int, flags: int, payload: bytes = b"", src_ip="10.0.4.15", dst_ip="10.0.4.1") -> bytes:
    offset_res = (5 << 4)
    window = 64240
    tcp_hdr_partial = struct.pack("!HHIIBBHHH", src_port, dst_port, seq, ack_seq, offset_res, flags, window, 0, 0)

    # TCP pseudo-header for checksum
    src_bytes = bytes(map(int, src_ip.split('.')))
    dst_bytes = bytes(map(int, dst_ip.split('.')))
    pseudo = struct.pack("!4s4sBBH", src_bytes, dst_bytes, 0, 6, len(tcp_hdr_partial) + len(payload))
    csum = ip_checksum(pseudo + tcp_hdr_partial + payload)

    return struct.pack("!HHIIBBHHH", src_port, dst_port, seq, ack_seq, offset_res, flags, window, csum, 0) + payload

def make_eth(src_mac: bytes, dst_mac: bytes, eth_type: int, payload: bytes) -> bytes:
    return dst_mac + src_mac + struct.pack("!H", eth_type) + payload

def write_pcap_packet(f, frame: bytes, ts: float):
    sec = int(ts)
    usec = int((ts - sec) * 1000000)
    hdr = struct.pack("<IIII", sec, usec, len(frame), len(frame))
    f.write(hdr + frame)

def generate_pcap(output_path: str):
    client_mac = b"\x00\x50\x56\xc0\x00\x08"
    server_mac = b"\x00\x0c\x29\x3e\x5a\x11"
    client_ip = "10.0.4.15"
    server_ip = "10.0.4.1"
    client_port = 49152
    server_port = 8042

    cur_time = 1758156800.0 # Historical capture timestamp

    with open(output_path, "wb") as f:
        f.write(PCAP_GLOBAL_HEADER)

        # Packet 1: Syslog from Gateway leaking the PSK
        syslog_msg = b"<14>Sep 18 05:12:00 LATVERIA-EMBASSY-GW[1042]: [AUTH] DOOM-NET v2 service starting on :8042 (PSK: LATVERIA_DIPLOMATIC_CIPHER_1962)"
        udp_pkt = make_udp(514, 514, syslog_msg)
        ip_pkt = make_ipv4(server_ip, "10.0.4.255", 17, udp_pkt, ip_id=101)
        eth_frame = make_eth(server_mac, b"\xff\xff\xff\xff\xff\xff", 0x0800, ip_pkt)
        write_pcap_packet(f, eth_frame, cur_time)
        cur_time += 0.05

        # Packet 2: TCP SYN
        c_seq = 1000
        s_seq = 5000
        tcp = make_tcp(client_port, server_port, c_seq, 0, 0x02, b"", client_ip, server_ip) # SYN
        ip = make_ipv4(client_ip, server_ip, 6, tcp, ip_id=201)
        write_pcap_packet(f, make_eth(client_mac, server_mac, 0x0800, ip), cur_time)
        cur_time += 0.002

        # Packet 3: TCP SYN-ACK
        tcp = make_tcp(server_port, client_port, s_seq, c_seq + 1, 0x12, b"", server_ip, client_ip) # SYN-ACK
        ip = make_ipv4(server_ip, client_ip, 6, tcp, ip_id=301)
        write_pcap_packet(f, make_eth(server_mac, client_mac, 0x0800, ip), cur_time)
        cur_time += 0.001
        c_seq += 1
        s_seq += 1

        # Packet 4: TCP ACK
        tcp = make_tcp(client_port, server_port, c_seq, s_seq, 0x10, b"", client_ip, server_ip) # ACK
        ip = make_ipv4(client_ip, server_ip, 6, tcp, ip_id=202)
        write_pcap_packet(f, make_eth(client_mac, server_mac, 0x0800, ip), cur_time)
        cur_time += 0.010

        # Packet 5: DOOM-NET MSG_HELLO_REQ
        hello_payload = b"AGENT_DOOM_GENEVA"
        doom_pkt = build_packet(MSG_HELLO_REQ, 1, hello_payload)
        tcp = make_tcp(client_port, server_port, c_seq, s_seq, 0x18, doom_pkt, client_ip, server_ip) # PSH-ACK
        ip = make_ipv4(client_ip, server_ip, 6, tcp, ip_id=203)
        write_pcap_packet(f, make_eth(client_mac, server_mac, 0x0800, ip), cur_time)
        c_seq += len(doom_pkt)
        cur_time += 0.003

        # Packet 6: DOOM-NET MSG_HELLO_RESP (with salt)
        sample_salt = b"\xca\xfe\xba\xbe\xde\xad\xbe\xef"
        doom_resp = build_packet(MSG_HELLO_RESP, 1, sample_salt)
        tcp = make_tcp(server_port, client_port, s_seq, c_seq, 0x18, doom_resp, server_ip, client_ip)
        ip = make_ipv4(server_ip, client_ip, 6, tcp, ip_id=302)
        write_pcap_packet(f, make_eth(server_mac, client_mac, 0x0800, ip), cur_time)
        s_seq += len(doom_resp)
        cur_time += 0.012

        # Packet 7: DOOM-NET MSG_AUTH_REQ
        auth_mac = hmac.new(SHARED_PSK, sample_salt, hashlib.sha256).digest()
        doom_auth = build_packet(MSG_AUTH_REQ, 2, auth_mac)
        tcp = make_tcp(client_port, server_port, c_seq, s_seq, 0x18, doom_auth, client_ip, server_ip)
        ip = make_ipv4(client_ip, server_ip, 6, tcp, ip_id=204)
        write_pcap_packet(f, make_eth(client_mac, server_mac, 0x0800, ip), cur_time)
        c_seq += len(doom_auth)
        cur_time += 0.004

        # Packet 8: DOOM-NET MSG_AUTH_RESP
        doom_auth_resp = build_packet(MSG_AUTH_RESP, 2, b"\x00")
        tcp = make_tcp(server_port, client_port, s_seq, c_seq, 0x18, doom_auth_resp, server_ip, client_ip)
        ip = make_ipv4(server_ip, client_ip, 6, tcp, ip_id=303)
        write_pcap_packet(f, make_eth(server_mac, client_mac, 0x0800, ip), cur_time)
        s_seq += len(doom_auth_resp)
        cur_time += 0.008

        # Packet 9: DOOM-NET MSG_QUERY_REQ (CMD_ORBITAL_TELEMETRY = 0x1337)
        cmd_payload = struct.pack("!H", CMD_ORBITAL_TELEMETRY)
        doom_query = build_packet(MSG_QUERY_REQ, 3, cmd_payload)
        tcp = make_tcp(client_port, server_port, c_seq, s_seq, 0x18, doom_query, client_ip, server_ip)
        ip = make_ipv4(client_ip, server_ip, 6, tcp, ip_id=205)
        write_pcap_packet(f, make_eth(client_mac, server_mac, 0x0800, ip), cur_time)
        c_seq += len(doom_query)
        cur_time += 0.005

        # Packet 10: DOOM-NET MSG_QUERY_RESP (Sample response in pcap)
        sample_secret = b"[DIPLOMATIC DISPATCH: TOP SECRET]\nORBITAL SATELLITE KEYS LOADED.\nPERIMETER ACCESS CODE: FLAG{dummy_pcap_traffic_capture_sample}\n"
        doom_qresp = build_packet(MSG_QUERY_RESP, 3, sample_secret)
        tcp = make_tcp(server_port, client_port, s_seq, c_seq, 0x18, doom_qresp, server_ip, client_ip)
        ip = make_ipv4(server_ip, client_ip, 6, tcp, ip_id=304)
        write_pcap_packet(f, make_eth(server_mac, client_mac, 0x0800, ip), cur_time)
        s_seq += len(doom_qresp)
        cur_time += 0.010

        # Packet 11 & 12: FIN / ACK teardown
        tcp = make_tcp(client_port, server_port, c_seq, s_seq, 0x11, b"", client_ip, server_ip) # FIN-ACK
        ip = make_ipv4(client_ip, server_ip, 6, tcp, ip_id=206)
        write_pcap_packet(f, make_eth(client_mac, server_mac, 0x0800, ip), cur_time)
        cur_time += 0.002

        tcp = make_tcp(server_port, client_port, s_seq, c_seq + 1, 0x11, b"", server_ip, client_ip)
        ip = make_ipv4(server_ip, client_ip, 6, tcp, ip_id=305)
        write_pcap_packet(f, make_eth(server_mac, client_mac, 0x0800, ip), cur_time)

    print(f"[+] PCAP successfully generated at {output_path}")

if __name__ == "__main__":
    import pathlib
    base_dir = pathlib.Path(__file__).resolve().parent.parent
    handouts_dir = base_dir / "handouts"
    handouts_dir.mkdir(parents=True, exist_ok=True)
    out_file = str(handouts_dir / "latverian_embassy.pcap")
    generate_pcap(out_file)
