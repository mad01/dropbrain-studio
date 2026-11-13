---
title: "pitfalls when writing commandline tools"
date: 2015-03-21
slug: command-line-tools-pitfalls
description: "Common pitfalls when using template files/support files in the working dir of the script, is easy to miss when you are writing command line tools. In this case using python. Some…"
tags: command, line, tools
---
Common pitfalls when using template files/support files in the working dir of the script, is easy to miss when you are writing command line tools. In this case using `python`. Some of the more annoying mistakes is when you have template files stores and referred to in a script, you assume that the person that will use you script stands in the folder were the script is. lest assume that we are using a file template.html in a folder named foobar. of corse this will not work if you are running the script from somewhere else. I normally stand in the same folder as the script when i am developing a tool. When you then stand in some other folder everything will fail since you are not giving the absolute path to the template files. 

there is a few option here and it's to either only work if you standing in the correct folder, fix the paths to work anyway, or last a install script that creates the env you need and have a static path that can be used in any system.

you have a few options here were to store scripts and template/files that you need to read in linux. 
```bash
/usr/local/sbin # custom script for root
/usr/local/bin 	# custom script for all users
/usr/local/share # store support files like templates for scripts recommended to use a subfolder
/usr/share # store support files like templates for scripts recommended to use a subfolder
```


i will assume that you want a custom script with a support template file. the script should be for all users. that means the script should be stored in `/usr/local/bin` and i will store the support template in a subfolder in `/usr/share`. this is how i can look to accomplish that. first i remove the old files and then write the new version.
```bash
#!/bin/bash
sudo rm -rf /usr/local/bin/foo.py /usr/local/bin/bar.py
sudo rm -rf /usr/share/foobar

sudo mkdir /usr/share/foobar
sudo cp -r template /usr/share/foobar
sudo cp foo.py bar.py /usr/local/bin
```

one other option is if you don't want to install the script but still like to call the script from anywhere and still have template files working. you can use `os.path.dirname(os.path.abspath(__name__))` in the python script to give the working dir of the script, and then using that to add to the path of template files. this is how it can look 

```python
scriptDir = os.path.dirname(os.path.abspath(__name__))

def readFile(inFile):
	"""read file in subfolder of working dir of script"""
	inFile = open(scriptDir + '/foobar/template.html',
		'r').readlines()
	return inFile

def writeFile(outFile, data):
	"""write file in working dir of script"""
	writeFile = open(scriptDir + '/' + outFile, 'w')
	for lines in data:
		writeFile.write(lines)

	writeFile.close()
```
