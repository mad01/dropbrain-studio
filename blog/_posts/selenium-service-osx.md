---
title: "selenium as a service in osx"
date: 2015-08-15
slug: selenium-service-osx
description: "Setting up selenium server as a service in os x that starts on boot. What is needed is a plist service file to start and take stdout and stderr and log the output. I will be using…"
tags: testing, selenium, jenkins, osx
---
Setting up selenium server as a service in os x that starts on boot. What is needed is a plist service file to start and take stdout and stderr and log the output.  I will be using homebrew for install of the selenium server. in this example i have used a vagrant image of Yosemite you can find it here [vagrant image](http://files.dryga.com/boxes/osx-yosemite-0.2.1.box). 

A NOTE about the OS X Licensing. 
Apple's EULA states that you can install your copy on your actual Apple-hardware, plus up to two VMs running on your Apple-hardware. So using this box on another hardware is may be illigal and you should do it on your own risk. 


Start by installing the selenium standalone server using brew
```bash
$ brew install selenium-server-standalone
```


install java7 using brew cask
```bash
$ brew tap caskroom/versions
$ brew cask install java7
```


create a plist file for the service. This is what is needed if you like to start selenium-standalone with port 4444 and logging the stdout to `/var/log/selenium/selenium-output.log` and stderr to `/var/log/selenium/selenium-error.log` . save it as selenium.plist
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>Label</key>
        <string>selenium</string>
        <key>RunAtLoad</key>
        <true/>
        <key>ProgramArguments</key>
        <array>
                <string>/usr/local/bin/selenium-server</string>
                <string>-port</string>
                <string>4444</string>
        </array>
        <key>ServiceDescription</key>
        <string>Selenium Server</string>
        <key>StandardErrorPath</key>
        <string>/var/log/selenium/selenium-error.log</string>
        <key>StandardOutPath</key>
        <string>/var/log/selenium/selenium-output.log</string>
</dict>
</plist>
```


create the log folder using sudo since root will run the service
```bash
$ sudo mkdir -p /var/log/selenium/
```


copy the selenium.plist to `/Library/LaunchDaemons` since we like it to run as a demon by the root user on boot. 
```bash
$ sudo cp selenium.plist /Library/LaunchDaemons
```


load the service in to system using `launchctl`
```bash
$ sudo launchctl bootstrap system /Library/LaunchDaemons/selenium.plist
```


bash script to install google chrome
```bash
#!/bin/bash
curl -L -O "https://dl.google.com/chrome/mac/stable/GGRO/googlechrome.dmg"
hdiutil mount -nobrowse googlechrome.dmg
cp -R "/Volumes/Google Chrome/Google Chrome.app" /Applications
hdiutil unmount "/Volumes/Google Chrome"
rm googlechrome.dmg
```


install chromedriver
```bash
$ brew install chromedriver
```


To make it possible to start running selenium tests on the server you need the user logged with a active workspace. To get this working after reboot with no manual login you do the following. Open `System Preferences` > `Security & Privacy` >`Click the lock to make changes` > uncheck `Disable automatic login` .


Source [selenium.plist](https://github.com/mad01/boilerplates/blob/master/osx/selenium.plist) [chrome-install.sh](https://github.com/mad01/boilerplates/blob/master/osx/chrome-install.sh)
