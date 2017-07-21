import argparse
import sys
import lib.elastic_backend
import lib.data_summary
import lib.util
import pkg_resources
import lib.crdb_summary
import lib.update_classifiers
import lib.test_classifiers


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

    parser.add_argument('--summary-uuid', dest="summary_uuid", type=str,
                        default=None,
                        help='--summary-uuid UUID summary of a specific uuid')

    parser.add_argument('--short-summary', dest="short_days", type=int,
                        default=-1,
                        help='--short-summary N gives \
                        summary of last N days of results but uses cockroach \
                        db so only provides with basic summary')

    parser.add_argument('-u', '--update-db', dest='update', type=bool,
                        default=False,
                        help='-u True pushes data to cockroach db')

    parser.add_argument('--update-clf', dest="clf_days", type=int,
                        default=-1,
                        help='--update-clf 60 will update all classifiers \
                        listed in config file under classifier_lists \
                        using data from last 60 days')

    parser.add_argument('--test-clf', dest="test_days", type=int,
                        default=-1,
                        help='--test-clf 60 will train all classifiers \
                        listed in config file under classifier_lists \
                        using data from last 60 days and then test it \
                        and display metrics')

    parser.add_argument('-v', '--osp-version', dest='version', type=str,
                        default=None,
                        help='-v 11-tripleo only returns hits for that \
                        OpenStack version, \
                        only supported by summary right now')

    parser.add_argument('-c', '--config', dest='config', type=str,
                        default=pkg_resources.resource_filename('bml',
                                                                "config.yml"),
                        help='-c <config file path> use custom config file')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    config = lib.util.load_config(args.config)
    es_backend = lib.elastic_backend.Backend(config['elastic-host'],
                                             config['elastic-port'])
    if args.days is not -1:
        lib.data_summary.time_summary(config,
                                      es_backend,
                                      str(args.days) + "d",
                                      args.version, update=False)
    elif args.summary_uuid is not None:
        lib.data_summary.summary_uuid(es_backend, config, args.summary_uuid,
                                      args.update)
    elif args.clf_days is not -1:
        lib.update_classifiers.update(config, args.clf_days)
    elif args.test_days is not -1:
        lib.test_classifiers.test(config, args.test_days)
    elif args.short_days is not -1:
        lib.crdb_summary.time_summary(config,
                                      int(args.short_days))
    else:
        args.error("No arguments defined!")


if __name__ == '__main__':
    sys.exit(main())
