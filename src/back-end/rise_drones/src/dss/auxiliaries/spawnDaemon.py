import os

# https://stackoverflow.com/questions/972362/spawning-process-from-python/972383#972383
def spawnDaemon(path_to_executable, *args, chdir=None):
  """Spawn a completely detached subprocess (i.e., a daemon).

  E.g. for mark:
  spawnDaemon("../bin/producenotify.py", "producenotify.py", "xx")
  """
  # fork the first time (to make a non-session-leader child process)
  try:
    pid = os.fork()
  except OSError as e:
    raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno)) from e
  if pid != 0:
    # parent (calling) process is all done
    os.waitpid(pid, 0)
    return

  # detach from controlling terminal (to make child a session-leader)
  os.setsid()
  try:
    pid = os.fork()
  except OSError as e:
    raise RuntimeError("2nd fork failed: %s [%d]" % (e.strerror, e.errno)) from e

  if pid != 0:
    # child process is all done
    os._exit(0) #pylint: disable=protected-access

  # grandchild process now non-session-leader, detached from parent
  # grandchild process must now close all open files
  try:
    maxfd = os.sysconf("SC_OPEN_MAX")
  except (AttributeError, ValueError):
    maxfd = 1024

  for fd in range(maxfd):
    try:
      os.close(fd)
    except OSError: # ERROR, fd wasn't open to begin with (ignored)
      pass

  # redirect stdin, stdout and stderr to /dev/null
  os.open(os.devnull, os.O_RDWR)  # standard input (0)
  os.dup2(0, 1)
  os.dup2(0, 2)

  # and finally let's execute the executable for the daemon!
  try:
    if chdir:
      os.chdir(chdir)
    os.execv(path_to_executable, args)
  except Exception as e:
    # oops, we're cut off from the world, let's just give up
    os._exit(255) #pylint: disable=protected-access
