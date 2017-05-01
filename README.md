# Browbeat-ML
Python scripts for Openstack performance machine learning.

Right now data is pulled out of Elasticsearch formatted, then put through
a off the shell combined Linear/DNN model. The resulting accuracy is about
76% but considering that I can vastly reduce the amount of training/neurons
and get the same result my conclusion is that I need to get more training
vectors into the model.

Now the `tf_train` function makes a lost of unsightly assumptions, mainly in handling
tests with a different number of runs, it just takes whatever `times` value it sees
first and enforces it on the rest. Not ideal but workable for now.

Also more flexibility to process errors needs to be on the roadmap. Right now errors
are silently filtered at every level, we need to avoid that.
