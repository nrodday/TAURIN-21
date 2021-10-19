import fabric

from fabric import Connection



c = Connection(
    host="nlnog",
    user="rgnet",
    forward_agent=True,
    connect_kwargs={
        "passphrase": "nlnog"
    }
)

command = "ring-all -n 5 -t 300 traceroute 184.164.235.1 -A -m 32 -I > trcrt_sshconntest"
result = c.run(command)

print(result)