from pathlib import Path
import socket, shutil

def tcp(port):
    s=socket.socket(); s.settimeout(1)
    try:
        s.connect(("127.0.0.1",port)); return True
    except OSError: return False
    finally: s.close()

def main():
    print("docker binary:", "available" if shutil.which("docker") else "unavailable")
    print("PostgreSQL:", "reachable" if tcp(5432) else "not running")
    print("Redis:", "reachable" if tcp(6379) else "not running")
    return 0

if __name__=="__main__": raise SystemExit(main())
