import numpy as np
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import confusion_matrix
from random import shuffle
from util import date_valid
from util import connect_crdb
from util import test_ignore_check
from sklearn.metrics import matthews_corrcoef


def train_classifier(data, target, name_clf):
    if name_clf == "dtree":
        clf = DecisionTreeClassifier()
        clf.fit(data, target)
    elif name_clf == "svc":
        clf = SVC()
        clf.fit(data, target)
    elif name_clf == "gnb":
        clf = GaussianNB()
        clf.fit(data, target)
    else:
        print("Invalid classifier name encountered \
        in the config file \n ")
        exit(1)
    return clf


def test(config, days):
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
    shuffle(rows)
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
    size_data = len(data)
    data_train = np.array(data[:int(0.8 * size_data)])
    data_test = np.array(data[int(0.8 * size_data):])
    target_train = np.array(target[:int(0.8 * size_data)])
    target_test = np.array(target[int(0.8 * size_data):])
    conn.close()
    clf_list = config['classifier_lists']
    for name_clf in clf_list:
        trained_clf = train_classifier(data_train, target_train, name_clf)
        print("The results for the '{}' classifier are as follows ".format(str(name_clf)))  # noqa
        display_results(trained_clf, data_test, target_test)


def display_results(clf, data_test, target_test):
    accuracy = clf.score(data_test, target_test)
    all_predictions = clf.predict(data_test)
    print "Accuracy is", accuracy  # noqa
    print "confusion matrix:", confusion_matrix(target_test, all_predictions)
    print "MCC is", matthews_corrcoef(target_test, all_predictions), "\n"
