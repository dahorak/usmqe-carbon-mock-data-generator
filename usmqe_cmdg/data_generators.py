"""
Module with data generators for usmqe carbon client.
"""

import math
import random
import sys

import logging

LOGGER = logging.getLogger("usmqe_cmdg.%s" % __name__)

class DataGenerators(object):
    """
    Data generators class.
    """
    # pylint: disable=R0201
    def __init__(self, metric_name, since_time, until_time):
        """
        Initialize DataGenerators object
        """
        self.metric_name = metric_name
        self.since_time = since_time
        self.until_time = until_time
        self.prev_value = 0
        self.random_constant = None

    def data_generator(self, dg_name, timestamp, dg_args):
        """
        run data generator dg_name with supplied parameters
        """
        dg_args.update({
            "prev_value": self.prev_value,
            "timestamp": timestamp,
            })
        try:
            value = getattr(self, "dg_%s" % dg_name)(dg_args)
        except AttributeError:
            LOGGER.error("Data generator '%s' not defined!", dg_name)
            sys.exit(3)
        value += self.prev_value
        self.prev_value = value
        return value

    def dg_random(self, dg_args):
        """
        Generate random value between min and max.
        """
        random_number = random.randint(int(dg_args["min"]), int(dg_args["max"]))
        return random_number

    def dg_constant(self, dg_args):
        """
        Generate constant number value (default: 0).
        """
        return dg_args.get("value", 0)

    def dg_random_constant(self, dg_args):
        """
        Generate random value between min and max.
        """
        if self.random_constant is None:
            self.random_constant = random.randint(int(dg_args["min"]), int(dg_args["max"]))
        return self.random_constant

    def dg_linear(self, dg_args):
        """
        Generate linear "line" between the since and until time from value_a to value_b.
        dg_args:
            value_a
            value_b
        """
        time_period = self.until_time - self.since_time
        relative_time = dg_args["timestamp"] - self.since_time
        value = round(dg_args["value_a"] + ((dg_args["value_b"] - dg_args["value_a"]) * (relative_time / time_period)))
        return value

    def dg_triangle(self, dg_args):
        """
        Generate triangle wave between value_a and value_b.
        dg_args:
            value_a
            value_b
            period
        """
        amplitude = dg_args["value_b"] - dg_args["value_a"]
        relative_time = dg_args["timestamp"] - self.since_time
        value = round(dg_args["value_a"] + (amplitude / (dg_args["period"] / 2)) * \
                (dg_args["period"] / 2 - \
                abs(relative_time % dg_args["period"] - dg_args["period"] / 2)))
        return value

    def dg_sawtooth(self, dg_args):
        """
        Generate sawtooth wave between value_a and value_b.
        dg_args:
            value_a
            value_b
            period
        """
        amplitude = dg_args["value_b"] - dg_args["value_a"]
        relative_time = dg_args["timestamp"] - self.since_time
        value = round(dg_args["value_a"] + (amplitude * \
                ((relative_time % dg_args["period"]) / dg_args["period"])))
        return value

    def dg_sin(self, dg_args):
        """
        Generate sinus wave between value_a and value_b.
        dg_args:
            value_a
            value_b
            period
        """
        amplitude = dg_args["value_b"] - dg_args["value_a"]
        relative_time = dg_args["timestamp"] - self.since_time
        value = round(dg_args["value_a"] + (amplitude/2) + \
                (amplitude/2) * math.sin((relative_time * 2 * math.pi) / dg_args["period"]))
        return value

    def dg_noise(self, dg_args):
        """
        Generate random noise -min - max or percent of already generated value.
        """
        value = dg_args["prev_value"]
        _noise_min = dg_args.get("min", -round((dg_args.get("percent", 5)/100) * abs(value)))
        _noise_max = dg_args.get("max", round((dg_args.get("percent", 5)/100) * abs(value)))
        noise = random.randint(_noise_min, _noise_max)
        return noise

    def dg_boundaries(self, dg_args):
        """
        Ensure, that generated value will be between min and max boundaries.
        """
        value = dg_args["prev_value"]
        if "min" in dg_args and value < dg_args["min"]:
            return dg_args["min"] - value
        elif "max" in dg_args and value > dg_args["max"]:
            return dg_args["max"] - value
        else:
            return 0

    def dg_abs(self, dg_args):
        """
        Ensure, that generated value will be positive.
        """
        value = dg_args["prev_value"]
        return abs(value) - value

class DataGeneratorNotDefined(Exception):
    """
    DataGeneratorNotDefined Exception
    """
    pass
