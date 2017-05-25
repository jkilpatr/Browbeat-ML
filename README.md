# Browbeat-ML
Python Library for Openstack performance machine learning.

Browbeat-ML or bml is a small project to apply machine learning to OpenStack
performance data specifically data gathered in the Openstack Browbeat metadata
format. Right now we only support Rally based tests, although other backends
are easy enough to integrate.

To install run

	pip install git+https://github.com/jkilpatr/Browbeat-ML

I suggest using a venv as the requirements for this project are sizeable and you
might not want them in your native python environment.

## Usage

You can either interact with the utilities through the provided command line
options or import the libraries provided by this package to use in your own
scripts.

### Provided Commands

First off the config file format, if you're inside RedHat the default config
file will work out of the box. If you want to use this with your own ElasticSearch
there's some setup to do. Take a look at the default config in `bml/config.yml`
the fields are fairly self explanatory. To pass your own at runtime do the following.

	bml -c <path to config> <other commands>

Once bml is setup there are several functions to use. `-s` will print a summary
of every test run up to `n` days in the past. This is useful for getting an
overview of data as it comes in.

	bml -s <n>
	bml --summary <n>

The two existing machine learning models are perf classify and perf predict.
Perf classify is an attempt at automatically flagging problem builds by training
a combined Linear/DNN model to separate a provided Browbeat UUID into 'pass' and
'needs attention' builds. Right now it's accuracy varies between 55% and 70%
depending on how the randomized split of training data and evaluation data goes
which means I don't have a good distribution of examples for training data.

	bml --classify <browbeat UUID>

This will train the model and classify a UUID, don't trust it right now. As I said
before this model needs more training data before it's anywhere near ready.

	bml --classify-test

This is used to test model changes and evaluate the model, it trains and then
evaluates the model.

Perf predict is even more experimental than perf classify, it's an attempt
at a model that feeds in lots of Browbeat metadata and test results and then
attempts to predict the performance of a given rally action on arbitrary hardware
for arbitrary concurrency, right now there's no wizard to guide you through
actually using this model and only the testing code is written.

	bml --predict_test

Don't run the above if you don't have awhile, instead of relying on explicit
training examples this model willl train itself on all available Browbeat data
for that rally action in whatever ElasticSearch instance you point it at. This
can take upwards of an hour to process all the data and train. Or many many hours
if your not using a GPU.


### Using BML as a python library

If you're just looking for a way to easily manipulate performance test data in
ElasticSearch bml's internal classes are abstracted enough to use as a library
easily. The following will run through all tests in a UUID And print the raw
results. Metadata is also parsed for you and is made easily available as class
objects. Please see `bml/lib/browbeat_test.py` for the full ever expanding list.

	from bml.lib.elastic_backend import Backend
	from bml.lib.browbeat_run import browbeat_run

	elastic = Backend("elk.browbeatproject.org", "9200")
	test_run = browbeat_run(elastic, "68c82031-96ef-4cfa-bf53-1aea21aab565")
	for test in test_run.get_tests():
	   print(test.name)
	   print(test.raw)

