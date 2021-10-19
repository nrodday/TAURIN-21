import subprocess
import sys

HOST="coloclue01.ring.nlnog.net"
# Ports are handled in ~/.ssh/config since we use OpenSSH
COMMAND="ring-all -n 5 -t 300 traceroute 184.164.235.1 -A -m 32 -I > trcrt_sshsubproctest"

ssh = subprocess.Popen(["ssh", HOST, COMMAND],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
result = ssh.stdout.readlines()
if result == []:
    error = ssh.stderr.readlines()
else:
    print(result)


print(ssh.stderr)
