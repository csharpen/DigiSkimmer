import importlib.util
import os
import logging
import json

VERSION = '0.20.5'
KIWI_USER = "digiskr_%s" % VERSION
DECODING_SOFTWARE = "DigiSkimmer %s" % VERSION
MODES = {'~': 'FT8', '#': 'JT65', '@': 'JT9', '+': 'FT4', '!': 'WSPR'}
BANDS = {   #Freq in MHz
    'FT8': {'160':1.840, '80':3.573, '60':5.357, '40':7.074, '30':10.136, '20':14.074, '17':18.100, '15':21.074, '12':24.915, '10':28.074, '6':50.313},
    'FT4': {'80':3.575, '40':7.0475, '30':10.140, '20':14.080, '17':18.104, '15':21.140, '12':24.919, '10':28.180, '6':50.318},
    'WSPR': {
        '2190': 0.136000, '630': 0.474200, '160': 1.836600, '80': 3.568600, '60': 7.038600, '40': 7.038600, '30': 10.138700,
        '20': 14.095600, '17': 18.104600, '15': 21.094600, '12': 24.924600, '10': 28.124600, '6': 50.293000,
        '2': 144.489000, '0.7': 432.300000
    }
}

class ConfigNotFoundException(Exception):
    pass


class ConfigError(object):
    def __init__(self, key, message):
        self.key = key
        self.message = message

    def __str__(self):
        return "Configuration Error (key: {0}): {1}".format(self.key, self.message)


class Config:
    instance = None

    @staticmethod
    def _loadPythonFile(file):
        spec = importlib.util.spec_from_file_location("settings", file)
        cfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cfg)
        conf = {}
        for name, value in cfg.__dict__.items():
            if name.startswith("__"):
                continue
            conf[name] = value
        return conf

    @staticmethod
    def _loadJsonFile(file):
        with open(file, "r") as f:
            conf = {}
            for k, v in json.load(f).items():
                conf[k] = v
            return conf

    @staticmethod
    def _loadConfig():
        for file in ["./settings.py", "./settings.json"]:
            try:
                if file.endswith(".py"):
                    return Config._loadPythonFile(file)
                elif file.endswith(".json"):
                    return Config._loadJsonFile(file)
                else:
                    logging.warning("unsupported file type: %s", file)
            except FileNotFoundError:
                pass
        raise ConfigNotFoundException(
            "no usable config found! please make sure you have a valid configuration file!")

    @staticmethod
    def get():
        if Config.instance is None:
            Config.instance = Config._loadConfig()
        return Config.instance

    @staticmethod
    def store():
        with open("settings.json", "w") as file:
            json.dump(Config.get().__dict__(), file, indent=4)

    @staticmethod
    def validateConfig():
        conf = Config.get()
        errors = [
            Config.checkTempDirectory(conf)
        ]

        errors += [
            Config.checkStations(conf)
        ]

        return [e for e in errors if e is not None]

    @staticmethod
    def checkTempDirectory(conf: dict):
        key = "PATH"
        if key not in conf or conf[key] is None:
            return ConfigError(key, "temporary directory is not set")
            
        return None

    @staticmethod
    def checkStations(conf: dict):
        key = "STATIONS"
        if key not in conf or conf[key] is None:
            return ConfigError(key, "STATIONS is not set")
        
        for k, v in conf[key].items():
            if not "callsign" in v:
                return ConfigError(key, "%s->callsign is not set" % k)

        return None
