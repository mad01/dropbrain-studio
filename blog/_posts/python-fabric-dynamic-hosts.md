---
title: "Fabric dynamic hosts tasks"
date: 2016-06-30
slug: python-fabric-dynamic-hosts
description: "Using fabric with dynamic hosts. In the fabric documentation most of it is using examples and is assuming that you you have a static set of hosts. That is no longer the case when…"
tags: python, fabric, fab, dynamic, hosts
---
Using fabric with dynamic hosts. In the fabric documentation most of it is using examples and is assuming that you you have a static set of hosts. That is no longer the case when we are working with cloud and a dynamic amout of hosts. The way the fabric want's you to run tasks is to use the `fabric.api.env` function to set the hosts you have. If you now want to do this on the fly you have one option a function called `execute` avalible in `fabric.api` that takes a key `hosts` this key will be used to tell fabric to run on this hosts as if you had set `env.hosts` .

The way i have structured my fab tasks is by having one `task` func and one _func doing the actual task that is called with execute. The `task` is just a placeholder to selecting the hosts i like to run on. In reality the `get_hosts` will return a list of hosts from google cloud platform. If you like to use key/value arguments on a function the `execute` function will pass those to you function like in the example


project structur
```bash
├── requirements.txt
└── fabfile.py
```

example fabfile
```python
#!/usr/bin/env python2
from fabric.api import task, parallel, run, execute

def get_hosts():
    return ['10.0.0.1', '10.0.0.2']

@parallel
def _tail(foo='', bar=''):
    try:
        run('sudo tail -f /var/log/*.log')
    except KeyboardInterrupt:
        pass

@task
def tail():
    hosts = get_hosts()
    execute(_tail, hosts=hosts, foo='foo', bar='bar')
```


The example can be found here. [Source](https://github.com/mad01/examples/tree/master/fabric)
