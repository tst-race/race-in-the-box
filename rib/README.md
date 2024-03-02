# RiB

## Tests

To run all the tests run this command:

```bash
make -C ../ test
```

If you wish to filter for a specific test case you can do so with a command like this:

```bash
# Run _just_ the test `test_RaceTest_run_deployment_test` from the file `rib/utils/tests/test_testing_utils.py`.
(cd .. && python3 setup.py test  --addopts rib/utils/tests/test_testing_utils.py::test_RaceTest_run_deployment_test)
```
