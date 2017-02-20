import yaml
import sys
from backend import Backend


def _load_config(path):
    try:
        stream = open(path, 'r')
    except IOError:
        self.logger.error("Configuration file {} passed is missing".format(path))
        exit(1)
    config = yaml.load(stream)
    stream.close()
    return config

def main():
   config = "config.yml"
   config = _load_config(config)
   es_backend = Backend(config)
   es_backend.get_training_vectors(config)

if __name__ == '__main__':
    sys.exit(main())
