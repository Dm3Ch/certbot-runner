import sys
import traceback
import hashlib
import yaml
import logging
from subprocess import check_call, call

from raven import Client
from raven.handlers.logging import SentryHandler
from raven.conf import setup_logging

# Specify default certbot command
certbotBinPath = "certbot"

def getConfigFileHash(file):
    return hashlib.sha256(file.read()).hexdigest()

def certbotAccountSet(email):
    """Sets certbot account"""
    call([certbotBinPath, "register", "-m", email, "--agree-tos", "-n"])

def certbotIssueCert(certName, domainNames, dryRun):
    """Issue cert"""
    command = [certbotBinPath, "certonly", "-n", "--standalone", "--preferred-challenges", "http"]
    if dryRun:
        command.append("--dry-run")
    for domainName in domainNames:
        command.append("-d")
        command.append(domainName)
    command.append("--cert-name")
    command.append(certName)
    check_call(command)


def certbotWork():
    """Issue or renew certs"""
    if configHash != oldConfigHash:
        check_call(["/bin/sh", "-c", "rm -rf /etc/letsencrypt/*"])
        check_call(["/bin/sh", "-c", "rm -rf " + certsDir + "/*"])

        print("\nSetting account:\n")
        certbotAccountSet(email)

        print("\nIssuing certs:\n")
        logger.info("Certbot runner is issuing certs")

        for cert in certs:
            certbotIssueCert(cert['certName'], cert['domainNames'], dryRun)

        if not dryRun:
            print("\nCopying certs to destination dir:\n")
            check_call(["/bin/sh", "-c", "cp -r /etc/letsencrypt/live/* " + certsDir])

            oldConfigHashFile = open(certsDir + '/config.hash', 'w')
            oldConfigHashFile.write(configHash)
            oldConfigHashFile.close()
    else:
        print("\nSetting account:\n")
        certbotAccountSet(email)
        print("\nRenewing certs:\n")
        logger.info("Certbot runner is renewing certs")
        check_call([certbotBinPath, "renew", "-n", "--standalone", "--preferred-challenges", "http"])
        print("\nCopying certs to destination dir:\n")
        check_call(["/bin/sh", "-c", "cp -rf /etc/letsencrypt/live/* " + certsDir])

if len(sys.argv) < 2:
    print("Specify config file")
    sys.exit(-1)

configStream = open(sys.argv[1], 'rb')
configHash = getConfigFileHash(configStream)
print("Config file hash:", configHash)
configStream.close()

configStream = open(sys.argv[1], 'r')
config = yaml.load(configStream)
certsDir = config['certsDir']

# Old config check start
oldConfigHash = ''
try:
    oldConfigHashFile = open(certsDir + '/config.hash', 'r')
    oldConfigHash = oldConfigHashFile.read()
    print("Old config file hash:", oldConfigHash)
    oldConfigHashFile.close()
except FileNotFoundError:
    print("Old config file doesn't exists")
print()
# Old config check ends

certbotBinPath = config['certbotBinPath']
email = config['email']
dryRun = bool(config['dryRun'])
certs = config['certs']
alwaysZeroReturnCode = bool(config["alwaysZeroReturnCode"])
if alwaysZeroReturnCode:
    print("Always zero return code mode is enabled")
sentryEnable = bool(config["sentryEnable"])
if sentryEnable:
    sentryDSN = config["sentryDSN"]
    print("Sentry reporting enabled, sentry DSN was found in config")
    sentryClient = Client(sentryDSN)
    handler = SentryHandler(sentryClient)
    handler.setLevel(logging.INFO)
    setup_logging(handler)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
configStream.close()

if sentryEnable:
    logger.info("Certbot runner was started")

try:
    certbotWork()
except KeyboardInterrupt:
    pass
except Exception:
    if sentryEnable:
        sentryClient.captureException()

    if alwaysZeroReturnCode:
        traceback.print_exc()
        print("\n Real exit status: 0")
        sys.exit()
    else:
        raise

if sentryEnable:
    logger.info("Certbot runner has successfully ended")