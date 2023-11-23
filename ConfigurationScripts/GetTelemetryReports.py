# GetTelemetryReports.py Python script using Redfish API to export Metric Report Definitions to a CSV file named GetTelemetryReports.csv in the current directory
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
from urllib.parse import urlparse

warnings.filterwarnings("ignore")
#logging.getLogger().setLevel(logging.INFO)  # Change to logging.DEBUG for detailed logs
logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

parser = argparse.ArgumentParser(description="Python script using Redfish to export Metric Report Definitions to a CSV file named GetTelemetryReports.csv in the current directory")
parser.add_argument('--script-examples', action="store_true", help='Prints script examples')
parser.add_argument('-ip', help='iDRAC IP address, argument only required if configuring one iDRAC', required=False)
parser.add_argument('-u', help='iDRAC username, argument only required if configuring one iDRAC', required=False)
parser.add_argument('-p', help='iDRAC password, argument only required if configuring one iDRAC', required=False)
group = parser.add_mutually_exclusive_group()
group.add_argument('-r', help='Export metric reports only', action='store_true', required=False)
group.add_argument('-m', help='Export metric reports with metrics', action='store_true', required=False)

args = vars(parser.parse_args())

def print_examples():
    """
    Print program examples and exit
    """
    print(
        '\n\'GetTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -r, this example will export all metric reports for single iDRAC to GetTelemetryReports.csv\n'
        '\n\'GetTelemetryReports.py -ip 192.168.0.120 -u root -p calvin -m, this example will export all metric reports and metrics for single iDRAC to GetTelemetryReports.csv\n')

def get_reports(ip, user, pwd, export_reports, export_metrics):
    """ Checks the current status of telemetry and creates telemetry_attributes, a list of telemetry attributes
    """
    global telemetry_attributes
    output = []
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
        for report in telemetry_attributes:
            row = []
            report_name = urlparse(report).path.split('/')[-1]
            if export_reports:
                row.append(report_name)
                output.append(row)
            #logging.info(row)
            if export_metrics:
                url_detail = 'https://{}{}'.format(ip, report)
                response_detail = requests.get(url_detail, headers=headers, verify=False, auth=(user, pwd))
                if response_detail.status_code != 200:
                    logging.error("- FAIL, status code for reading attributes is not 200, code is: {}".format(response_detail.status_code))
                    sys.exit()
                try:
                    response_detail_json = json.loads(response_detail.text)
                    metrics = response_detail_json.get('Metrics', {})
                    for metric in metrics:
                        row_detail = []
                        row_detail.append(report_name)
                        row_detail.append(metric.get('MetricId'))
                        output.append(row_detail)
                        #logging.info(row)

                except Exception as e:
                    logging.error("- FAIL: detailed error message: {0}".format(e))
                    sys.exit()

        logging.info(output)
        with open('GetTelemetryReports.csv', mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerows(output)
            logging.info("- INFO, successfully exported GetTelemetryReports.csv")


    except Exception as e:
        logging.error("- FAIL: detailed error message: {0}".format(e))
        sys.exit()

if __name__ == "__main__":
    if args["script_examples"]:
        print_examples()
    elif args["ip"] and args["u"] and args["p"]:
        get_reports(args["ip"], args["u"], args["p"], args["r"], args["m"])
    else:
        logging.warning("- WARNING, missing or incorrect arguments passed in for executing script")

