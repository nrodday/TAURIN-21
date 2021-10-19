import pexpect
from pexpect import pxssh


s = pxssh.pxssh(options={
    "IdentityFile": "~/.ssh/nlnog",
    "User": "rgnet"
})

s.login("coloclue01.ring.nlnog.net", "rgnet", "nlnog")

print(s)

s.sendline("ring-all -n 5 -t 300 traceroute 184.164.235.1 -A -m 32 -I > trcrt_sshconntest_5")
s.prompt()
print(s.before)

s.logout()