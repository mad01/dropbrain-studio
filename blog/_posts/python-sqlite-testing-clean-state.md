---
title: "sqlite3 in memory db for testing db functions in python"
date: 2015-06-06
slug: python-sqlite-testing-clean-state
description: "designing a app to be as testable as posible. When writing a application that you like to, write unit tests the best options it to always on everything written for a application…"
tags: testing, python, sqlite
---
designing a app to be as testable as posible. When writing a application that you like to, write unit tests the best options it to always on everything written for a application to not be dependent on that the application is running. Since if we can import a function and muck or just test the isolated function. One example on this is a database function, and a database. In this example i will use sqlite3 as a example. sqlite have a option to start the db in memory. This is something is very useful since you like to have a clean state of the database for every test. 

Continuing with a example. In the test setup function a in memory sqlite db is created and data is imported that is needed to test some database functions. On teardown the db is closed and on the next test its recreated to have every test start in a clean state and not be dependent the order of a test. 
```python
def setUp(self):
    self.inactive = ["b", "c", "d", "e"]
    self.db = sqlite3.connect(':memory:')

    cursor = self.db.cursor()
    cursor.execute(
        "CREATE TABLE inactive(id INTEGER PRIMARY KEY,word TEXT)"
        )
    self.db.commit()
    for i in self.inactive:
        sql.db_insert_row_inactive(
            self.db,
            word=i
        )

def tearDown(self):
    """close the db in memory to start next test in a clean state"""
    self.db.close()
```

Looking on two example tests that is then importing a db function to add and remove rows in the inactive table. between the tests the db is recreated which makes the test start from a known state which makes it's easier to recreate and control the what is tested.
```python
def test_db_insert_row_inactive(self):
    test_word = "bar"
    sql.db_insert_row_inactive(self.db, word=test_word)
    dbGet = sql.db_get_word_in_inactive(test_word, self.db)
    self.assertEqual(dbGet.get("word"), test_word)

def test_db_remove_row_inactive_by_word(self):
    sql.db_remove_word_inactive("b", self.db)
    dbGet = sql.db_get_word_in_inactive("b", self.db)
    self.assertIsNone(dbGet)
```

The full application that is used as a example can be found here. [Source](https://github.com/mad01/url-shortener)
