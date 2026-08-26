# SQLite concurrency test fix

The lifecycle race tests were using an in-memory SQLite URL with multiple
connections. That creates separate databases per connection, causing worker
threads to observe `no such table: jobs`.

The tests now use SQLAlchemy `StaticPool` with `check_same_thread=False` so all
threads share the same in-memory database. This changes only the test
environment; production store semantics remain under test.
