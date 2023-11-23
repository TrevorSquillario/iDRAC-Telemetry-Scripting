# DeleteTelemetryReports.py Python script using Redfish API to delete Metric Report Definitions
# 
#
#
# _author_ = Trevor Squillario <Trevor_Squillario@Dell.com>
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

warnings.filterwarnings("ignore")
#logging.getLogger().setLevel(logging.INFO)  # Change to logging.DEBUG for detailed logs
logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

parser = argparse.ArgumentParser(description="Python script using Redfish to delete Metric Report Definitions")
parser.add_argument('--script-examples', action="store_true", help='Prints script examples')
parser.add_argument('-ip', help='iDRAC IP address, argument only required if configuring one iDRAC', required=False)
parser.add_argument('-u', help='iDRAC username, argument only required if configuring one iDRAC', required=False)
parser.add_argument('-p', help='iDRAC password, argument only required if configuring one iDRAC', required=False)
parser.add_argument('-f', help='Pass in csv file name. If file is not located in same directory as script, pass in the full directory path with file name. NOTE: Make sure to use iDRACs.csv file from the repo which has the correct format.', required=False)
group = parser.add_mutually_exclusive_group()
group.add_argument('-a', help='Delete all Metric Reports', action='store_true', required=False)
group.add_argument('-n', help='Metric report name to delete. *Supports a comma delimted list', required=False)

args = vars(parser.parse_args())

def print_examples():
    """
    Print program examples and exit
    """
    print(
        '\n\'DeleteTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -a, this example will delete all metric reports for a single iDRAC\n'
        '\n\'DeleteTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -n "PowerMetrics", this example will delete the PowerMetrics metric report for a single iDRAC\n')

def delete_all_reports(ip, user, pwd):
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

        for report in telemetry_attributes:
            delete_url = 'https://{}{}'.format(ip, report)
            logging.info("- INFO, deleting metric report {}".format(report))
            del_response = requests.delete(delete_url, headers=headers, verify=False, auth=(user, pwd))
            if del_response.status_code != 200:
                logging.error("- FAIL, status code for {} is not 200, code is: {}".format(report, del_response.status_code))

    except Exception as e:
        logging.error("- FAIL: detailed error message: {0}".format(e))
        sys.exit()

def delete_reports(ip, user, pwd, reports):
    """ Checks the current status of telemetry and creates telemetry_attributes, a list of telemetry attributes
    """
    reports_list = map(str.strip, reports.split(','))
    for report in reports_list:
        delete_url = 'https://{}/redfish/v1/TelemetryService/MetricReportDefinitions/{}'.format(ip, report)
        headers = {'content-type': 'application/json'}
        logging.info("- INFO, deleting metric report {}".format(report))
        del_response = requests.delete(delete_url, headers=headers, verify=False, auth=(user, pwd))
        if del_response.status_code != 200:
            logging.error("- FAIL, status code for {} is not 200, code is: {}".format(report, del_response.status_code))

if __name__ == "__main__":
    if args["script_examples"]:
        print_examples()
    elif args["ip"] and args["u"] and args["p"] and args["a"]:
        delete_all_reports(args["ip"], args["u"], args["p"])
    elif args["ip"] and args["u"] and args["p"] and args["n"]:
        delete_reports(args["ip"], args["u"], args["p"], args["n"])
    elif args["f"] and (args["a"] or args["n"]):
        try:
            open_csv_file = open(args["f"], encoding='UTF8')
        except:
            logging.error("\n- ERROR, unable to locate file %s" % args["f"])
            sys.exit(0)
        csv_reader = csv.reader(open_csv_file)
        next(csv_reader)
        for line in csv_reader:
            logging.info("\n- Delete Telemetry report definition for iDRAC %s -\n" % (line[0]))
            if args["a"]:
                delete_all_reports(line[0], line[1], line[2])
            elif args["n"]:
                delete_reports(line[0], line[1], line[2], args["n"])
    else:
        logging.warning("- WARNING, missing or incorrect arguments passed in for executing script")

