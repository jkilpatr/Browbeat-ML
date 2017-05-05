# Browbeat-ML
Python scripts for Openstack performance machine learning.

What this project does is provide an easy way to stream Browbeat performance
results out of ElasticSearch and into a `browbeat_run` object, identified by
the Browbeat uuid. From there you can search for any number of `browbeat_test`
objects each of which represent a single action as indexed by Browbeat, a single
benchmark may have many.

The `browbeat_test` class parses the test data and provides a simple way to
retrieve test metadata such as CPU, kernel, machine type, raw test data, and
various other test, hardware, and software specific metadata.

From that point the challenge is feeding this data into TensorFlow and making
effective models. The `tests.py` file is pretty much a dumping ground for
various models and the utility functions required to make them work.

There are two major models provided right now, `perf_classify` and `perf_predict`

`perf_classify` is a manually classified test in which we attempt to train a network
to identify several potential classifications, at this point these are only pass
and fail, it's about 76% accurate with the current fairly small number of samples.

`perf_predict` on the other hand is an attempt at predicting the performance of
a single rally action on arbitrary hardware with an arbitrary number of nodes by
automatically training on all appropriate data in the ElasticSearch it's pointed
at. It's proven to be within 10% or so of the actual value for the dataset in
ElasticSearch but it's real ability to generalize remains difficult to determine.
