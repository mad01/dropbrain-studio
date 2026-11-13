---
title: "docker compose with selenium"
date: 2015-04-24
slug: docker-compose-selenium-hub
description: "Running a local setup with selenium hub with Firefox and Google Chrome nodes using docker-compose . Using docker-compose makes the setup even more convenient the using the docker…"
tags: docker, selenium
---
Running a local setup with selenium hub with `Firefox` and `Google Chrome` nodes using [docker-compose](https://github.com/docker/compose) .  Using `docker-compose` makes the setup even more convenient the using the `docker --link` commands. Starting and stoping the setup is just easy. Scaling up and down the number of Chrome and Firefox nodes is just a command to.

`docker-compose` builds a setup based on a compose file that is a yaml file. Creating the setup file for a selenium hub with two nodes can look like this.

Selenium hub, the web ui is exposed on port 4444 on the docker server. If you are using a local setup in `OS X` you can get the ip with `boot2docker ip | pbcopy` . 
```yaml
hub:
image: selenium/hub
ports:
- "4444:4444"
```

Firefox selenium node head less
```yaml
firefox:
image: selenium/node-firefox
links:
- hub
expose:
- "5555"
```

Google Chrome selenium node head less
```yaml
chrome:
image: selenium/node-chrome
links:
- hub
expose:
- "5555"
```

to run the setup save it to a file named `docker-compose.yml` . Stand in the same folder as the compose file. run the following command to start the setup and send it to the background. If you like to run it in foreground remove the `-d` flag. If you don't have the images `docker-compose` will pull the images like normal with docker
```bash
jone@doe:~$ docker-compose up -d
Recreating selenium_hub_1...
Recreating selenium_firefox_1...
Recreating selenium_chrome_1...
```

Now lets look and see if the docker images are running
```bash
jone@doe:~$  docker-compose ps
Name Command State Ports
----------------------------------------------------------
selenium_chrome_1 /opt/bin/entry_point.sh Up 5555/tcp
selenium_firefox_1 /opt/bin/entry_point.sh Up 5555/tcp
selenium_hub_1 /opt/bin/entry_point.sh Up 0.0.0.0:4444->4444/tcp
```

Lest assume that you like to scale the number of Firefox and Chrome nodes to two of each. You can use the `scale` command with `docker-compose` . The name of the nodes are used to scale up and down the number of docker instances that are running. 
```bash
jone@doe:~$ docker-compose scale firefox=2 chrome=2
Creating selenium_firefox_2...
Starting selenium_firefox_2...
Creating selenium_chrome_2...
Starting selenium_chrome_2...
```

Now lets stop the setup. using the `stop` command with `docker-compose`
```bash
jone@doe:~$ docker-compose stop
Stopping selenium_chrome_2...
Stopping selenium_chrome_1...
Stopping selenium_firefox_2...
Stopping selenium_firefox_1...
Stopping selenium_hub_1...
```

link to docker-compose file [source](https://github.com/mad01/boilerplates/blob/master/docker/compose/selenium/docker-compose.yml)
