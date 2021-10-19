import subprocess

subprocess.run(["ssh", "nlnog", "ring-all", "-n", "5", "-t", "300", "traceroute", "184.164.235.1", "-A", "-m", "32", "-I", ">", "trcrt_sshconntest"])