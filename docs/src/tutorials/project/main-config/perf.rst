Configuration for summary performance measures. Does not have to be named
``perf-config.yaml``, but must match whatever is specified in
``main.yaml``.

.. code-block:: YAML

   # Root key is required.
   perf:

     # Is the performance measure for the project inverted, meaning that
     # lower values are better. This key is optional; defaults to False if
     # omitted.
     inverted: true

     # The CSV file under ``statistics/`` for each experiment which
     # contains the averaged performance information for the
     # experiment. This key is required.
     intra_perf_csv: 'block-transport.csv'

     # The CSV column within ``intra_perf_csv`` which is the
     # temporally charted performance measure for the experiment. This key
     # is required.
     intra_perf_col: 'cum_avg_transported'

Additional fields can be added to this dictionary as needed to support
custom performance measures,graph generation, or batch criteria as
needed. For example, you could add fields to this dictionary as a lookup
table of sorts for a broader range of cmdline configuration (i.e., using
it to make the cmdline syntax for the a new batch criteria much nicer).
