'''
  @file allknn.py
  @author Marcus Edel

  Class to benchmark the flann All K-Nearest-Neighbors method with kd-trees.
'''

import os
import sys
import inspect

# Import the util path, this method even works if the path contains symlinks to
# modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], "../../util")))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

from log import *
from profiler import *

import shlex
import subprocess
import re
import collections

'''
This class implements the All K-Nearest-Neighbor Search benchmark.
'''
class ALLKNN(object):

  '''
  Create the All K-Nearest-Neighbors benchmark instance, show some informations
  and return the instance.

  @param dataset - Input dataset to perform All K-Nearest-Neighbors on.
  @param timeout - The time until the timeout. Default no timeout.
  @param path - Path to the flann executable.
  @param verbose - Display informational messages.
  '''
  def __init__(self, dataset, timeout=0, path=os.environ["FLANN_PATH"],
        verbose = True):
    self.verbose = verbose
    self.dataset = dataset
    self.path = path
    self.timeout = timeout

  '''
  Perform All K-Nearest-Neighbors. If the method has been successfully completed
  return the elapsed time in seconds.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def RunMetrics(self, options):
    Log.Info("Perform ALLKNN.", self.verbose)

    # If the dataset contains two files then the second file is the query file.
    # In this case we add this to the command line.
    if len(self.dataset) == 2:
      cmd = shlex.split(self.path + "allknn -r " + self.dataset[0] + " -q " +
          self.dataset[1] + " -v " + options)
    else:
      cmd = shlex.split(self.path + "allknn -r " + self.dataset +
          " -v " + options)

    # Run command with the nessecary arguments and return its output as a byte
    # string. We have untrusted input so we disable all shell based features.
    try:
      s = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False,
          timeout=self.timeout)
    except subprocess.TimeoutExpired as e:
      Log.Warn(str(e))
      return -2
    except Exception as e:
      Log.Fatal("Could not execute command: " + str(cmd))
      return -1

    # Datastructure to store the results.
    metrics = {}

    # Parse data: runtime.
    timer = self.parseTimer(s)

    if timer != -1:
      metrics['Runtime'] = timer.tree_building + timer.computing_neighbors
      metrics['TreeBuilding'] = timer.tree_building
      metrics['ComputingNeighbors'] = timer.computing_neighbors

      Log.Info(("total time: %fs" % (metrics['Runtime'])), self.verbose)

    return metrics

  '''
  Parse the timer data form a given string.

  @param data - String to parse timer data from.
  @return - Namedtuple that contains the timer data or -1 in case of an error.
  '''
  def parseTimer(self, data):
    # Compile the regular expression pattern into a regular expression object to
    # parse the timer data.
    pattern = re.compile(r"""
        .*?tree_building: (?P<tree_building>.*?)s.*?
        .*?computing_neighbors: (?P<computing_neighbors>.*?)s.*?
        """, re.VERBOSE|re.MULTILINE|re.DOTALL)

    match = pattern.match(data.decode())
    if not match:
      Log.Fatal("Can't parse the data: wrong format")
      return -1
    else:
      # Create a namedtuple and return the timer data.
      timer = collections.namedtuple("timer", ["tree_building",
                                               "computing_neighbors"])

      if match.group("tree_building").count(".") == 1:
        return timer(float(match.group("tree_building")),
                     float(match.group("computing_neighbors")))
      else:
        return timer(float(match.group("tree_building").replace(",", ".")),
                     float(match.group("computing_neighbors").replace(",", ".")))
