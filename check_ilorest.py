#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# Script for checking hardware health of HPE servers using ilorest
#@---------------------------------------------------------------------
# Copyright 2024-2025 Swisscom (Schweiz) AG
# Copyright 2024-2025 Claudio Kuenzler
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#@---------------------------------------------------------------------
#@ History:
#@ 20240213-20240229 R+D phase
#@ 20240305 Prometheus output for all components
#@ 20240318 Improve output when unable to parse JSON from ilorest cmd
#@ 20240320 Add TMPDIR parameter
#@ 20240409 Check for ilorest command as dependency
#@ 20240805 Add support for Gen9 servers
#@ 20250205 Bugfix in prometheus output
#@ 20250827 Adjustments for public release as open source software (1.0.0)
#@ 20251028 Add metrics parameter for System Usage metrics (1.1.0)
#@ 20251028 Add version parameter to show plugin version (1.1.0)
#@---------------------------------------------------------------------
import sys
import time
import json
import subprocess
import argparse
import re

# Define version
pluginversion='1.1.0'
# Define variables and defaults
output_format='nagios'
ilo_user=''
ilo_password=''
ilo_url=''
metrics=False
verbose=False
timeout=60
tmpdir=''
serverinfo=''
perfdata=[]
ignore_list=[]
ok_list=[]
alert_list=[]
warning_list=[]
critical_list=[]
ExitOK=0
ExitWarning=1
ExitCritical=2
ExitUnknown=3
# ---------------------------------------------------------------------
# Arguments
def getargs() :
  parser = argparse.ArgumentParser(description='Check hardware health of HPE servers using ilorest command')
  parser.add_argument('-u', '--user', dest='user', required=False, help='Set ILO username (TODO)')
  parser.add_argument('-p', '--password', dest='password', required=False, help='Set ILO password (TODO)')
  parser.add_argument('-a', '--address', dest='url', required=False, help='Set ILO Address (URL) if connecting to a remote ILO (TODO)')
  parser.add_argument('-i', '--ignore', dest='ignore_list', required=False, help='Ignore specific components (TODO)')
  parser.add_argument('-t', '--tmpdir', dest='tmpdir', required=False, help='Set path for temporary files created by ilorest (defaults to environment $TMPDIR variable, usually /tmp)')
  parser.add_argument('-o', '--output', dest='output_format', choices=['nagios', 'prometheus'], required=False, help='Set output type to either nagios or prometheus (defaults to nagios)')
  parser.add_argument('-m', '--metrics', dest='metrics', action='store_true', default=False, required=False, help='Show performance data/metrics for system usage')
  parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, required=False, help='Enable verbose mode for debugging plugin')
  parser.add_argument('-V', '--version', dest='version', action='store_true', default=False, required=False, help='Show plugin version')
  args = parser.parse_args()
  
  if (args.version):
      print('check_ilorest v{}'.format(pluginversion))
      sys.exit(ExitOK)

  if (args.user and not args.password) or (args.password and not args.user):
      print('UNKNOWN: Define both user and password, not just one of these!')
      sys.exit(ExitUnknown)

  if (args.user): 
      ilo_user=args.user
  
  if (args.password):
      ilo_password=args.password
  
  if (args.url):
      ilo_url=args.url

  if (args.metrics):
      global metrics
      metrics = args.metrics

  if (args.verbose):
      global verbose
      verbose = args.verbose

  if (args.tmpdir):
      global tmpdir
      tmpdir = args.tmpdir
      verboseoutput("TMPDIR is set to %s" % (tmpdir))

  if (args.output_format):
      global output_format
      output_format = args.output_format
      verboseoutput("Output format is %s" % (output_format))
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# Verbose output for debugging help
def verboseoutput(*message) :
    if verbose is True:
        print(time.strftime("%Y%m%d %H:%M:%S"), message)
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# Check ilorest dependency
def dep_ilorest() :
  verboseoutput("Checking for ilorest command as dependency")
  cmd = "type ilorest"
  process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
  output, err = process.communicate()
  retcode = process.poll()
  if (retcode > 0):
    verboseoutput("Problem finding ilorest command as dependency")
    print("ILOREST HARDWARE UNKNOWN: ilorest command not found")
    sys.exit(ExitUnknown)
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# Check ComputerSystem
def check_computersystem() :
  try:
      if tmpdir:
          #cmd = "export TMPDIR=%s; cat tests/gen11-computersystem-degraded.json" % tmpdir # FOR USING TEST JSON
          cmd = "export TMPDIR=%s; ilorest --nocache --nologo get --select ComputerSystem. --json" % tmpdir # FOR NORMAL USE
      else:
          #cmd = "cat tests/gen11-computersystem-degraded.json" # FOR USING TEST JSON
          cmd = "ilorest --nocache --nologo get --select ComputerSystem. --json" # FOR NORMAL USE
      verboseoutput("Launching command: %s" % (cmd))
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
      output, err = process.communicate()
      retcode = process.poll()
  except OSError as e:
      print("ILOREST HARDWARE UNKNOWN: Executing command failed: %s" % (cmd))
      sys.exit(ExitUnknown)

  # Verify we have working JSON data
  try:
      data = json.loads(output)
  except json.JSONDecodeError as e:
      print("ILOREST HARDWARE CRITICAL: Unable to decode JSON, Error: {}. Manually run command ({}) to verify JSON output.".format(e, cmd))
      sys.exit(ExitUnknown)

  # Retrieve server information
  cs_HostName = data['HostName']
  cs_Manufacturer = data['Manufacturer']
  cs_Model = data['Model']
  verboseoutput("Detected Server Model: %s" % (cs_Model))
  cs_SerialNumber = data['SerialNumber']
  cs_BiosVersion = data['BiosVersion'].rstrip()
  if re.search("Gen9$", cs_Model):
      cs_Status_HealthRollup = data['Status']['Health']
  else:
      cs_Status_HealthRollup = data['Status']['HealthRollup']
      cs_AggregateServerHealth = data['Oem']['Hpe']['AggregateHealthStatus']['AggregateServerHealth']

  global serverinfo
  if output_format == 'nagios':
    serverinfo = "Server: %s %s, S/N: %s, System BIOS: %s" % (cs_Manufacturer, cs_Model, cs_SerialNumber, cs_BiosVersion)

  # Health Status
  if cs_Status_HealthRollup != "OK":
    verboseoutput("AggregateServerHealth Rollup shows {}".format(cs_Status_HealthRollup))
    alert_list.append("AggregateHealthStatus")
  if (re.search("Gen9$", cs_Model) == None) and (data['Oem']['Hpe']['AggregateHealthStatus']):
    healthdetail = data['Oem']['Hpe']['AggregateHealthStatus']
    healthkey = 'Status'
    verboseoutput("Iterating over each hardware component")
    verboseoutput(healthdetail)
    parse_json_recursively(healthdetail, healthkey)

  # Performance data / metrics for System Usage
  if metrics:
    global perfdata
    if data['Oem']['Hpe']['SystemUsage']:
      systemusage = data['Oem']['Hpe']['SystemUsage']
      usagekey = 'SystemUsage'
      verboseoutput("Iterating over each SystemUsage entry")
      verboseoutput(systemusage)
      if output_format == 'nagios':
        perfdata.append("|")
      for key in systemusage:
        verboseoutput("System metric {} found with value {}".format(key, systemusage[key]))
        if output_format == 'prometheus':
          perfdata.append("#HELP ilorest_hardware_{}".format(key))
          perfdata.append("#TYPE ilorest_hardware_{} gauge".format(key))
          perfdata.append("ilorest_hardware_{} {}".format(key, systemusage[key]))
        else:
          if re.search("Util$", key):
            perfdata.append("{}={};;;0;100".format(key, systemusage[key]))
          else:
            perfdata.append("{}={};;;;".format(key, systemusage[key]))
      if output_format == 'prometheus':
        perfdata = '\n'.join(perfdata)
      else:
        perfdata = ' '.join(perfdata)
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
def parse_json_recursively(json_object, target_key, *parent_key):
    if type(json_object) is dict and json_object:
        for key in json_object:
            verboseoutput("Key: {}, Parent Key: {}".format(key, parent_key))
            if key == target_key: # Found Health key
                pkey = "".join(parent_key) # Parent Key is a tuple, need to convert to str
                verboseoutput("Health status of {} is {}".format(pkey, json_object[key]['Health']))
                if json_object[key]['Health'] == 'Critical':
                    critical_list.append(pkey)
                elif json_object[key]['Health'] == 'Warning':
                    warning_list.append(pkey)
                else:
                    ok_list.append(pkey)
            else: # Continue iterating
                parse_json_recursively(json_object[key], target_key, key)
# ************************************************************************************
# Main
if __name__ == '__main__':
  getargs()
  dep_ilorest()

  # Hardware checks
  check_computersystem()

  # Merge alerts
  alert_list = alert_list + warning_list + critical_list

  if alert_list: # Hardware problems
      if output_format == 'prometheus':
          print("#HELP ilorest_hardware_health Overall health status of server. 0=OK, 1=Warning, 2=Critical")
          print("#TYPE ilorest_hardware_health gauge")
          if critical_list:
              print("ilorest_hardware_health 2")
              exitcode=2
          elif warning_list:
              print("ilorest_hardware_health 1")
              exitcode=1
          for component in critical_list:
              print("#HELP ilorest_hardware_health_{} Health status of hardware component {}".format(component.lower(), component))
              print("#TYPE ilorest_hardware_health_{} gauge".format(component.lower()))
              print("ilorest_hardware_health_{} 2".format(component.lower()))
          for component in warning_list:
              print("#HELP ilorest_hardware_health_{} Health status of hardware component {}".format(component.lower(), component))
              print("#TYPE ilorest_hardware_health_{} gauge".format(component.lower()))
              print("ilorest_hardware_health_{} 1".format(component.lower()))
          for component in ok_list:
              print("#HELP ilorest_hardware_health_{} Health status of hardware component {}".format(component.lower(), component))
              print("#TYPE ilorest_hardware_health_{} gauge".format(component.lower()))
              print("ilorest_hardware_health_{} 0".format(component.lower()))
          if perfdata:
              print(perfdata)
          sys.exit(exitcode)
      else:
          if critical_list:
              print("ILOREST HARDWARE CRITICAL: {}, {}".format(alert_list, serverinfo))
              sys.exit(ExitCritical)
          else:
              print("ILOREST HARDWARE WARNING: {}, {}".format(alert_list, serverinfo))
              sys.exit(ExitWarning)
  else: # Hardware OK
      if output_format == 'prometheus':
          print("#HELP ilorest_hardware_health Overall health status of server. 0=OK, 1=Warning, 2=Critical")
          print("#TYPE ilorest_hardware_health gauge")
          print("ilorest_hardware_health 0")
          for component in ok_list:
            print("#HELP ilorest_hardware_health_{} Health status of hardware component {}".format(component.lower(), component))
            print("#TYPE ilorest_hardware_health_{} gauge".format(component.lower()))
            print("ilorest_hardware_health_{} 0".format(component.lower()))
          if perfdata:
            print(perfdata)
          sys.exit(ExitOK)
      else:
          print("ILOREST HARDWARE OK: Hardware is healthy. {} {}".format(serverinfo, perfdata))
          sys.exit(ExitOK)

  print("UNKNOWN: Should never reach this part")
  sys.exit(ExitUnknown)
