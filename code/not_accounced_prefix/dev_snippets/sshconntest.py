import os
import sys
import paramiko

import configparser

##############################################################
# Reading from the Config File
config = configparser.ConfigParser()
config.read('../config.ini')



client = paramiko.SSHClient()
#client.set_missing_host_key_policy(paramiko.WarningPolicy())
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.load_system_host_keys()

# set connection details
hostkeytype = None
hostkey = None
hostname = config['nlnog.account']['hostname']

pkey_file = paramiko.RSAKey.from_private_key_file("/home/luke/.ssh/nlnog", "nlnog")



# Connect
client.connect(hostname, 22, username="rgnet", allow_agent=True, pkey=pkey_file, passphrase="nlnog")
# Obtain session
session = client.get_transport().open_session()
handler = paramiko.agent.AgentRequestHandler(session)
paramiko.channel.Channel.request_forward_agent(session, handler)
#session.get_pty()
#session.invoke_shell()
# Forward local agent

# Commands executed after this point will see the forwarded agent on
# the remote end.
session.exec_command("ring-all -n 5 -t 300 traceroute 184.164.235.1 -A -m 32 -I > trcrt_sshconntest_3")
#session.exec_command("sleep 10")



exit()




#print("Enter SSH Key pass: ")
# request pass from user
#passphrase = sys.stdin.readline().strip('\n')
#pkey = paramiko.RSAKey.from_private_key(pkey_file, passphrase)
#pkey = paramiko.RSAKey.from_private_key(pkey_file)

def start():
    try :
        client.connect(hostname, 22,  look_for_keys=True, allow_agent=True, username="rgnet", pkey=pkey_file)
        return True
    except Exception as e:
        #client.close()
        print(e)
        return False

while start():
    key = True
    cmd = input("Command to run: ")
    if cmd == "":
        break
    chan = client.get_transport().open_session()
    print("running '%s'" % cmd)
    chan.exec_command(cmd)
    while key:
        if chan.recv_ready():
            print("recv:\n%s" % chan.recv(4096).decode('ascii'))
        if chan.recv_stderr_ready():
            print("error:\n%s" % chan.recv_stderr(4096).decode('ascii'))
        if chan.exit_status_ready():
            print("exit status: %s" % chan.recv_exit_status())
            key = False
            client.close()

client.close()




'''

# prepare ssh client
ssh = paramiko.SSHClient()

# set connection details
hostkeytype = None
hostkey = None
hostname = config['nlnog.account']['hostname']

# initiate the client
client = paramiko.SSHClient()
client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))

# prepare private keyfile
pkey_file = open(os.path.expanduser(config['nlnog.account']['pkey_file']))
print("Enter SSH Key pass: ")
# request pass from user
passphrase = sys.stdin.readline().strip('\n')
pkey = paramiko.RSAKey.from_private_key(pkey_file, passphrase)
# connect to server
client.connect(hostname, 22, username="rgnet", pkey=pkey)


'''