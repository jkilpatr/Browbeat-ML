# Browbeat-ML
Python Library for Openstack performance machine learning.

Browbeat-ML or bml is a small project to apply machine learning to OpenStack
performance data specifically data gathered in the Openstack Browbeat metadata
format. Right now bml only supports Rally based tests, although other backends
are easy enough to integrate.

To install run

	pip install git+https://github.com/aakarshg/Browbeat-ML

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

Storing import data needed to update the classifier, `--update-db True` helps you 
to upload needed features like avg_runtime, time_stamp, test name, osp-version and
grade which are primarily used by the default classifier. It is set to False by default

	bml --update-db <True/False>

In order to not thrash elastic search for getting simpler summary, we provide
with short-summary which gets data from cockroachdb and displays the results.
it takes the argument no. of days, just like summary. Only difference being 
that instead of querying from elastic search, it uses cockroachdb. 


	bml --short-summary <n>
	
You can update the classifier using the cockroach db short summary by giving it `n`
days as argument and it'll use data from the last `n` days to train and update
all the classifiers listed in config.yaml and update the pickle files. 

	bml --update-clf <n>
	
You can test the classifiers using the cockroach db short summary by giving it `n`
days as argument and it'll use data from the last `n` days to train classifiers
and display the metrics so that you've a better idea of what's happening. 

	bml --test-clf <n>
	

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

### Classifier

The classifier has been trained using the data extracted for runs on in house clouds.
It won't give perfect results out-of-box, you'll need to retrain it using data.

Note: It uses just 4 features: test name, osp_version, average_runtime and grade.

Default grading scale used in the classifier was 1-5, with 1 meaning bad, with 3
meaning it is in expected range.

We're using svc kernel rbf, and can be made to use gaussianNB, dtree by updating the 
classifier in the config.yaml. It takes 'svc', 'gnb' or 'dtree'. 
