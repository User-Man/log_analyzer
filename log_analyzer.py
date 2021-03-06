#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import sys
import os
import re
import imp
import gzip
import json
import time
import logging
import argparse
import hashlib
from datetime import datetime


def get_command_options():
    description = "Analyze nginx logfiles and create report."
    parser = argparse.ArgumentParser(description=description)
    help_description = 'Config file name or config directory by default name "config.py"'
    parser.add_argument('--config', nargs=1, metavar='config_file', help=help_description)
    return parser.parse_args()


def load_config_from_args(config_from_args):
    default_filename = 'config.py'

    if os.path.isfile(config_from_args):
        pathname = config_from_args
    elif os.path.isdir(config_from_args):
        pathname = os.path.join(config_from_args, default_filename)
    else:
        logging.error("Config file not found: {}".format(config_from_args))
        sys.exit(0)
    try:
        module_cfg = imp.load_source('config', pathname)
        cfg = module_cfg.config
        return cfg
    except:
        logging.error("Can't use config file: {}".format(config_from_args))
        return {}


def get_config(args):
    config = {
        "REPORT_SIZE": 1000,
         "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
    "REPORT_TEMPLATE": "report.html",
        "REPORT_NAME": "report-{}.html",
    "REGEXP_FIND_DATE_FROM_FILE_NAME": "^nginx-access-ui.log-([0-9]{8})",
            "TS_FILE": "/tmp/log_nalyzer.ts",
    "LOG_OUTPUT_FILE": None,
         "LOG_FORMAT": '[%(asctime)s] %(levelname).1s %(message)s',
    "LOG_DATA_FORMAT": '%Y.%m.%d %H:%M:%S',
          "LOG_LEVEL": logging.INFO,
      "PARSER_REGEXP": "(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})([\s-]+).+"
                      + "(?P<date>\[[\/\w:\s+]+\])\s"
                      + "\"\w*\s*(?P<url>[\w\/\.\-?\&\%_=:]+).+"
                      + "\s(?P<request_time>[0-9\.]+)$",
      "PARSER_MAX_PERCENT_ERRORS": 75,
    }

    if hasattr(args, 'config') and args.config:
        config_from_file = load_config_from_args(args.config[0])
        if isinstance(config_from_file, dict):
            config = dict(config, **config_from_file)

    return config


def get_last_file(config):
    try:
        log_files = {}
        if os.path.isdir(config['LOG_DIR']):
            for file_in_dir in os.listdir(config['LOG_DIR']):
                result = re.search(config["REGEXP_FIND_DATE_FROM_FILE_NAME"], file_in_dir)
                if result:
                    datetime_object = datetime.strptime(result.group(1), '%Y%m%d')
                    log_files[datetime_object] = file_in_dir
        else:
            logging.error("Can't use log directory: {}".format(config['LOG_DIR']))

        if log_files:
            max_date_in_files = max(dt for dt in log_files.keys())
            config["REPORT_NAME"] = config["REPORT_NAME"].format(max_date_in_files.strftime("%Y.%m.%d"))
            return log_files[max_date_in_files]
        else:
            return None
    except:
        logging.exception("Can't get last log file")
        sys.exit(0)


def median(lst):
    quotient, remainder = divmod(len(lst), 2)
    if remainder:
        return sorted(lst)[quotient]
    return sum(sorted(lst)[quotient - 1:quotient + 1]) / 2.


def open_log_file(log_dir, last_log_file):
    log_file = os.path.join(log_dir, last_log_file)
    try:
        if log_file.endswith(".gz"):
            fd_log = gzip.open(log_file, 'rb')
        else:
            fd_log = open(log_file, 'r')
        return fd_log
    except:
        logging.exception("Open file error")
        sys.exit(0)


def check_percent_errors(count_line, count_line_parse_errors, parser_max_percent_errors):
    current_percent_errors = int(float(count_line_parse_errors) * 100 / float(count_line))
    if current_percent_errors > parser_max_percent_errors:
        error_str = "Reached maximum number of parser errors ({0} from {1}) it's more then {2}%"
        logging.error(error_str.format(count_line_parse_errors, count_line, parser_max_percent_errors))


def analize_log_file(fd_log, config):
    report_size = config['REPORT_SIZE']
    analize_result = {}
    count_all_reqest = 0
    count_all_request_time = 0
    count_line_parse_errors = 0
    ROUND_NUMBER = 3
    for log_line in fd_log:
        count_all_reqest += 1
        result = re.search(config['PARSER_REGEXP'], log_line)
        if result:
            url = result.group("url")
            key = hashlib.md5(url).hexdigest()
            request_time = float(result.group("request_time"))
            count_all_request_time += request_time
            if analize_result.get(key):
                analize_result[key]['time_sum'] += request_time
                analize_result[key]['time_list'].append(request_time)
            else:
                analize_result[key] = {'url': url,
                                  'time_sum': request_time,
                                 'time_list': [request_time]}
        else:
            count_line_parse_errors += 1

    check_percent_errors(count_all_reqest, count_line_parse_errors, config['PARSER_MAX_PERCENT_ERRORS'])

    for key in analize_result.keys():
        if analize_result[key]['time_sum'] < report_size:
            del analize_result[key]
            continue
        analize_result[key]['count'] = len(analize_result[key]['time_list'])
        analize_result[key]['count_perc'] = round((float(analize_result[key]['count'])) * 100 / float(count_all_reqest), ROUND_NUMBER)
        analize_result[key]['time_perc'] = round((float(analize_result[key]['time_sum'])) * 100 / float(count_all_request_time), ROUND_NUMBER)
        analize_result[key]['time_avg'] = round(analize_result[key]['time_sum'] / analize_result[key]['count'], ROUND_NUMBER)
        analize_result[key]['time_max'] = round(max(analize_result[key]['time_list']), ROUND_NUMBER)
        analize_result[key]['time_med'] = round(median(analize_result[key]['time_list']), ROUND_NUMBER)
        analize_result[key]['time_sum'] = round(analize_result[key]['time_sum'], ROUND_NUMBER)
        del analize_result[key]['time_list']

    return analize_result.values()


def save_report_to_file(result, config):
    try:
        if config.get('REPORT_DIR') and not os.path.isdir(config['REPORT_DIR']):
            os.mkdir(config['REPORT_DIR'])

        report_template = config['REPORT_TEMPLATE']
        report_result = os.path.join(config['REPORT_DIR'], config['REPORT_NAME'])
        with open(report_template, "rt") as fin:
            with open(report_result, "wt") as fout:
                for line in fin:
                    fout.write(line.replace('$table_json', json.dumps(result)))

        return report_result
    except:
        logging.exception("Save report error")
        os.remove(report_result)
        sys.exit(0)


def is_report_was_created(config):
    try:
        for file_name in os.listdir(config['REPORT_DIR']):
            if file_name == config['REPORT_NAME']:
                return True
        return False
    except:
        logging.exception("Can't read report directory")
        sys.exit(0)

def save_timestamp_to_file(ts_file):
    with open(ts_file, 'w') as fd_ts_file:
        fd_ts_file.write(str(time.time()))


def main():
    all_args = get_command_options()
    config = get_config(all_args)
    try:
        logging.basicConfig(filename = config["LOG_OUTPUT_FILE"],
                              format = config["LOG_FORMAT"],
                             datefmt = config["LOG_DATA_FORMAT"],
                               level = config['LOG_LEVEL'])

        last_log_file = get_last_file(config)
        if last_log_file:
            if is_report_was_created(config):
                logging.info("The report for {0} is ready.".format(last_log_file))
            else:
                fd_log = open_log_file(config['LOG_DIR'], last_log_file)
                logging.info("Start analysis log {}".format(last_log_file))
                result = analize_log_file(fd_log, config)
                report_file = save_report_to_file(result, config)
                logging.info("End analysis and save report in {}".format(report_file))
        else:
            logging.info("No file to analyze")

        save_timestamp_to_file(config['TS_FILE'])
    except:
        logging.exception("We have a problem")
        sys.exit(0)


if __name__ == "__main__":
    main()
