# Hardware

To work, FINESSE requires connections to a number of devices. At a minimum, this must
include:

- An interferometer
- A stepper motor for orienting the interferometer's mirror
- Temperature controllers for getting and setting the temperature of the hot and cold
  black bodies
- A separate temperature monitor with sensors recording from various angles around the
  mirror

All the code for interfacing with the hardware lives in the
[`finesse.hardware`](../reference/finesse/hardware) module.

## Plugin architecture

Code in the `finesse.hardware` module is not imported into the frontend code
([`finesse.gui`](../reference/finesse/gui)) directly. Instead, messages are passed back
and forth using the [PyPubSub](https://pypi.org/project/PyPubSub/) package.

As we want the user to be able to select which devices to use at runtime, the FINESSE
hardware framework is designed to be modular. This is achieved via a plugin system. Each
device type and device base type (explained below) is represented by a plugin class
residing somewhere in the
[`finesse.hardware.plugins`](../reference/finesse/hardware/plugins) module. To add a new
plugin, it is sufficient just to define this class in a `.py` file and put it somewhere
in the plugins directory hierarchy.

### Creating a new device type

A device base type is a class providing a common interface for similar device types
(e.g. a stepper motor). Each device base class must inherit from `Device` and each
device class must inherit from a device base class.

You can create a new device base like so:

```py
class MyBaseType(
    Device, is_base_type=True, name="my_base_type", description="Example base type"
):
    # ...
```

The `is_base_type=True` is required to register the class as a device base type. `name`
is the short name for the base type and is used in the topic for PyPubSub messages (see
more below). `description` provides a human-readable name for the base type, which will
be displayed in the GUI. It is additionally possible to provide a list of possible names
for instances of the device, but this is currently only used for temperature controllers
(to distinguish between the hot and cold black body controllers).

You can create a concrete implementation of `MyBaseType` like so:

```py
class MyDevice(MyBaseType, description="An example device"):
    # ...
```

Certain device base types require extra parameters. For example, to create a USB serial
device type which also inherits from `MyBaseType`, you can do:

```py
class MySerialDevice(
    SerialDevice, MyBaseType, description="An example device", default_baudrate=9600
):
    # ...
```

### Device parameters

Devices can also require additional parameters to be specified by the user, such as port
and baudrate for serial devices. Details about these parameters are set in an
`__init_subclass__()` method for the class. These parameters will be passed as arguments
to the device type's constructor when it is opened.

### Communicating with devices via PyPubSub

Many messages for communicating with devices include a string indicating which device
the communication is intended for. This is composed of the device base type's name and,
if provided, the device's name. For example, this could be `stepper_motor` for the
stepper motor and `temperature_controller.hot_bb` for the hot black body temperature
monitor.

When the main program window has loaded, the plugins are dynamically loaded and
information about each device type (grouped by base type) is sent to the frontend with
the `device.list` message.

To connect to a device, the frontend should send a `device.open` message, indicating
which device type should be opened, along with any device parameters. If the connection
is successful, a `device.opening.*` message is sent, followed by a `device.opened.*`
one. If the connection fails, a `device.error.*` message is sent instead.
(`device.error.*` messages can also be sent at any point during the device's lifetime to
indicate that an error has occurred.) Similarly, the `device.close` method is used to
close a connection to a device.

Device types also need to define their own message types for communication. For example,
the `StepperMotorBase` class allows for setting the current angle of the stepper motor
with a `device.stepper_motor.move.begin` message.
