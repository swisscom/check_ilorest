# check_ilorest

This is the public repository for the check_ilorest monitoring plugin.

check_ilorest is a monitoring plugin to monitor the hardware health on HPE servers.

The plugin uses the `ilorest` command in the background, to query the hardware status from ILO (on HPE servers).

Authors:
- Swisscom (Schweiz) AG
- Claudio Kuenzler

This monitoring plugin was developed at and for Swisscom (Schweiz) AG and was published as open source software in 2025.

# Usage

## Requirements
As mentioned, `check_ilorest` uses the `ilorest` command. This command can be installed as RPM package, as PyPI package (using `pip3`) or built from source. Have a look at the official [ilorest repository](https://github.com/HewlettPackard/python-redfish-utility). The [ilorest user guide](https://servermanagementportal.ext.hpe.com/docs/redfishclients/ilorest-userguide/installation/) lists different installation method.

Besides `ilorest` available as command, the following requirements are needed:
- python3
- Must be run locally on a HPE server (remote ILO target is TODO)
- Must be run as root (`ilorest` requirement)

## Monitoring Plugin
The plugin was developped for the purpose to easily integrate into classic system monitoring software, such as Icinga or Nagios.

```
root@linux ~ # /usr/lib64/nagios/plugins/check_ilorest.py
ILOREST HARDWARE OK: Hardware is healthy. Server: HPE ProLiant DL380 Gen11, S/N: XXXXXXXXXX, System BIOS: U54 v1.40 (06/29/2023)
```

The exit codes of `check_ilorest` are based on other monitoring plugins and follow the monitoring plugin development guidelines. 

- Exit Code 0: OK, no hardware problems detected
- Exit Code 1: WARNING, degraded hardware detected
- Exit Code 2: CRITICAL, hardware failure detected
- Exit Code 3: UNKNOWN, there was a problem executing `check_ilorest` correctly


## Prometheus readiness
`check_ilorest` was developed for both classic and metrics-based monitoring tools. The plugin can be executed with the optional parameter `-o` to choose a different output format. By using `-o prometheus` the plugin outputs the information in Prometheus metrics exposition format. It could be used in combination with the Prometheus [Script Exporter](https://github.com/ricoberger/script_exporter) to execute the plugin and scrape the metrics through Script Exporter's API.

```
root@linux ~ # /usr/lib64/nagios/plugins/check_ilorest.py -o prometheus
#HELP ilorest_hardware_health Overall health status of server. 0=OK. 1=Warning. 2=Critical
#TYPE ilorest_hardware_health gauge
ilorest_hardware_health 0
#HELP ilorest_hardware_health_biosorhardwarehealth Health status of hardware component BiosOrHardwareHealth
#TYPE ilorest_hardware_health_biosorhardwarehealth gauge
ilorest_hardware_health_biosorhardwarehealth 0
#HELP ilorest_hardware_health_fans Health status of hardware component Fans
#TYPE ilorest_hardware_health_fans gauge
ilorest_hardware_health_fans 0
#HELP ilorest_hardware_health_memory Health status of hardware component Memory
#TYPE ilorest_hardware_health_memory gauge
ilorest_hardware_health_memory 0
#HELP ilorest_hardware_health_network Health status of hardware component Network
#TYPE ilorest_hardware_health_network gauge
ilorest_hardware_health_network 0
#HELP ilorest_hardware_health_powersupplies Health status of hardware component PowerSupplies
#TYPE ilorest_hardware_health_powersupplies gauge
ilorest_hardware_health_powersupplies 0
#HELP ilorest_hardware_health_processors Health status of hardware component Processors
#TYPE ilorest_hardware_health_processors gauge
ilorest_hardware_health_processors 0
#HELP ilorest_hardware_health_smartstoragebattery Health status of hardware component SmartStorageBattery
#TYPE ilorest_hardware_health_smartstoragebattery gauge
ilorest_hardware_health_smartstoragebattery 0
#HELP ilorest_hardware_health_storage Health status of hardware component Storage
#TYPE ilorest_hardware_health_storage gauge
ilorest_hardware_health_storage 0
#HELP ilorest_hardware_health_temperatures Health status of hardware component Temperatures
#TYPE ilorest_hardware_health_temperatures gauge
ilorest_hardware_health_temperatures 0
```

## Compatibility with ProLiant server generations
The `ilorest` command, used in the background of the plugin, queries the Redfish API integrated into the ILO controller. Newer server generations have a better and more detailled implementation inside ILO, allowing to query more information and more hardware elements.

- Gen9: Works but with very limited number of hardware elements, shows overall health state
- Gen10: Works
- Gen11: Works

## ToDos
- Support remote ILO (using `-a` and credentials)
- Support ignore list to ignore specific discovered hardware elements
