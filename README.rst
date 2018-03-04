Log Analyzer
=======

Запуск скрипта:
----
  python log_analyzer.py # конфигурация по умолчанию
  python log_analyzer.py --config config_file.py # использование конфигурации из файла config_file.py
  python log_analyzer.py --config ./CONFIG_DIR/  # использование конфигурации из директории ./CONFIG_DIR/, с именем config.py по умолчанию
  python log_analyzer.py --config ./CONFIG_DIR/config.py  # использование конфигурации config.py из директории ./CONFIG_DIR/

Конфигурация по умолчанию
----
  config = {
      "REPORT_SIZE": 1000,             # В отчет попадает REPORT_SIZE URL'ов с наибольшим суммарным временем обработки (time_sum)
       "REPORT_DIR": "./reports",      # Расположение отчетов
          "LOG_DIR": "./log",          # Расположение логов на обработку
  "REPORT_TEMPLATE": "report.html",    # Шаблон отчета
      "REPORT_NAME": "report-{}.html", # Шаблон имени, результирующего отчета
  "REGEXP_FIND_DATE_FROM_FILE_NAME": "^nginx-access-ui.log-([0-9]{8})", # regexp поиска временной метки
          "TS_FILE": "/tmp/log_nalyzer.ts", # timestamp файл
  "LOG_OUTPUT_FILE": None,             # Вывод logging, None по умолчанию stdout, можно указать файл лога.
       "LOG_FORMAT": '[%(asctime)s] %(levelname).1s %(message)s', # Формат лога logging
  "LOG_DATA_FORMAT": '%Y.%m.%d %H:%M:%S', # Формат времени logging
        "LOG_LEVEL": logging.INFO,     # Уровень logging
    "PARSER_REGEXP": "(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})([\s-]+).+"
                    + "(?P<date>\[[\/\w:\s+]+\])\s"
                    + "\"\w*\s*(?P<url>[\w\/\.\-?\&\%_=:]+).+"
                    + "\s(?P<request_time>[0-9\.]+)$", # regexp парсинга лога
    "PARSER_MAX_PERCENT_ERRORS": 75, # Допустимый процент ошибок (пропуска строк)
  }

Файл конфигурации может содержать частичную информацию, т.е хранить изменения только необходимых параметров.
Например: config_file.py
  config = { "LOG_DIR": "./log" }

Внесет изменения только касательно LOG_DIR, все остальные параметры останутся по умолчанию.

Тестирование
-----

python test_log_analyzer.py -v
