# EnableOrDisableTelemetryReports.py Python script using Redfish API to Enable or Disable All Telemetry Reports
# with Default/Existing settings.
#
#
# _author_ = Trevor Squillario <Trevor_Squillario@Dell.com>
# _author_ = Sankunny Jayaprasad <Sankunny.Jayaprasad@Dell.com>
# _author_ = Texas Roemer <Texas_Roemer@Dell.com>
# _version_ = 2.0
#
# Copyright (c) 2022, Dell, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

import argparse
import csv
import json
import logging
import sys
import warnings
import requests
from requests.exceptions import HTTPError

warnings.filterwarnings("ignore")
#logging.getLogger().setLevel(logging.INFO)  # Change to logging.DEBUG for detailed logs
logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

parser = argparse.ArgumentParser(description="Python script using Redfish to Enable/Disable iDRAC Telemetry and all supported metric reports for one iDRAC using script arguments or multiple iDRACs using CSV file.")
parser.add_argument('--script-examples', action="store_true", help='Prints script examples')
parser.add_argument('-ip', help='iDRAC IP address, argument only required if configuring one iDRAC', required=False)
parser.add_argument('-u', help='iDRAC username, argument only required if configuring one iDRAC', required=False)
parser.add_argument('-p', help='iDRAC password, argument only required if configuring one iDRAC', required=False)
parser.add_argument('-s', help='Pass in the report status to be set. Possible values are Enabled/Disabled', default='Enabled', choices=['Enabled', 'Disabled'], required=False)
parser.add_argument('-ss', help='Pass in the Telemetry Service state to be set. Possible values are Enabled/Disabled', default='Enabled', choices=['Enabled', 'Disabled'], required=False)
parser.add_argument('-f', help='Pass in csv file name. If file is not located in same directory as script, pass in the full directory path with file name. NOTE: Make sure to use iDRACs.csv file from the repo which has the correct format.', required=False)
group = parser.add_mutually_exclusive_group()
group.add_argument('-a', help='Enable/Disable all Metric Reports', action='store_true', required=False)
group.add_argument('-n', help='Metric report name to delete. *Supports a comma delimted list', required=False)

args = vars(parser.parse_args())

def print_examples():
    """
    Print program examples and exit
    """
    print(
        '\n\'EnableOrDisableTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -s Enabled, this example will enable Telemetry and all metric reports for single iDRAC\n'
        '\n\'EnableOrDisableTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -s Disabled, this example will disable Telemetry and all metric reports for single iDRAC\n'
        '\n\'EnableOrDisableTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -s Enabled -n "PowerMetrics", this example will enable Telemetry and the PowerMetrics metric reports for single iDRAC\n'
        '\n\'EnableOrDisableTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -ss Enabled -s Disabled -n "PowerMetrics", this example will enable Telemetry and disable the PowerMetrics metric reports for single iDRAC\n'
        '\n\'EnableOrDisableTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -ss Enabled -s Enabled -n "PowerMetrics, SystemUsage", this example will enable Telemetry and enable the PowerMetrics and SystemUsage metric reports for single iDRAC\n'
        '\n\'EnableOrDisableTelemetryReports.py -s Enabled -f C:\Python39\iDRACs.csv, this example will enable Telemetry and all metric reports for all iDRACs in CSV file.\n'
        '\n\'EnableOrDisableTelemetryReports.py -s Disabled -f C:\Python39\iDRACs.csv, this example will disable Telemetry and all metric reports for all iDRACs in CSV file.\n')

def set_service_state(ip, user, pwd, service_state):
    # Enable and disable global telemetry service
    url = 'https://{}/redfish/v1/TelemetryService'.format(ip)
    headers = {'content-type': 'application/json'}
    response = requests.patch(url, data=json.dumps({"ServiceEnabled": service_state=='Enabled'}), headers=headers,
                              verify=False, auth=(user, pwd))
    if response.status_code != 200:
        logging.error("- FAIL, status code for reading attributes is not 200, code is: {}".format(response.status_code))
        logging.debug(str(response))
        sys.exit() 

    logging.info("- INFO, successfully '{}' iDRAC Telemetry".format(service_state))

def get_attributes(ip, user, pwd):
    """ Checks the current status of telemetry and creates telemetry_attributes, a list of telemetry attributes
    """
    global telemetry_attributes
    # Use redfish API instead of AR
    url = 'https://{}/redfish/v1/TelemetryService/MetricReportDefinitions'.format(ip)
    headers = {'content-type': 'application/json'}
    response = requests.get(url, headers=headers, verify=False, auth=(user, pwd))
    if response.status_code != 200:
        logging.error("- FAIL, status code for reading attributes is not 200, code is: {}".format(response.status_code))
        sys.exit()
    try:
        logging.info("- INFO, successfully pulled configuration attributes")
        configurations_dict = json.loads(response.text)
        attributes = configurations_dict.get('Members', {})
        telemetry_attributes = [map['@odata.id'] for map in attributes]
        logging.debug(telemetry_attributes)
    except Exception as e:
        logging.error("- FAIL: detailed error message: {0}".format(e))
        sys.exit()


def set_attributes_all(ip, user, pwd, service_state):
    """Uses the RedFish API to set the telemetry enabled attribute to user defined status.

    Args:
        telemetry_attributes (list): A list containing all telemetry attributes attributes 
    """

    # Enable Telemetry Service before enabling metric reports
    if service_state == 'Enabled':
        set_service_state(ip, user, pwd, service_state)

    status_to_set = args["s"]
    headers = {'content-type': 'application/json'}
    # Go to each metric report definition and enable or disable based on input
    for uri in telemetry_attributes:
        url = 'https://{}{}'.format(ip,uri)
        response = requests.patch(url, data=json.dumps({"MetricReportDefinitionEnabled": status_to_set=='Enabled'}), headers=headers,
                              verify=False, auth=(user, pwd))
    
    # Disable Telemetry Service after disabling metric reports
    if service_state == 'Disabled':
        set_service_state(ip, user, pwd, service_state)

    logging.info("- INFO, successfully '{}' iDRAC Telemetry and all supported metric reports".format(status_to_set))

def set_attributes(ip, user, pwd, reports, service_state):
    """Uses the RedFish API to set the telemetry enabled attribute to user defined status.
    """
    status_to_set = args["s"]
    headers = {'content-type': 'application/json'}

    # Enable Telemetry Service before enabling metric reports
    if service_state == 'Enabled':
        set_service_state(ip, user, pwd, service_state)

    reports_list = map(str.strip, reports.split(','))
    for report in reports_list:
        url = 'https://{}/redfish/v1/TelemetryService/MetricReportDefinitions/{}'.format(ip, report)
        response = requests.patch(url, data=json.dumps({"MetricReportDefinitionEnabled": status_to_set=='Enabled'}), headers=headers,
                    verify=False, auth=(user, pwd))
        if response.status_code != 200:
            logging.error("- FAIL, status code for is not 200, code is: {}".format(response.status_code))
            logging.error(response.text)
        else:
            logging.info("- INFO, successfully '{}' metric reports {}".format(status_to_set, report))
    
    # Disable Telemetry Service after disabling metric reports
    if service_state == 'Disabled':
        set_service_state(ip, user, pwd, service_state)

if __name__ == "__main__":
    if args["script_examples"]:
        print_examples()
    elif args["ip"] and args["u"] and args["p"] and args["s"] and args["a"]:
        get_attributes(args["ip"], args["u"], args["p"])
        set_attributes_all(args["ip"], args["u"], args["p"], args["ss"])
    elif args["ip"] and args["u"] and args["p"] and args["s"] and args["n"]:
        set_attributes(args["ip"], args["u"], args["p"], args["n"], args["ss"])
    elif args["s"] and args["f"] and (args["a"] or args["n"]):
        try:
            open_csv_file = open(args["f"], encoding='UTF8')
        except:
            logging.error("\n- ERROR, unable to locate file %s" % args["f"])
            sys.exit(0)
        csv_reader = csv.reader(open_csv_file)
        next(csv_reader)
        for line in csv_reader:
            logging.info("\n- %s Telemetry attributes for iDRAC %s -\n" % (args["s"], line[0]))
            if args["a"]:
                get_attributes(line[0], line[1], line[2])
                set_attributes_all(line[0], line[1], line[2], args["ss"])
            elif args["n"]:
                set_attributes(line[0], line[1], line[2], args["n"], args["ss"])
    else:
        logging.warning("- WARNING, missing or incorrect arguments passed in for executing script")
