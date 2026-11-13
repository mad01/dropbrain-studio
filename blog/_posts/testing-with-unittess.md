---
title: "why do we do need unit tests"
date: 2016-06-05
slug: testing-with-unittess
description: "You might be thinking well unit tests is kind of a obvious thing that you have when you are writhing code. If you do you are wrong. Not all developers want and can write unit…"
tags: testing, unittest
---
You might be thinking well unit tests is kind of a obvious thing that you have when you are
writhing code. If you do you are wrong. Not all developers want and can write unit tests.
This is kind of interesting for me.

Short about me. I am a software developer in test, i have been spending years on designing,
test automation and writing tooling to help other developers to to be more efficient in
finding issues in the code they deliver. And strategies around quality and testing. Mostly
on the backend and infrastructure area. Also being part of the design phase of a service
to help point out risky areas.

There is a few questions i see that some comes up when unit tests are not obvious. They are

1. I don't know how to
2. It slows me down, i.e I don't have time
3. It's working so we don't need it

Point 1
Well then there is a few options that can help. Fist list do some pair programming, spend
some time with the team or the developer that need some help getting started. And implement
a few features together. During this it's easier to help steering the design of the features
in a direction that makes them easy to test, like splitting code it small functions that are
then more approachable since they should just do one thing. Mock all the thing that you are
dependent on doing calls to external services.

Point 2
From the start writhing unit tests might be time consuming yes. But when you have everything
in place and have tests for most of the code base. You will find that it saves you time, since 
you will get broken tests fast if you broke something during development not in production. That
is just embarrassing that is not something we what. There is also one big benefit that might not
be to obvious. This is that it will be easier to grow the team that owns the service. It's a pain
in the ass to get to a project as a new developer when there it no tests. The last thing to add 
here is that. Adding tests will help you split the code in to smaller functions that is easier
to add tests for and control. Which improves maintainability of the code in a team.

Point 3
Stating that it it's working it kind of a dumb ting to say. This is really hard to prove. 
Event if the service looks like it's working you can't be entirely sure since you don't have
tests for it there might be obvious bugs that you will have to spend a lot of time to
trouble shot before you can fix it. Having tests is the key to having a stable service. And
to be able to deploy to production with sanity some left.

Unit testing is not that hard you just have to design and think `how do i test this function`
during development. This might mean splitting a function in to few smaller functions.
Awesome this means that you have succeeded and made the code more testable and maintainable


![test all the things](/blog/images/test-all-the-things.png)
