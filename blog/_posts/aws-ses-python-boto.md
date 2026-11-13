---
title: "html email with aws ses and boto"
date: 2015-04-11
slug: aws-ses-python-boto
description: "Sending html email with amazon ses simple email service using the python module boto."
tags: amazon, aws, ses, python, boto
---
Sending html email with amazon ses `simple email service` using the python module [boto](https://github.com/boto/boto). 

to be able to start using the `ses` service you need to verify two emails. The first you what is the address that you like to use to send from. The second is the one you like to receive it in. To be able to verify that addresses you need a valid address since a validation email will be sent to the address. after that is done, you can start yo use the mail addresses. At this stage you will only have a sandbox version of `ses`, you will only be able to send/receive from the verified addressed. at a later state you can request production that will open to send email to any one. When in the sandbox state of `ses` you will only have a limit of 200 emails every 24h. 


the input variables that will be need to send a html email, is a html file, a subject, a address that you send from, a list of addresses to send to. at this state only the list of the verified addresses will work, and last the aws region.  
```python
def ses_send_html_mail(
	htmlFile="foobar.html",
	subject="example",
	send_from="from@example.com",
	send_to=["to@example.com"],
	aws_region="us-west-2"):
```


Now lets assing the needed variables to the `MIMEMultipart`, subject, to and from. 
```python
	message = MIMEMultipart()
	message["Subject"] = subject
	message["From"] = send_from
	message["To"] = send_to
```



The html file needs to be passed as a string and to do that we can open that file with .read() . The MIMEText takes a string as the first input variable, add a optional second string that identifies the type of the first string, here you set html. There is a list of [unsupported attachment types](http://docs.aws.amazon.com/ses/latest/DeveloperGuide/mime-types.html) that can't be used everything else is supported. 
```python
	html = open(htmlFile, 'r').read()
	attachment = MIMEText(html, 'html')
	message.attach(attachment)
```


Now the last step to connect to amazon aws `ses` and send the email.
```python
	aws_connect = boto.ses.connect_to_region(aws_region)
	send_mail = aws_connect.send_raw_email(
		message.string(),
		source=message['From'],
		destinations=message['To']
	)
	return send_mail
```


source to example [link](https://github.com/mad01/boilerplates/blob/master/python/aws.py)
