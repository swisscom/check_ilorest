# check_ilorest

This is the public repository for the check_ilorest monitoring plugin.

check_ilorest is a monitoring plugin to monitor the hardware health on HPE servers.

The plugin uses the `ilorest` command in the background, to query the hardware status from ILO (on HPE servers).

Authors:
- Swisscom (Schweiz) AG
- Claudio Kuenzler

This monitoring plugin was developped at and for Swisscom (Schweiz) AG and was published as open source software in 2025.

## Monitoring Plugin
The plugin was developped for the purpose to easily integrate into classic system monitoring software, such as Icinga or Nagios


## Prometheus readiness
The plugin can be executed with the optional parameter `-o` to choose a different output format. By using `-o prometheus` the plugin outputs the information in Prometheus metrics exposition format. It could be used in combination with the Prometheus script_exporter to execute the plugin and scrape the metrics through Script Exporter's API.

```
[root@linux ~]# python3 check_ilorest.py -o prometheus
#HELP ilorest_hardware_health Health status of server. 0=OK, 1=Warning, 2=Critical
#TYPE ilorest_hardware_health gauge
ilorest_hardware_health 2
```

## Compatibility with ProLiant server generations
The `ilorest` command, used in the background of the plugin, queries the Redfish API integrated into the ILO controller. Newer server generations have a better and more detailled implementation inside ILO, allowing to query more information and more hardware elements.

- Gen9: Works but with very limited number of hardware elements, shows overall health state
- Gen10: Works
- Gen11: Works
