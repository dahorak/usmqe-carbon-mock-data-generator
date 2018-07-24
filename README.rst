==================================
 USMQE Carbon Mock Data Generator
==================================

This repository contains python scripts for generating mock data for
`Tendrl`_ - Grafana Dashboards.

Inspired by `carbon-random`_ script.

Example usage
-------------

1. First of all, you need to find the metrics you want to generate data for.

   You can list all available metrics::

    # ./usmqe_carbon_mock_data_generator.py -s server.example.com list

   And you can filter the list of metrics::

    # ./usmqe_carbon_mock_data_generator.py -s server.example.com list \
        --filter 'used_capacity'

    # ./usmqe_carbon_mock_data_generator.py -s server.example.com list \
        --filter 'utilization !inode !thin_pool'

   As a *filter* you can use list of space separated strings which should
   be (or with exclamation mark not be) present in the filtered list of metric.
   All the words are combined with logical and.

   Prepare *filter* which will return only the desired metrics you want to
   update.

2. Once you find the correct *filter* which will return the desired metrics,
   prepare configuration file (see the section below) and generate the mock
   data for the desired period of time (from 2018-07-01 till now in the
   following example)::

    # ./usmqe_carbon_mock_data_generator.py -s server.example.com  generate \
        --since 2018-07-01 -c example_config.yml


Example configuration file
--------------------------

The configuration file is yaml file with list of dictionaries, each dictionary
usually contains configuration for one metric or set of similar metrics.

See the following example and explanation below::

  ---
  - filter: "usable_capacity"
    generators:
      - name: constant
        # 100GB
        value: 104857600
  
  - filter: "used_capacity !volume_beta"
    generators:
      - name: linear
        # from 0GB
        value_a: 0
        # to 90GB
        value_b: 94371840
      - name: noise
        percent: 5

The example above will generate data for two different set of metrics, defined
by ``filter``:

- the first one is for all metrics containing string *usable_capacity*
- and the second is for metrics containing string *used_capacity* but not
  containing string *volume_beta*.

Parameter ``generators`` contains list of data generators with parameters.
The generated value is combined from all the generators in the list.
The order of the generators is mandatory, because some generators use the
already generated value.

List of available generator functions:

- ``random``: generate random number between ``min`` and ``max``
- ``constant``: return (generate) constant number defined by ``value`` (default: 0)
- ``random_constant``: generate random constant number between ``min`` and ``max``
                   (the value will be the same for whole one metric)
- ``linear``: generate linear graph between ``value_a`` and ``value_b``
- ``triangle``: Generate triangle wave between ``value_a`` and ``value_b`` with
            ``period`` (number in seconds).
- ``sawtooth``: Generate sawtooth wave between ``value_a`` and ``value_b`` with
            ``period`` (number in seconds).
- ``sin``: Generate sinus wave between ``value_a`` and ``value_b`` with
            ``period`` (number in seconds).
- ``noise``: Generate random noise in range from ``-min`` to ``max`` or as
         ``percent`` of already generated value.
- ``boundaries``: Ensure, that generated value will be between ``min`` and ``max``
              boundaries.
- ``abs``: Ensure, that generated value will be positive.

License
-------

Distributed under the terms of the `Apache License 2.0`_ license.


.. _`Tendrl`: http://tendrl.org/
.. _`carbon-random`: https://github.com/cloudbehl/carbon-random
.. _`Apache License 2.0`: http://www.apache.org/licenses/LICENSE-2.0
