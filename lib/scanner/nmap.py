"""

*********************************************************************************************
*                          NOTICE FROM AUTOSPLOIT DEVELOPERS                                *
*********************************************************************************************
* this is basically an exact copy of                                                        *
* `https://github.com/komand/python-nmap/blob/master/nmap/nmap.py` that has been modified   *
* to better fit into autosploits development. There has been very minimal changes to it     *
* and it still basically functions the exact same way                                       *
*********************************************************************************************


ORIGINAL INFO:
--------------
nmap.py - version and date, see below
Source code : https://bitbucket.org/xael/python-nmap
Author :
* Alexandre Norman - norman at xael.org
Contributors:
* Steve 'Ashcrow' Milner - steve at gnulinux.net
* Brian Bustin - brian at bustin.us
* old.schepperhand
* Johan Lundberg
* Thomas D. maaaaz
* Robert Bost
* David Peltier
Licence: GPL v3 or any later version for python-nmap
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
**************
IMPORTANT NOTE
**************
The Nmap Security Scanner used by python-nmap is distributed
under it's own licence that you can find at https://svn.nmap.org/nmap/COPYING
Any redistribution of python-nmap along with the Nmap Security Scanner
must conform to the Nmap Security Scanner licence

__author__ = 'Alexandre Norman (norman@xael.org)'
__version__ = '0.6.2'
__last_modification__ = '2017.01.07'
"""

#!/usr/bin/env python3
"""
AutoSploit Nmap Scanner Module
Modernized for Python 3.12
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from xml.etree import ElementTree

import lib.jsonize
import lib.errors
import lib.output
import lib.settings


def parse_nmap_args(args: List[str]) -> List[str]:
    """Parse the provided arguments and ask if they aren't in the `known` arguments list."""
    runnable_args = []
    try:
        with open(lib.settings.NMAP_OPTIONS_PATH, 'r', encoding='utf-8') as f:
            known_args = [a.strip() for a in f.readlines()]
    except FileNotFoundError:
        known_args = []
    
    for arg in args:
        if " " in arg:
            tmparg = arg.split(" ")[0]
        else:
            tmparg = arg
        if tmparg in known_args:
            runnable_args.append(arg)
        else:
            choice = lib.output.prompt(
                f"argument: '{arg}' is not in the list of 'known' nmap arguments, "
                "do you want to use it anyways[y/N]"
            )
            if choice.lower() == "y":
                runnable_args.append(tmparg)
    return runnable_args


def write_data(host: str, output: str, is_xml: bool = True) -> str:
    """Dump XML data to a file."""
    backup_path = lib.settings.NMAP_XML_OUTPUT_BACKUP if is_xml else lib.settings.NMAP_JSON_OUTPUT_BACKUP
    Path(backup_path).mkdir(parents=True, exist_ok=True)
    
    file_path = str(Path(backup_path) / f"{host}_{lib.jsonize.random_file_name(length=10)}.{'xml' if is_xml else 'json'}")
    
    with open(file_path, 'a+', encoding='utf-8') as results:
        if is_xml:
            results.write(output)
        else:
            json.dump(output, results, indent=4)
    return file_path


def find_nmap(search_paths: Tuple[str, ...]) -> str:
    """Check if nmap is on the system."""
    for path in search_paths:
        try:
            _ = subprocess.Popen([path, '-V'], bufsize=10000, stdout=subprocess.PIPE, close_fds=True)
        except OSError:
            pass
        else:
            return path
    raise lib.errors.NmapNotFoundException


def do_scan(host: str, nmap_path: str, ports: Optional[str] = None, arguments: Optional[List[str]] = None) -> Tuple[str, str, str]:
    """Perform the nmap scan."""
    if arguments is None:
        arguments = ["-sV"]
    launch_arguments = [
        nmap_path, '-oX', '-', host,
        '-p ' + ports if ports is not None else "",
    ] + arguments
    to_launch = []
    for item in launch_arguments:
        if not item == "":
            to_launch.append(item)
    lib.output.info(f"launching nmap scan against {host} ({' '.join(to_launch)})")
    process = subprocess.Popen(
        launch_arguments, bufsize=10000, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    output, error = process.communicate()
    output_data = output
    nmap_error = error
    nmap_error_tracestack = []
    nmap_warn_tracestack = []
    if len(nmap_error) > 0:
        for line in nmap_error.split(os.linesep):
            if len(line) != 0:
                if lib.settings.NMAP_ERROR_REGEX_WARNING.search(line) is not None:
                    nmap_warn_tracestack.append(line + os.linesep)
                else:
                    nmap_error_tracestack.append(line + os.linesep)
    write_data(host, output_data, is_xml=True)
    return output_data, "".join(nmap_warn_tracestack), "".join(nmap_error_tracestack)


def parse_xml_output(output: str, warnings: str, error: str) -> Dict[str, Any]:
    """Parse the XML data out of the file into a dict."""
    results = {}
    try:
        root = ElementTree.fromstring(output)
    except Exception:
        if len(error) != 0:
            raise lib.errors.NmapScannerError(error)
        else:
            raise lib.errors.NmapScannerError(output)
    
    # Safely get scan stats
    finished_elem = root.find('runstats/finished')
    hosts_elem = root.find('runstats/hosts')
    
    results['nmap_scan'] = {
        'full_command_line': root.get('args'),
        'scan_information': {},
        'scan_stats': {
            'time_string': finished_elem.get('timestr') if finished_elem is not None else '',
            'elapsed': finished_elem.get('elapsed') if finished_elem is not None else '',
            'hosts_up': hosts_elem.get('up') if hosts_elem is not None else '',
            'down_hosts': hosts_elem.get('down') if hosts_elem is not None else '',
            'total_hosts_scanned': hosts_elem.get('total') if hosts_elem is not None else ''
        }
    }
    if len(error) != 0:
        results['nmap_scan']['scan_information']['errors'] = error
    if len(warnings) != 0:
        results['nmap_scan']['scan_information']['warnings'] = warnings
    for info in root.findall('scaninfo'):
        results['nmap_scan']['scan_information'][info.get('protocol')] = {
            'method': info.get('type'),
            'services': info.get('services')
        }
    for attempted_host in root.findall('host'):
        host = None
        addresses = {}
        vendors = {}
        for address in attempted_host.findall("address"):
            address_type = address.get('addrtype')
            addresses[address_type] = address.get('addr')
            if address_type == "ipv4":
                host = addresses[address_type]
            elif address_type == "mac" and address.get('vendor') is not None:
                vendors[addresses[address_type]] = address.get('vendor')
        if host is None:
            host = attempted_host.find('address').get('addr')
        hostnames = []
        if len(attempted_host.findall('hostnames/hostname')) != 0:
            for current_hostnames in attempted_host.findall('hostnames/hostname'):
                hostnames.append({
                    'hostname': current_hostnames.get('name'),
                    'host_type': current_hostnames.get('type')
                })
        else:
            hostnames.append({
                'hostname': None,
                'host_type': None
            })

        results['nmap_scan'][host] = {}
        results['nmap_scan'][host]['hostnames'] = hostnames
        results['nmap_scan'][host]['addresses'] = addresses
        results['nmap_scan'][host]['vendors'] = vendors

        for status in attempted_host.findall('status'):
            results['nmap_scan'][host]['status'] = {
                    'state': status.get('state'),
                    'reason': status.get('reason')
            }
        for uptime in attempted_host.findall('uptime'):
            results['nmap_scan'][host]['uptime'] = {
                    'seconds': uptime.get('seconds'),
                    'lastboot': uptime.get('lastboot')
            }
        for discovered_port in attempted_host.findall('ports/port'):
            protocol = discovered_port.get('protocol')
            port_number = discovered_port.get('portid')
            port_state = discovered_port.find('state').get('state')
            port_reason = discovered_port.find('state').get('reason')

            # this is actually a thing!!
            name = discovered_config = discovered_version = extra_information = discovered_product = stuff = ""
            for discovered_name in discovered_port.findall('service'):
                name = discovered_name.get('name')
                if discovered_name.get('product'):
                    discovered_product = discovered_name.get('product')
                if discovered_name.get('version'):
                    discovered_version = discovered_name.get('version')
                if discovered_name.get('extrainfo'):
                    extra_information = discovered_name.get('extrainfo')
                if discovered_name.get('conf'):
                    discovered_config = discovered_name.get('conf')

                for other_stuff in discovered_name.findall('cpe'):
                    stuff = other_stuff.text
            if protocol not in results['nmap_scan'][host].keys():
                results['nmap_scan'][host][protocol] = list()
            results['nmap_scan'][host][protocol].append({
                    'port': port_number, 'state': port_state, 'reason': port_reason,
                    'name': name, 'product': discovered_product, 'version': discovered_version,
                    'extrainfo': extra_information, 'conf': discovered_config, 'cpe': stuff
                })

    return results
