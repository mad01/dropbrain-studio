---
title: "backup of linux vps using gsutil"
date: 2015-08-30
slug: backup-linux-gsutil
description: "Backing up linux servers to google clound storage with gsutil using the storage option nearline. What is needed to do this is a google cloud accound. Start by creating a new…"
tags: backup, google, gsutil
---
Backing up linux servers to google clound storage with gsutil using the storage option nearline. What is needed to do this is a google cloud accound. Start by creating a new project for backup. After that use that Project ID to configure gsutil in the next step.

start by configuring gsutil.
```bash
$ gsutil config
```

Create a nearline bucket on google clound storage. The mb flag means create bucket. the -l flag means location options is ASIA, EU, US. For more options take a look in the [gsutil mb doc](https://cloud.google.com/storage/docs/gsutil/commands/mb)
```bash
$ gsutil mb -l EU -c nearline gs://<bucket>
```

Set up the backup to run ones every day by placing this script in /etc/cron.daily/. You can use the monthly weekly daily or hourly like this. The -x flag is all files that like you to be excluded from the backup and the -r flag is the src directory that you like to backup.
```bash
#!/bin/bash
gsutil -qm rsync -x '.<exclude-file>|<exclude-file>' -r /<src-directory>  gs://<bucket>
```
