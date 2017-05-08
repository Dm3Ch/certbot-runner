import sys
import hashlib
import yaml
from subprocess import check_call

def getConfigFileHash(file):
    return hashlib.sha256(file.read()).hexdigest()

def certbotAccountSet(email):
    """Sets certbot account"""
    check_call(["/tmp/certbot-auto", "register", "-m", email, "--agree-tos", "-n"])

def certbotIssueCert(certName, domainNames, dryRun):
    """Issue cert"""
    command = ["/tmp/certbot-auto", "certonly", "-n", "--standalone", "--preferred-challenges", "http"]
    if dryRun:
        command.append("--dry-run")
    for domainName in domainNames:
        command.append("-d")
        command.append(domainName)
    command.append("--cert-name")
    command.append(certName)
    check_call(command)

if len(sys.argv) < 2:
    print("Specify config file")
    sys.exit(-1)

configStream = open(sys.argv[1], 'rb')
configHash = getConfigFileHash(configStream)
print("Config file hash:", configHash)
configStream.close()

configStream = open(sys.argv[1], 'r')
config = yaml.load(configStream)
email = config['email']
dryRun = bool(config['dryRun'])
certs = config['certs']
configStream.close()

certbotAccountSet(email)

for cert in certs:
    certbotIssueCert(cert['certName'], cert['domainNames'], dryRun)