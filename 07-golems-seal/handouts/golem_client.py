#!/usr/bin/env python3
"""
Golem Protocol Client Handout
Helper to interact with the Golem Lattice Authentication Oracle.
"""
import sys
import socket
import json

def interact(host="127.0.0.1", port=1341):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))
    
    buf = ""
    while True:
        chunk = s.recv(1024).decode("utf-8", errors="ignore")
        if not chunk:
            break
        print(chunk, end="")
        if "Select Command" in chunk or "Enter response" in chunk:
            cmd = input()
            s.sendall(cmd.encode("utf-8") + b"\n")

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 1341
    interact(h, p)
