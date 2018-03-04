#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest
import log_analyzer as la
from datetime import datetime


class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Log_analyzer_test_with_full_config(unittest.TestCase):
    def setUp(self):
        self.default_config = la.get_config(Namespace())

    def test_get_config_default(self):
        self.assertEqual(la.get_config(Namespace()), self.default_config)

    def test_get_config_where_full_config_from_file(self):
        config_file_name = "config-file.py"
        full_config = la.get_config(Namespace())
        full_config['REPORT_SIZE'] = 1000
        full_config['REPORT_DIR'] = './report_other_dir'

        with open(config_file_name, 'w') as fd:
            fd.write("config = " + str(full_config))

        self.assertEqual(la.get_config(Namespace(config=[config_file_name])), full_config)
        os.remove(config_file_name)
        os.remove(config_file_name+'c')

    def test_get_config_where_half_config_from_file(self):
        config_file_name = "half_config-file.py"
        half_config = {'LOG_OUTPUT_FILE': "./log.log",
                           'REPORT_SIZE': 2000}

        self.default_config['LOG_OUTPUT_FILE'] = "./log.log"
        self.default_config['REPORT_SIZE'] = 2000

        with open(config_file_name, 'w') as fd:
            fd.write("config = " + str(half_config))

        self.assertEqual(la.get_config(Namespace(config=[config_file_name])), self.default_config)
        os.remove(config_file_name)
        os.remove(config_file_name+'c')

    def test_get_config_where_half_config_in_dir(self):
        dir_name = "./TEMP_DIR/"
        half_config = {'REPORT_SIZE': 4000,
                   'REPORT_TEMPLATE': 'report-template.html'}

        self.default_config['REPORT_SIZE'] = 4000
        self.default_config['REPORT_TEMPLATE'] = 'report-template.html'

        os.mkdir(dir_name)
        with open(dir_name + "config.py", 'w') as fd:
            fd.write("config = " + str(half_config))

        self.assertEqual(la.get_config(Namespace(config=[dir_name])), self.default_config)

        os.remove(dir_name + "config.py")
        os.remove(dir_name + "config.pyc")
        os.rmdir(dir_name)

    def test_get_config_where_config_not_found(self):
        with self.assertRaises(SystemExit):
            la.get_config(Namespace(config=['./config-file1.py']))

    def test_get_config_where_config_is_empty(self):
        config_file_name = "config-empty.py"
        with open(config_file_name, 'w') as fd:
            fd.write("")

        self.assertEqual(la.get_config(Namespace(config=[config_file_name])), self.default_config)
        os.remove(config_file_name)
        os.remove(config_file_name+'c')

    def test_get_config_where_config_is_broken(self):
        config_file_name = "config-broken.py"
        with open(config_file_name, 'w') as fd:
            fd.write("config = something broken")

        self.assertEqual(la.get_config(Namespace(config=[config_file_name])), self.default_config)

        os.remove(config_file_name)

    def test_get_last_file_without_logs(self):
        dir_name = "./TEMP_DIR/"
        os.mkdir(dir_name)

        self.default_config['LOG_DIR'] = dir_name

        self.assertEqual(la.get_last_file(self.default_config), None)
        os.rmdir(dir_name)

    def test_get_last_file_find_last_date(self):
        dir_name = "./TEMP_DIR/"
        os.mkdir(dir_name)

        self.default_config['LOG_DIR'] = dir_name

        open(dir_name + "nginx-access-ui.log-20170630", 'w')
        open(dir_name + "nginx-access-ui.log-20180210", 'w')
        open(dir_name + "nginx-access-ui.log-{}".format(datetime.now().strftime("%Y%m%d")), 'w')

        self.assertEqual(la.get_last_file(self.default_config), "nginx-access-ui.log-{}".format(datetime.now().strftime("%Y%m%d")))

        os.remove(dir_name + "nginx-access-ui.log-20170630")
        os.remove(dir_name + "nginx-access-ui.log-20180210")
        os.remove(dir_name + "nginx-access-ui.log-{}".format(datetime.now().strftime("%Y%m%d")))
        os.rmdir(dir_name)

    def test_analize_log_file(self):
        something_like_file = [
        """1.138.198.128 -  - [30/Jun/2017:03:28:23 +0300] "GET / HTTP/1.1" 200 9134 "-" "-" "-" "-" "-" 0.01""",
        """1.138.198.128 -  - [30/Jun/2017:03:28:23 +0300] "GET / HTTP/1.1" 200 9134 "-" "-" "-" "-" "-" 0.054""",
        """1.138.198.128 -  - [30/Jun/2017:03:28:23 +0300] "GET / HTTP/1.1" 200 9134 "-" "-" "-" "-" "-" 0.1"""]

        self.default_config['REPORT_SIZE'] = 0

        expected_result = [{'count': 3,
                       'count_perc': 100.0,
                         'time_avg': 0.055,
                         'time_max': 0.1,
                         'time_med': 0.054,
                        'time_perc': 100.0,
                         'time_sum': 0.164,
                              'url': '/'}]

        self.assertSequenceEqual(la.analize_log_file(something_like_file, self.default_config), expected_result)


if __name__ == '__main__':
    unittest.main()
