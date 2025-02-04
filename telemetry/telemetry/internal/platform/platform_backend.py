# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry.internal.forwarders import do_nothing_forwarder
from telemetry.internal.platform import network_controller_backend
from telemetry.internal.platform import tracing_controller_backend
from telemetry.testing import test_utils


# pylint: disable=unused-argument

class PlatformBackend(object):

  def __init__(self, device=None):
    """ Initalize an instance of PlatformBackend from a device optionally.
      Call sites need to use SupportsDevice before intialization to check
      whether this platform backend supports the device.
      If device is None, this constructor returns the host platform backend
      which telemetry is running on.

      Args:
        device: an instance of telemetry.core.platform.device.Device.
    """
    if device and not self.SupportsDevice(device):
      raise ValueError('Unsupported device: %s' % device.name)
    self._platform = None
    self._network_controller_backend = None
    self._tracing_controller_backend = None
    self._forwarder_factory = None

  def InitPlatformBackend(self):
    self._network_controller_backend = (
        network_controller_backend.NetworkControllerBackend(self))
    self._tracing_controller_backend = (
        tracing_controller_backend.TracingControllerBackend(self))

  @classmethod
  def IsPlatformBackendForHost(cls):
    """ Returns whether this platform backend is the platform backend to be used
    for the host device which telemetry is running on. """
    return False

  @classmethod
  def SupportsDevice(cls, device):
    """ Returns whether this platform backend supports intialization from the
    device. """
    return False

  @classmethod
  def CreatePlatformForDevice(cls, device, finder_options):
    raise NotImplementedError

  def SetPlatform(self, platform):
    assert self._platform is None
    self._platform = platform

  @property
  def platform(self):
    return self._platform

  @property
  def is_host_platform(self):
    return self._platform.is_host_platform

  @property
  def network_controller_backend(self):
    return self._network_controller_backend

  @property
  def tracing_controller_backend(self):
    return self._tracing_controller_backend

  @property
  def forwarder_factory(self):
    if not self._forwarder_factory:
      self._forwarder_factory = self._CreateForwarderFactory()
    return self._forwarder_factory

  def _CreateForwarderFactory(self):
    return do_nothing_forwarder.DoNothingForwarderFactory()

  def GetRemotePort(self, port):
    return port

  def GetSystemLog(self):
    return None


  def IsRemoteDevice(self):
    """Check if target platform is on remote device.

    Returns True if device is remote, i.e. android
    device connected via adb or running a test with
    remote option specifying the ip address of a cros device.
    Return False for other platforms.
    """
    return False

  def IsDisplayTracingSupported(self):
    return False

  def StartDisplayTracing(self):
    """Start gathering a trace with frame timestamps close to physical
    display."""
    raise NotImplementedError()

  def StopDisplayTracing(self):
    """Stop gathering a trace with frame timestamps close to physical display.

    Returns a raw tracing events that contains the timestamps of physical
    display.
    """
    raise NotImplementedError()

  def SetFullPerformanceModeEnabled(self, enabled):
    pass

  def CanMonitorThermalThrottling(self):
    return False

  def IsThermallyThrottled(self):
    raise NotImplementedError()

  def HasBeenThermallyThrottled(self):
    raise NotImplementedError()

  def GetSystemTotalPhysicalMemory(self):
    raise NotImplementedError()

  def GetCpuStats(self, pid):
    return {}

  def GetCpuTimestamp(self):
    return {}

  def GetChildPids(self, pid):
    raise NotImplementedError()

  def GetCommandLine(self, pid):
    raise NotImplementedError()

  def GetDeviceTypeName(self):
    raise NotImplementedError()

  def GetArchName(self):
    raise NotImplementedError()

  def GetOSName(self):
    raise NotImplementedError()

  def GetDeviceId(self):
    return None

  def GetOSVersionName(self):
    raise NotImplementedError()

  def GetOSVersionDetailString(self):
    raise NotImplementedError()

  def CanFlushIndividualFilesFromSystemCache(self):
    raise NotImplementedError()

  def SupportFlushEntireSystemCache(self):
    return False

  def FlushEntireSystemCache(self):
    raise NotImplementedError()

  def FlushSystemCacheForDirectory(self, directory):
    raise NotImplementedError()

  def FlushDnsCache(self):
    pass

  def LaunchApplication(
      self, application, parameters=None, elevate_privilege=False):
    raise NotImplementedError()

  def StartActivity(self, intent, blocking):
    raise NotImplementedError()

  def IsApplicationRunning(self, application):
    raise NotImplementedError()

  def CanLaunchApplication(self, application):
    return False

  def InstallApplication(self, application):
    raise NotImplementedError()

  def CanMonitorPower(self):
    return False

  def CanMeasurePerApplicationPower(self):
    return False

  def StartMonitoringPower(self, browser):
    raise NotImplementedError()

  def StopMonitoringPower(self):
    raise NotImplementedError()

  def CanTakeScreenshot(self):
    return False

  def TakeScreenshot(self, file_path):
    raise NotImplementedError

  def IsCooperativeShutdownSupported(self):
    """Indicates whether CooperativelyShutdown, below, is supported.
    It is not necessary to implement it on all platforms."""
    return False

  def CooperativelyShutdown(self, proc, app_name):
    """Cooperatively shut down the given process from subprocess.Popen.

    Currently this is only implemented on Windows. See
    crbug.com/424024 for background on why it was added.

    Args:
      proc: a process object returned from subprocess.Popen.
      app_name: on Windows, is the prefix of the application's window
          class name that should be searched for. This helps ensure
          that only the application's windows are closed.

    Returns True if it is believed the attempt succeeded.
    """
    raise NotImplementedError()

  def PathExists(self, path, timeout=None, retries=None):
    """Tests whether the given path exists on the target platform.
    Args:
      path: path in request.
      timeout: timeout.
      retries: num of retries.
    Return:
      Whether the path exists on the target platform.
    """
    raise NotImplementedError()

  def WaitForBatteryTemperature(self, temp):
    pass

  def WaitForCpuTemperature(self, temp):
    pass

  def GetTypExpectationsTags(self):
    return test_utils.sanitizeTypExpectationsTags(
        [self.GetOSName(), self.GetOSVersionName()])
