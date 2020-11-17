# devops.py

import subprocess
import datetime
import sys
import redis


# register your services here - use absolute paths

services = [
    'node::redis-worker.js',
    'node::s3appdb.js'
]

rClient = redis.Redis()

def setv(key, value):
    rClient.set(key, repr(value))

def getv(key):
    result = None
    try:
        result = rClient.get(key).decode()
    except:
        pass
    try:
        result = eval(result)
    except:
        pass
    return result

long_run_time = getv('devops::long_run_time')

if not long_run_time:
    long_run_time = 86400 # restart every 24 hours
    setv('devops::long_run_time', long_run_time)

def now() : return datetime.datetime.today()

def ss(script):
    started = getv('devops::%s::started' % script)
    if not started:
        started = now()
    return (now() - started).total_seconds()

def run_shell(cmd):
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, shell=True)
  out, err = p.communicate()
  if err:
      return err.decode()
  else:
      out = out.decode()
      try:
          return eval(out)
      except:
          return out

def reboot(service):
    runner, script = service.split('::')
    for mode in ['stop', 'start']:
        print(run_shell('sudo forever %s -c %s %s' % ( mode, runner, script )))
    setv('devops::%s::started' % service, now())

status = run_shell('sudo forever logs')

for service in services:
    runner, script = service.split('::')
    if script not in status or ss(script) > long_run_time:
        reboot(service)

sys.exit()
