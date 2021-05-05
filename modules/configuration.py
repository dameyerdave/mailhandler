import yaml
from pydotdict import DotDict
from os.path import exists


class ParseError(Exception):
    pass


class NotParsedError(Exception):
    pass


class Configuration():
    """
    Loads the configuration from a yaml file and provides function to handle the config.
    """

    def __init__(self, config_file):
        self.config_file = config_file
        self.__config = {}

    def parse(self):
        """
        Parses the yaml config file into the internal config variable
        """
        try:
            if exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.__config = yaml.load(f, Loader=yaml.FullLoader)
        except Exception as ex:
            raise ParseError(ex)

    def rules(self):
        if 'rules' not in self.__config:
            raise NotParsedError(
                'The configuration is not yet parsed, please run parse() first.')
        rules = []
        for rule in self.__config['rules']:
            rules.append(DotDict(rule))
        return rules
