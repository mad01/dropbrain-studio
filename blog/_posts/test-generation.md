---
title: "dynamic test generation"
date: 2015-03-15
slug: test-generation
description: "I what to show a api template i did to generate api post tests with a random varible lenght hex value as the payload in a http post request. In this case i am using python, in…"
tags: testing, python
---
I what to show a api template i did to generate api post tests with a random varible lenght hex value as the payload in a http post request. In this case i am using python, in compination with [nose](https://nose.readthedocs.org), to run my tests. Note you can run this without nose but you will get all prints from the support libs. Nose will supress the prints if the test passes. To change to varible number of tests that you can generate you just change the `random_data` input integer. The purpose of this is to be able to check that a REST api can take the random input length of the hex payload. in the testmap you gets a dict that contains a random, int, float, hex, password. 

```python
class TestGenClass(unittest.TestCase):
    pass

def dynamic_gen(test_assert):
    def dynamic_test_method(self):
        shared = {
            "api": "post",
            "host": "httpbin.org"
        }
        result_code, http_data = http_post(
            shared.get('host'),
            api=shared.get('api'),
            payload={"hex": test_assert}
        )
        data = json.loads(http_data)
        self.assertEqual(int(result_code), 200)
        self.assertEqual(
            unicode(test_assert),
            json.loads(data.get('data')).get('hex')
        )

    return dynamic_test_method

testmap = random_data(10)
for name, parms in testmap.iteritems():
    data = dynamic_gen(parms["hex"])
    data.__name__ = "test_{0}".format(name)
    data.__doc__ = "test_{0}".format(name)
    setattr(TestGenClass, data.__name__, data)
    del data
```


link to [source](https://github.com/mad01/boilerplates/blob/master/python/test_api_post.py).
