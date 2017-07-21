import numpy as np
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
import cPickle
import pkg_resources
from util import date_valid
from util import connect_crdb
from util import test_ignore_check


def train_classifier(data, target, name_clf):
    size_data = len(data)
    data_train = np.array(data[:int(1 * size_data)])
    target_train = np.array(target[:int(1 * size_data)])
    if name_clf == "dtree":
        clf = DecisionTreeClassifier()
        clf.fit(data_train, target_train)
    elif name_clf == "svc":
        clf = SVC()
        clf.fit(data_train, target_train)
    elif name_clf == "gnb":
        clf = GaussianNB()
        clf.fit(data_train, target_train)
    else:
        print("Invalid classifier name encountered \
        in the config file \n ")
        exit(1)
    pickle_classifier(clf, name_clf)


def pickle_classifier(clf, name_clf):
    clf_file = "lib/classifier/" + str(name_clf) + ".pkl"
    fid = open(pkg_resources.resource_filename('bml', clf_file), 'wb')
    print("Updated '{}' pickle".format(name_clf))
    cPickle.dump(clf, fid)
    fid.close()


def update(config, days):
    osp_version_dic = reduce(lambda r, d: r.update(d) or r, config['osp_version_dic'], {})  # noqa
    test_name_dic = reduce(lambda r, d: r.update(d) or r, config['test_name_dic'], {})  # noqa
    table_name = config['table_name'][0]
    data = []
    target = []
    conn = connect_crdb(config)
    cur = conn.cursor()
    cur.execute("select test, osp_version, avg_runtime, \
                grade, timestamp, \
                concurrency, times from {}".format(table_name))
    rows = cur.fetchall()
    for row in rows:
        if date_valid(str(row[4]), days):
            if test_ignore_check(row[0], config):
                temp = [0, 1, 2, 3, 4]
                temp[1] = test_name_dic[str(row[0])]
                temp[0] = osp_version_dic[str(row[1])]
                temp[2] = row[2]
                temp[3] = row[5]
                temp[4] = row[6]
                data.append(temp)
                output_grade = row[3]
                target.append(int(output_grade))
    conn.close()
    clf_list = config['classifier_lists']
    for name_clf in clf_list:
        train_classifier(data, target, name_clf)
