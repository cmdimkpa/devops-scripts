# update and redeploy service

import subprocess
from hashlib import md5
import sys
import redis

ref_dir = '/home/ubuntu/updater/SnapFill'
reference = '%s/core.js' % ref_dir
target = '/home/ubuntu/SnapFill/SnapFill/core.js'
service = 'node::%s' % target

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

def read_file(file):
    with open(file, 'rb') as handle:
        data = handle.read()
        handle.close()
    return data

def hash(obj):
    hasher = md5(); hasher.update(str(obj).encode())
    return hasher.hexdigest()

# last file hash
last_file_hash = getv('devops::last_file_hash')

if not last_file_hash:
    last_file_hash = hash(read_file(target))
    setv('devops::last_file_hash', last_file_hash)

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

def redeploy(service):
    runner, script = service.split('::')
    for mode in ['stop', 'start']:
        print(run_shell('sudo forever %s -c %s %s' % ( mode, runner, script )))

def pull_and_compare():
    run_shell('cd %s;sudo git pull' % ref_dir)
    reference_hash = hash(read_file(reference))
    # trigger for redeployment
    if reference_hash != last_file_hash:
        # Step 1. Update last_file_hash
        setv('devops::last_file_hash', reference_hash)
        # Step 2. Copy reference to target
        run_shell('sudo cp %s %s' % (reference, target))
        # Step 3. Redeploy service
        redeploy(service)
        # Step 4. Exit
        sys.exit()

pull_and_compare()
