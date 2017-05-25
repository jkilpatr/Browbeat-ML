import argparse
import sys
import lib.elastic_backend
import lib.perf_classify
import lib.perf_predict
import lib.data_summary
import lib.util
import pkg_resources


class MyParser(argparse.ArgumentParser):
    """Custom parser class."""

    def error(self, message):
        """Print help on argument parse error."""
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


def parse_args():
    """Parse input args and returns an args dict."""
    parser = MyParser(description='Data processing and analytics library \
                                   for OpenStack Browbeat perf data')

    parser.add_argument('-s', '--summary', dest="days", type=int, default=-1,
                        help='-s N summary of last N days of results')

    parser.add_argument('-v', '--osp-version', dest='version', type=str,
                        default=None,
                        help='-v 11-tripleo only returns hits for that \
                        OpenStack version, \
                        only supported by summary right now')

    parser.add_argument('-c', '--config', dest='config', type=str,
                        default=pkg_resources.resource_filename('bml',
                                                                "config.yml"),
                        help='-c <config file path> use custom config file')

    parser.add_argument('--classify', dest="classify", type=str, default=None,
                        help='--classify <Browbeat UUID> returns a \
                        classification for the UUID provided')

    parser.add_argument('--classify-test', dest="classify_test",
                        action="store_true",
                        help='dev mode for --classify \
                        just runs and evals model')

    parser.add_argument('--predict', dest="predict", action="store_true",
                        help='Starts an interactive workflow \
                        for the predict net')

    parser.add_argument('--predict-test', dest="predict_test",
                        action="store_true",
                        help='Runs training and evaluation \
                        for the predict net')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    config = lib.util.load_config(args.config)
    es_backend = lib.elastic_backend.Backend(config['elastic-host'],
                                             config['elastic-port'])
    # tests.perf_classify(config, es_backend)
    # tests.perf_predict(config, es_backend, "neutron.create_network")
    if args.days is not -1:
        lib.data_summary.time_summary(config,
                                      es_backend,
                                      str(args.days) + "d",
                                      args.version)
    elif args.classify is not None:
        lib.perf_classify.perf_classify(config, es_backend, uuid=args.classify)
    elif args.classify_test:
        lib.perf_classify.perf_classify(config, es_backend)
    elif args.predict:
        lib.perf_predict()
    elif args.predict_test:
        lib.perf_predict.perf_predict()
    else:
        args.error("No arguments defined!")


if __name__ == '__main__':
    sys.exit(main())
