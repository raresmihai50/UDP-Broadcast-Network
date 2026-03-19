import socket
import sys
import time
import hashlib
import os
import threading

def read_config(config_path):
    nodes = []
    with open(config_path, 'r') as f:
        lines = f.readlines()
        
    n_broadcasts = int(lines[0].strip())
    
    for line in lines[1:]:
        line = line.split('#')[0].strip() # Ignora comentariile
        if line:
            parts = line.split()
            nodes.append((parts[0], int(parts[1])))
            
    return n_broadcasts, nodes

# def receiver_thread(node_index, listen_ip, listen_port, expected_total):
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.bind((listen_ip, listen_port))
#     # Insista maxim 5 secunde pe o citire
#     sock.settimeout(5.0) 

#     received_count = 0
#     log_filename = f"node_{node_index}_messages.log"
#     err_filename = f"node_{node_index}_errors.log"

#     with open(log_filename, "w") as log_file, open(err_filename, "a") as err_file:
#         while received_count < expected_total:
#             try:
#                 # La UDP, citirea este atomica 
#                 data, addr = sock.recvfrom(1024)
                
#                 if len(data) != 1024:
#                     err_file.write(f"Eroare: S-a primit un pachet incorect ({len(data)} bytes)\n")
#                     continue

#                 # Extrage datele conform formatului
#                 sender_idx = data[0]
#                 payload = data[:1004]
#                 received_sha1 = data[1004:1024]
                
#                 # Calculeaza SHA-1 (bytes 0-1003)
#                 calculated_sha1 = hashlib.sha1(payload).digest()

#                 # Verifica potrivirea
#                 status = "OK" if received_sha1 == calculated_sha1 else "FAIL"
                
#                 received_hex = received_sha1.hex()
#                 calc_hex = calculated_sha1.hex()

#                 # Salveaza in log
#                 log_file.write(f"{status} {sender_idx} {received_hex} {calc_hex}\n")
#                 log_file.flush()

#                 received_count += 1

#             except socket.timeout:
#                 # Timeout-ul de 5 secunde a expirat, continua bucla
#                 continue
#             except Exception as e:
#                 err_file.write(f"Eroare la recepție: {e}\n")
#                 err_file.flush()

def receiver_thread(node_index, listen_ip, listen_port, expected_total):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_ip, listen_port))
    # Insistăm maxim 5 secunde pe o citire (conform cerinței)
    sock.settimeout(5.0) 

    received_count = 0
    log_filename = f"node_{node_index}_messages.log"
    err_filename = f"node_{node_index}_errors.log"
    
    # Adăugăm un flag pentru a ști dacă am început să primim mesaje
    started_receiving = False

    with open(log_filename, "w") as log_file, open(err_filename, "a") as err_file:
        while received_count < expected_total:
            try:
                # La UDP, citirea este atomica 
                data, addr = sock.recvfrom(1024)
                
                # Dacă am ajuns aici, înseamnă că am primit cel puțin un pachet
                started_receiving = True 
                
                if len(data) != 1024:
                    err_file.write(f"Eroare: S-a primit un pachet incorect ({len(data)} bytes)\n")
                    continue

                # Extrage datele conform formatului
                sender_idx = data[0]
                payload = data[:1004]
                received_sha1 = data[1004:1024]
                
                # Calculeaza SHA-1 (bytes 0-1003)
                calculated_sha1 = hashlib.sha1(payload).digest()

                # Verifica potrivirea
                status = "OK" if received_sha1 == calculated_sha1 else "FAIL"
                
                received_hex = received_sha1.hex()
                calc_hex = calculated_sha1.hex()

                # Salveaza in log
                log_file.write(f"{status} {sender_idx} {received_hex} {calc_hex}\n")
                log_file.flush()

                received_count += 1

            except socket.timeout:
                # Dacă dă timeout, verificăm dacă am început să primim mesaje sau nu
                if not started_receiving:
                    # Dacă dă timeout dar NU a început încă să primească mesaje
                    # (ex: este încă în acele 15 secunde de așteptare inițială), continuă să asculte.
                    continue
                else:
                    # Dacă dă timeout și DEJA primise mesaje în trecut, înseamnă că fluxul 
                    # s-a oprit de mai bine de 5 secunde. Presupunem că s-au pierdut pe drum.
                    mesaje_pierdute = expected_total - received_count
                    err_file.write(f"Timeout: Au trecut 5 secunde fara mesaje. Se inchide. Pierdute: {mesaje_pierdute}\n")
                    break # IESE DIN BUCLA (termină thread-ul)

            except Exception as e:
                err_file.write(f"Eroare la recepție: {e}\n")
                err_file.flush()

def main():
    if len(sys.argv) != 3:
        print("Utilizare: python bcastnode.py <config.txt> <node_index>")
        sys.exit(1)

    config_path = sys.argv[1]
    node_index = int(sys.argv[2])

    n_broadcasts, nodes = read_config(config_path)
    m_nodes = len(nodes)
    expected_received = n_broadcasts * m_nodes

    my_ip, my_port = nodes[node_index]

    err_filename = f"node_{node_index}_errors.log"
    with open(err_filename, "w") as f:
        f.write(f"--- Log erori nod {node_index} ---\n")

    # 1. Pornim thread-ul de receptie IMEDIAT
    recv_thread = threading.Thread(
        target=receiver_thread, 
        args=(node_index, my_ip, my_port, expected_received)
    )
    recv_thread.start()

    # 2. Asteptam 15 secunde inainte de broadcasting
    print(f"Nodul {node_index} a pornit pe portul {my_port}. Asteptam 15 secunde...")
    time.sleep(15)
    print(f"Nodul {node_index} a inceput broadcasting-ul.")

    # 3. Incepem trimiterea mesajelor
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_sock.settimeout(5.0)

    for _ in range(n_broadcasts):
        byte_0 = bytes([node_index])
        random_bytes = os.urandom(1003) 
        payload = byte_0 + random_bytes
        sha1_hash = hashlib.sha1(payload).digest()
        
        message = payload + sha1_hash

        for ip, port in nodes:
            try:
                send_sock.sendto(message, (ip, port))
            except Exception as e:
                with open(err_filename, "a") as err_file:
                    err_file.write(f"Eroare la trimitere catre {ip}:{port} : {e}\n")
        time.sleep(0.001) # Mică pauză pentru a nu inunda rețeaua instantaneu

    # 4. Asteptam ca receptia sa se finalizeze (se primesc N*M mesaje)
    recv_thread.join()
    print(f"Nodul {node_index} a terminat cu succes!")

if __name__ == "__main__":
    main()