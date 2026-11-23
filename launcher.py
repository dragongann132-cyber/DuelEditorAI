import socket
import sys
import threading
import webbrowser

def find_free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

def main():
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    sys.argv = [
        "streamlit", "run", "app.py",
        "--server.headless=true",
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--browser.gatherUsageStats=false",
    ]
    threading.Timer(3.0, lambda: webbrowser.open(url)).start()
    from streamlit.web.cli import main as streamlit_main
    streamlit_main()

if __name__ == "__main__":
    main()
