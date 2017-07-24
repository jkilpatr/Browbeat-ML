import numpy
import cPickle
import pkg_resources


def classify_value(config, value, test_name, osp_version, concurrency, times):
    predictors = numpy.array([0, 1, 2, 3, 4])
    dict_osp = config['osp_version_dic']
    dict_test = config['test_name_dic']
    osp_version_dic \
        = reduce(lambda r, d: r.update(d) or r, dict_osp, {})  # noqa
    test_name_dic \
        = reduce(lambda r, d: r.update(d) or r, dict_test, {})  # noqa
    predictors[0] = osp_version_dic[str(osp_version)]
    predictors[1] = test_name_dic[str(test_name)]
    predictors[2] = float(value)
    predictors[3] = int(concurrency)
    predictors[4] = int(times)
    predictors.reshape(1, -1)
    clf_name = str(config['classifier'][0])
    clf_dir = "lib/classifier/" + clf_name + ".pkl"
    with open(pkg_resources.resource_filename('bml', clf_dir), 'rb') as cfid:
        clf = cPickle.load(cfid)
    output_prediction = clf.predict([predictors])
    return output_prediction
