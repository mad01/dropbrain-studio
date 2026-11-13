---
title: "python flask rest api auth option storing in mongoDB 3.0 running on docker"
date: 2015-03-28
slug: python-flask-mongodb-restapi-auth
description: "I have been looking on a way to auth rest api endpoints that needs to have auth. I will be using Python with flask, flask-restful, yaml, pymongo and passlib. passlib will be used…"
tags: python, rest, docker, mongodb
---
I have been looking on a way to auth rest api endpoints that needs to have auth. I will be using Python with flask, flask-restful, yaml, pymongo and passlib. passlib will be used to salt the password that will be stored in mondoDB. A note here is that i will be using mongoDB 3.0 which means that you have to install the un released pymongo 3.0. here is the packets and links you need. 

```bash
pip install https://github.com/mongodb/mongo-python-driver/archive/3.0b1.tar.gz
pip install PyYaml
pip install flask-restful
pip install flask
pip install passlib
```


i am installing MongoDB 3.0 using docker. And starting the db. i should end up with one running mondoDB 3.0 named `mongo`. i can check that with `docker ps`
```bash
docker pull mongo
docker run --name mongo -d -p 27017:27017 mongo:3.0
```


Starting with the mongo module to add a user to a collection in mongo. The `createOrUpdateUser` function creates a checks if the user exists in mongo. If that is the case it will update it and add a new time to the updates so i have stored the created date and last update with a timestamp. If the user is not in the db collection one will be created. This function will return the ObjectId of the user that later will be used to get the user. 

```python
def createOrUpdateUser(username, saltedKey='', host='', database=''):
    client = MongoClient(host)
    db = client[database]
    checkUser = [doc for doc in db.user.find({"username": username})]
    if checkUser:
        userData = checkUser[0]
        db.user.replace_one(
            {
                "username": username,
                "saltedKey": userData.get('saltedKey'),
            }, {
                "username": username,
                "saltedKey": saltedKey,
                "created": userData.get('created'),
                "updated": datetime.datetime.utcnow()
            }
        )
        userObjectId = [doc for doc in db.user.find({"username": username})][0].get('_id')
        return str(userObjectId)

    else:
        data = {
            "saltedKey": saltedKey,
            "created": datetime.datetime.utcnow(),
            "updated": datetime.datetime.utcnow(),
            "username": username,
        }
        userObjectId = db.user.insert_one(data).inserted_id
        return str(userObjectId)
```


Next is the `getUser` from mongo using the ObjectId. it will return the full json document stored in mongo.
```python
def getUser(userObjectId, host='', database=''):
    """get user json ducument from mongo"""
    client = MongoClient(host)
    db = client[database]
    return [doc for doc in db.user.find({"_id": ObjectId(userObjectId)})][0]
```



To create the use and salt the password i am using `passlib` i'm giving a username, a password, and the mongo host, I'm then using the `createOrUpdateUser` to add the user in to a collection called endpoints. the function returns a dict that contains the ObjectId if the new of updated user.
```python
def addUser(username, password='', mongo=''):
    passwordSalted = apps.custom_app_context.encrypt(password)
    userObjectId = createOrUpdateUser(
        username,
        saltedKey=passwordSalted,
        host=mongo,
        database='endpoints'
    )
    return {"userObjectId": userObjectId}
```


To validate that the password is current I'm using `getUser` to get the salted password from mongo in the collection endpoints where i stored that user data. the function is then using a validation option of the salt function that takes the salted password and the password to check if it's correct.  if the verification passes a boolean True is returned else you get a False. 
```python
def validateUserKey(userObjectId, password='', mongo=''):
    salt = getUser(
        userObjectId,
        host=mongo,
        database="endpoints"
    )
    valid = apps.custom_app_context.verify(
        password,
        salt.get('saltedKey')
    )
    return valid
```



Lest look on the REST api. I am using the [flask](http://flask.pocoo.org/) and [flask restful](https://flask-restful.readthedocs.org/en/0.3.2/) packets to create the REST api. The `protected` class __init__ have two keys `oid` and `key` that should be in the http payload. in the get function i am using "self.reqparse.parse_args(strict=True)" that means that the oid and key key/value have to be in the get payload or the request will be rejected. i am then checking that the key for the oid is valid using `validateCheck` if it's valid you get the {"key": "valid"} else you get http 401. i am then adding that class to the "api.add_resource(protected, '/api/protected')" which adds a REST endpoint `/api/protected`valid

```python
class protected(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('oid')
        self.reqparse.add_argument('key')
        self.mongo = conf.get('mongoDB').get('host')
        super(protected, self).__init__()

    def get(self):
        args = self.reqparse.parse_args(strict=True)
        validateCheck = salt.validateUserKey(
            userObjectId=args.oid,
            password=args.key,
            mongo=self.mongo
        )
        if validateCheck:
            return {"key": "valid"}
        else:
            abort(401)

api.add_resource(protected, '/api/protected')

if __name__ == '__main__':
    app.run(debug=True)
```


Looking on a test for this to checks that a user is valid if the correct key/oid is passed and then if the wrong key/right oid is passed it can look like this. The assumption here is that the REST api is started and running on localhost and that the docker mongo:3.0 is running on 192.168.59.103. In the `setUpClass` i am declaring all variables to self that will be used in test. i am running the tests with [nosetests](https://nose.readthedocs.org/en/latest/). The first test `testAccessValidKey` passed the correct key/oid and should get back http 200. the second test should fail the validation, it passes a invalid key and a valid oid, the api should return http 401.
```python
def checkAccess(oid, password='', host=''):
    data = {"oid": oid, "key": password}
    return get('http://' + host + ':5000/api/protected', data=data)

class TestRestGetCalls(unittest.TestCase):

    @classmethod       
    def setUpClass(self):
        confFile = file('tests/test_salt.yaml', 'r')
        conf = yaml.load(confFile)
        self.mongo = conf.get('mongoDB').get('host')
        self.api = conf.get('api').get('host')
        self.key = "foo"
        self.user = "bar"
        userDoc = salt.addUser(
            self.user,
            password=self.key,
            mongo=self.mongo
        )
        self.oid = userDoc.get("userObjectId")

    @classmethod       
    def tearDownClass(self):
        pass

    def testAccessValidKey(self):
        httpGet = checkAccess(
            self.oid,
            password=self.key,
            host=self.api
        )
        self.assertEqual(200, httpGet.status_code)

    def testAccessInValidKey(self):
        httpGet = checkAccess(
            self.oid,
            password="foobar",
            host=self.api
        )
        self.assertEqual(401, httpGet.status_code)
```


the source for all the code can be found on my github here [Link](https://github.com/mad01/boilerplates/tree/master/python)
