---
title: "simple prometheus exporter in python"
date: 2016-08-28
slug: docker-prometheus-exporter-python
description: "writing a simple prometheus exporter to collect metrics from a external system that needs monitoring. I will use the python official prometheusclient package for python and falcon…"
tags: prometheus, exporter, python
---
writing a simple prometheus exporter to collect metrics from a external system that needs monitoring. I will use the python official `prometheus_client` package for python and `falcon` to serve the exporter.

notise the following example is written with the assumtion that you are collection metrics from some other systems when multiple services is written in the same framwork and have a generic set of metrics. That is why there is a service label included. Normaly you should get the service name, from your service discovery.

to just view the code jump to he source link in the end of the page. 

project structure
```bash
├── Dockerfile
├── Makefile
├── prom-exporter
├── prom_exporter
│   ├── __init__.py
│   ├── app.py
│   ├── handler.py
│   └── prom.py
├── requirements.txt
├── setup.cfg
├── setup.py
```


`app.py` starting the app with the python `click` framework to write a simple cli tool that takes some input to start the server
```python
import click
from prom_exporter.handler import falcon_app

@click.group(help='')
def cli():
    pass

@click.command()
@click.option('-s', '--service', required=True, type=str)
@click.option('-u', '--url', required=True, type=str)
@click.option('-p', '--port', required=True, type=int)
@click.option('-e', '--exclude', multiple=True)
def start(service, url, port, exclude):
    falcon_app(url, service, port=port, exclude=list(exclude))

cli.add_command(start)

if __name__ == '__main__':
    cli()
```


`handler.py` the handler holds the metric class that will be serving the metrics to prometheus when it's collecting metrics. The on\_get function uses the `generate_latest` function from the prometheus package to generate the body of the request. the `generate_latest` takes a class with a collect function that yields `Metrics` objects that holds a list of samples that is used to generate the body. Every `Metrics` object can hold more then just one metric if you have multiple metrics that is from the same metric like. requets-p99 requets-p95 requets-p90 and so on you shoud not export this metrics using the current name. It's a more optimal to do this by using the labels and by translating them to a generic metric name. If metrics is exported in a format like `response{latency="p99"}` `response{latency="p95"}` . You can new do a promQL like this `response{latency="p99"}` to access this metrics.


```python
import falcon

from wsgiref import simple_server
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from prometheus_client.exposition import generate_latest

from prom_exporter.prom import Collector

class metricHandler:
    def __init__(self, url='', service='', exclude=list):
        self._service = service
        self._url = url
        self._exclude = exclude

    def on_get(self, req, resp):
        resp.set_header('Content-Type', CONTENT_TYPE_LATEST)
        registry = Collector(
            self._url,
            self._service,
            exclude=self._exclude
            )
        collected_metric = generate_latest(registry)
        resp.body = collected_metric

def falcon_app(url, service, port=9999, addr='0.0.0.0', exclude=list):
    print('starting server http://127.0.0.1:{}/metrics'.format(port))
    api = falcon.API()
    api.add_route(
        '/metrics',
        metricHandler(url=url, service=service, exclude=exclude)
    )

    httpd = simple_server.make_server(addr, port, api)
    httpd.serve_forever()
```


`prom.py` A basic collector class with a collect function that gets called to generate the last metrics. it's important to also allow for the option to exclude metrics when you are implementing a exporter to not add unwanted data. The `_get_metrics` function can just be replaced with a request to the system that you like to export metrics from to get prometheus native format. A suggestion here is to enrich the metrics like building a dict with the metrics you like to collect. By doing this you can select only a subset of the metrics the system exposes and you can enrich the metrics by adding extra labels and translate the metrics to a generic name used by all services to make the promQL's more reusable over multiple service types.

```python
import time
import random
from prometheus_client import Metric

class Collector(object):
    def __init__(self, endpoint, service, exclude=list):
        self._endpoint = endpoint
        self._service = service
        self._labels = {}
        self._set_labels()
        self._exclude = exclude

    def _set_labels(self):
        self._labels.update({'service': self._service})

    def filter_exclude(self, metrics):
        return {k: v for k, v in metrics.items() if k not in self._exclude}

    def _get_metrics(self):
        metrics = {
            'requests': 100,
            'requests_status_2xx': 90,
            'requests_status_4xx': 3,
            'requests_status_5xx': 7,
            'uptime_sec': 123,
            'exclude_me': 1234,
            }

        if self._exclude:
            metrics = self.filter_exclude(metrics)

        time.sleep(random.uniform(0.1, 0.4))
        return metrics

    def collect(self):
        metrics = self._get_metrics()

        if metrics:
            for k, v in metrics.items():
                metric = Metric(k, k, 'counter')
                labels = {}
                labels.update(self._labels)
                metric.add_sample(k, value=v, labels=labels)

                if metric.samples:
                    yield metric
                else:
                    pass
```

metric output when running the exporter 
```bash
# HELP requests requests
# TYPE requests counter
requests{service="foo"} 100.0
# HELP requests_status_2xx requests_status_2xx
# TYPE requests_status_2xx counter
requests_status_2xx{service="foo"} 90.0
# HELP uptime_sec uptime_sec
# TYPE uptime_sec counter
uptime_sec{service="foo"} 123.0
# HELP exclude_me exclude_me
# TYPE exclude_me counter
exclude_me{service="foo"} 1234.0
# HELP requests_status_4xx requests_status_4xx
# TYPE requests_status_4xx counter
requests_status_4xx{service="foo"} 3.0
# HELP requests_status_5xx requests_status_5xx
# TYPE requests_status_5xx counter
requests_status_5xx{service="foo"} 7.0
```


prometheus config to collect from the exporter
```yaml
scrape_configs:
  - job_name: 'prom_exporter'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:9999']
```

edited: `2016-09-24`, 
Python exporter source [Source](https://github.com/mad01/examples/tree/master/prometheus/python)
