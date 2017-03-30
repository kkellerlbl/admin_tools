#!/usr/bin/env python

import json
import requests
import os
import pprint
import datetime
import sys
import configparser
from collections import defaultdict

dump=False

def usage():
    print "usage: %s <prod|ci|appdev|next> <|clients|suspend|job> [job text] -d -n" % (sys.argv[0])
    print "  -d dump json for some commands"
    print "  -n no op for some commands (suspend|cancel)"


def dumpdata(data):
  if dump:
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data['data'])
  

def list_clients(baseurl,token,showjobs):
  url = baseurl+"client" #?query&limit=5000&state=in-progress"
  header={'Authorization': 'OAuth '+token}
  req = requests.get(url, headers=header)
  #resp = urllib2.urlopen(req)
  if req.status_code==200:
    data = json.loads(req.text)
    dumpdata(data)
  else:
    print req.status_code
    sys.exit()

  for d in data['data']:
    print '%-40.40s %36.36s %-20s %-20s %-20.20s %6d'%(d['name'],d['id'],d['host'],d['group'],d['Status'],d['idle_time'])
    if showjobs and 'current_work' in d:
       for j in d['current_work'].keys():
          print "                       %-40.40s" % (j)


def get_jobs(baseurl,token,status):
  url = baseurl+"jobs?query&state="+status #in-progress"
  header={'Authorization': 'OAuth '+token}
  req = requests.get(url, headers=header)

  data = json.loads(req.text)

  dumpdata(data)
  return data['data']

def list_jobs(baseurl,token):
  for status in ['in-progress','queued']:
    data=get_jobs(baseurl,token,status)
    for d in data:
      i=d['info']
      print '%-16.16s   %-16.16s   %-36.36s   %-50.50s %-20.20s %-20s %-20s'%(i['submittime'],i['startedtime'],d['id'],i['name'],i['clientgroups'],i['user'],d['state'])

def cancel_jobs(baseurl,token,other,dryrun):
  for status in ['in-progress','queued']:
    data=get_jobs(baseurl,token,status)
    for d in data:
      i=d['info']
      line='%-22.22s %-36.36s %-50.50s %-20.20s %-20s %-20s'%(i['startedtime'],d['id'],i['name'],i['clientgroups'],i['user'],d['state'])
      if line.find(other)>=0:
         print "Canceling... "+line
         if dryrun is False:
           url = baseurl+"/job/"+d['id']
           header={'Authorization': 'OAuth '+token}
           req = requests.delete(url, headers=header)

def suspend_jobs(baseurl,token,other,dryrun):
  for status in ['in-progress','queued']:
    data=get_jobs(baseurl,token,status)
    for d in data:
      i=d['info']
      line='%-22.22s %-36.36s %-50.50s %-20.20s %-20s %-20s'%(i['startedtime'],d['id'],i['name'],i['clientgroups'],i['user'],d['state'])
      if line.find(other)>=0:
         print "Suspending... "+line
         if dryrun is False:
           url = baseurl+"/job/"+d['id']+'?suspend'
           header={'Authorization': 'OAuth '+token}
           req = requests.put(url, headers=header)

def get_job(baseurl,token,job):
    url = baseurl+"job/"+job
    header={'Authorization': 'OAuth '+token}
    req = requests.get(url, headers=header)
    data = json.loads(req.text)
    dumpdata(data)
    d=data['data']
    i=d['info']
    line='%-22.22s %-36.36s %-50.50s %-20.20s %-20s %-20s'%(i['startedtime'],d['id'],i['name'],i['clientgroups'],i['user'],d['state'])
    print line

def create_cgroup(baseurl,token,group, dryrun):
    url = baseurl+"cgroup/"+group
    header={'Authorization': 'OAuth '+token}
    req = requests.post(url, headers=header)
    data = json.loads(req.text)
    dumpdata(data)
    d=data['data']
    print d['token']

def get_cgroups(baseurl,token):
    url = baseurl+"cgroups"
    header={'Authorization': 'OAuth '+token}
    req = requests.get(url, headers=header)
    data = json.loads(req.text)
    dumpdata(data)
    d=data['data']
    for c in d:
       print "%-15.15s %s\n" % (c['name'],c['token'])
    #line='%-22.22s %-36.36s %-50.50s %-20.20s %-20s %-20s'%(i['startedtime'],d['id'],i['name'],i['clientgroups'],i['user'],d['state'])

def main():
  global dump
  showjobs=False
  dryrun=False
  deploy=None

  if len(sys.argv) == 1:
     usage()
     sys.exit(1)

  config = configparser.ConfigParser()
  config.read('config.ini')

  action='jobs'
  actions = ['clients', 'jobs', 'suspend', 'cancel', 'job', 'cgroups', 'create_cgroup' ]

  other = []
  for arg in sys.argv[1:]:
    if arg == '-d':
      dump=True
    elif arg == '-j':
      showjobs=True
    elif arg == '-n':
      dryrun=True
    elif arg in actions:
      action=arg
    elif arg in config.sections():
      deploy=arg
    else:
      other.append(arg)

  if deploy is None:
    print "I didn't find a deployment specified."
    sys.exit(1)

  token=config[deploy]['token'] 
  baseurl=config[deploy]['url'] 

  if action == 'clients':
    list_clients(baseurl,token,showjobs)
  elif action == 'jobs':
    list_jobs(baseurl,token)
  elif action == 'cancel':
    cancel_jobs(baseurl,token,other[0],dryrun)
  elif action == 'suspend':
    suspend_jobs(baseurl,token,other[0],dryrun)
  elif action == 'job':
    get_job(baseurl,token,other[0])
  elif action == 'cgroups':
    get_cgroups(baseurl,token)
  elif action == 'create_cgroup':
    create_cgroup(baseurl,token,other[0],dryrun)


if __name__ == "__main__":
    main()
