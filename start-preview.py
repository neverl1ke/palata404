from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os, webbrowser
os.chdir(Path(__file__).resolve().parent)
server=ThreadingHTTPServer(('127.0.0.1',8044),SimpleHTTPRequestHandler)
print('http://127.0.0.1:8044/Game/index.html?avatarCore=1')
webbrowser.open('http://127.0.0.1:8044/Game/index.html?avatarCore=1')
server.serve_forever()
