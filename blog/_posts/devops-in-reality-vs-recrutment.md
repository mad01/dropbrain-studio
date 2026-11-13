---
title: "different sides of devops in recrutment and engineering"
date: 2016-12-20
slug: devops-in-reality-vs-recrutment
description: "The question is what is devops? How do you recruit a devops engineer. The short answer is you don't. a devops engineer does not exist. The thing about recruiting a so called…"
tags: devops, software-engineering, platform-engineering
---
The question is what is devops? How do you recruit a devops engineer. The short answer is you don't. a devops engineer does not exist. The thing about recruiting a so called devops engineer is all a bit undefined and often miss understood and is often used by head hunters and recruiters to find software engineers/ops engineers.

If we look at it a bit in short first, what is devops! devops is a way of working in a engineering organisation. The way of working generally means a few thing. You start by moving the organisation from a `itil` or `waterfall` to a more `agile` way of working. What this means is that you strive to have a culture that allows people freedom under responsibility, short development cycles, allowing quick adoption and changes, to move fast. The one big part here is `trust` in the engineers.

As i see it devops have two main groups, engineering culture, operations culture. knowing that lets add a third group infrastructure engineering culture. If we break down the three the groups a bit to explains what devops/none devops means for the different groups, and what the extra groups brings. 


### engineering culture

#### none devops
the engineering team develops and delivers builds for approval to QA/Test teams to get the features ready for production and a handover to ops is done when it's done. The engineers gets frustrated due to the slow time to production, and they need to have a lot more balls in the air at the same time. since time to deliver is long and they still need to add more features.

#### devops
the engineering team, develops and delivers directly to production, takes responsibility to uphold the quality level of a service, and that if it's lower they will prior to fix it. This lowers the wall between engineering and operations that is traditionally there. Since the engineers are the experts they should also run the services. the engineers also don't need to many balls in the air.


## opperations culture

#### none devops 
the ops team have a handover process, that gets a tested and proven build delivered hopefully some documentation, on how to run, and take care of that application. the ops team often tries to minimise the amount of deploys. Since the time to get a fix is long, a deploy is risky and can break production. So the result is that you get a long time from development to delivery. a wall is formed between engineering and operations and there is often disagreement about deployments to production and it tends to be some friction between the two groups. Engineers break things and ops gets to fix it.

#### devops
the ops team have a agreement with engineering that deployments by engineers can be done when they feel like they are done. The agreement here is that you need to have some level of quality checking done. This quality needs to be checked that is's true when running in production to. Like if you agree that 99% of all requests served by the service needs to be correct, if that is lower. engineering will have to fix it. The worry about having a broken service is here moved to engineering and not operations.


## infrastructure engineering culture

#### devops
This extra groups is actually not devops. However this is what most people actually is looking for when they need a devops engineer. What devops mostly is mistaken for is automation and tooling around infrastructure, deployment, monitoring when in reality devops is a engineering culture and a agile way of delivering features to production.

To actually be able to have a devops organisation you will need software engineers that acts as operations engineers to create the needed tools and automation around the platform that services is delivered on. To provide the engineering teams with some sane defaults, a robust platform and the needed tools around it to do deployments, to allow failing services.

Instead of babying a service to keep it running like ops usually do in a traditional organisation. You need to build and run services with the assumption, that things will break all the time. It's not the engineers job to keep the services running it's the platform. if a service fails a new should just start in it's place. As long as the service upholds the agreed upon availability everything is good.


## Conclusion
What devops actually is. Is not a role it's a way of structuring a agile engineering organisation. And a group of software engineers working with tools and infrastructure to provide a platform to run services on, for the engineering team building the product. 

There is a un answered question. That is do you actually need a operations team in a agile/devops engineering organisation. I would say no, if you run everything in the cloud. You might want some good sysadmin to take care of the day to day IT that is not related to running and delivering the product/platform.
