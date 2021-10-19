import paramiko
import time

# Connect
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# pkey_file = paramiko.RSAKey.from_private_key_file("/home/luke/.ssh/nlnog", "nlnog")
pkey_file = "/home/luke/.ssh/nlnog"
#client.connect("coloclue01.ring.nlnog.net", 22, "rgnet", pkey="~/.ssh/nlnog", passphrase="nlnog", allow_agent=True)
client.connect("coloclue01.ring.nlnog.net", username="rgnet", key_filename=pkey_file, allow_agent=True, passphrase="nlnog")
# Obtain session
#session = client.get_transport().open_session()

# Forward local agent
#paramiko.agent.AgentRequestHandler(session)

# Commands executed after this point will see the forwarded agent on
# the remote end.
# command = "sleep 10"
command1 = "env > env_output"
command2 = "cat trcrt_paramikotest"
command3 = "/usr/local/bin/ring-all -n 5 -t 60 traceroute 184.164.235.1 -A -m 32 -I > trcrt_paramikotest_2"

#session.get_pty()
#stdin, stdout, stderr = client.exec_command(command3)




sleeptime = 0.001
outdata, errdata = '', ''
ssh_transp = client.get_transport()
chan = ssh_transp.open_session()
# chan.settimeout(3 * 60 * 60)
chan.setblocking(0)

paramiko.agent.AgentRequestHandler(chan)
chan.get_pty()

chan.exec_command(command3)
while True:  # monitoring process
    # Reading from output streams
    while chan.recv_ready():
        outdata += str(chan.recv(1000))
    while chan.recv_stderr_ready():
        errdata += str(chan.recv_stderr(1000))
    if chan.exit_status_ready():  # If completed
        break
    time.sleep(sleeptime)
retcode = chan.recv_exit_status()
ssh_transp.close()

print(outdata)
print(errdata)