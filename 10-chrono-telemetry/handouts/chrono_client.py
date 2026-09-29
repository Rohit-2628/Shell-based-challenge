#!/usr/bin/env python3
"""
Chrono-Stream Client SDK Handout
Protocol interface for CHRONO-STREAM/3.1.
"""
import socket
import struct
import zlib

MAGIC = b"CHRN"
VERSION = 0x0301

TYPE_TELEMETRY   = 0x0001
TYPE_DIAGNOSTICS = 0x0002
TYPE_HEARTBEAT   = 0x0003
TYPE_ADMIN_CMD   = 0x00A0
TYPE_RESPONSE    = 0x00FF

CMD_DRAIN_CORE   = 0x1337

class ChronoClient:
    def __init__(self, host="127.0.0.1", port=8043):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, int(port)))

    def send_packet(self, type_id, payload):
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        header = struct.pack(">4sHHII", MAGIC, VERSION, type_id, len(payload), crc)
        self.sock.sendall(header + payload)

    def recv_packet(self):
        header_bytes = self.sock.recv(16)
        if len(header_bytes) < 16:
            return None, None
        magic, ver, type_id, plen, crc = struct.unpack(">4sHHII", header_bytes)
        payload = b""
        while len(payload) < plen:
            chunk = self.sock.recv(plen - len(payload))
            if not chunk:
                break
            payload += chunk
        return type_id, payload

    def ping(self):
        self.send_packet(TYPE_HEARTBEAT, b"PING")
        return self.recv_packet()

    def query_diagnostics(self, query_id=1, reflection_flag=0):
        payload = struct.pack(">II", query_id, reflection_flag)
        self.send_packet(TYPE_DIAGNOSTICS, payload)
        return self.recv_packet()

    def send_admin_cmd(self, auth_token, cmd_id, params=b""):
        token_bytes = auth_token if isinstance(auth_token, bytes) else auth_token.encode("utf-8")
        token_padded = token_bytes.ljust(16, b"_")[:16]
        payload = token_padded + struct.pack(">II", cmd_id, len(params)) + params
        self.send_packet(TYPE_ADMIN_CMD, payload)
        return self.recv_packet()

    def close(self):
        self.sock.close()

if __name__ == "__main__":
    c = ChronoClient()
    print("[*] Sending Heartbeat...")
    t, p = c.ping()
    print("Response:", p.decode("utf-8", errors="ignore"))
    c.close()
