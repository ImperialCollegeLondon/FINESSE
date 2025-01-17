# Hardware

To work, FROG requires connections to a number of devices. At a minimum, this must
include:

- An interferometer
- A stepper motor for orienting the interferometer's mirror
- Temperature controllers for getting and setting the temperature of the hot and cold
  black bodies
- A separate temperature monitor with sensors recording from various angles around the
  mirror

All the code for interfacing with the hardware lives in the
[`frog.hardware`](../reference/frog/hardware) module.

## Plugin architecture

Code in the `frog.hardware` module is not imported into the frontend code
([`frog.gui`](../reference/frog/gui)) directly. Instead, messages are passed back and
forth using the [PyPubSub](https://pypi.org/project/PyPubSub/) package.

As we want the user to be able to select which devices to use at runtime, the FROG
hardware framework is designed to be modular. This is achieved via a plugin system. Each
device type and device base type (explained below) is represented by a plugin class
residing somewhere in the [`frog.hardware.plugins`](../reference/frog/hardware/plugins)
module. To add a new plugin, it is sufficient just to define this class in a `.py` file
and put it somewhere in the plugins directory hierarchy.

### Creating a new device type

There are three "kinds" of device classes:

1. Device base types, which must inherit from `Device` directly
2. Abstract device types, which must inherit from a device base type (directly or
   indirectly) and have at least one abstract method
3. Concrete device types which must inherit from one of the above and have no abstract
   methods

Device base types and concrete device types are included in registries that are
communicated to the frontend if it requests a list of plugins (abstract device types are
excluded). Note that there are other possibilities one could imagine (e.g. a class
inheriting from `Device` which is not registered as a device base type), but these are
currently not possible.

A device base type is a class providing a common interface for similar device types
(e.g. a stepper motor). You can create a new device base like so:

```py
class MyBaseType(
    Device, name="my_base_type", description="Example base type"
):
    # ...
```

As this class inherits directly from `Device`, it will be registered as a device base
type. `name` is the short name for the base type and is used in the topic for PyPubSub
messages (see more below). `description` provides a human-readable name for the base
type, which will be displayed in the GUI. It is additionally possible to provide a list
of possible names for instances of the device, but this is currently only used for
temperature controllers (to distinguish between the hot and cold black body
controllers).

You can create a concrete implementation of `MyBaseType` like so:

```py
class MyDevice1(MyBaseType, description="An example device"):
    # ...
```

You may optionally provide a `dict` specifying which parameters should be passed when
the device object is constructed, along with a human-readable description. This provides
a mechanism by which the frontend can know what parameters it can provide for a given
device type, as well as information about their type and default value (if any). Here is
an example:

```py
class MyDevice2(
    MyBaseType,
    description="An example device",
    parameters={"my_param": "An example parameter"}
):
    def __init__(self, my_param: int = 42) -> None:
        # ...
```

In this case, the frontend will be informed that `MyDevice2` has a parameter, `my_param`
of type `int` with a default value of `42`. The user can then alter this value via a
text box in the GUI. Note that if a default value were *not* provided for this
parameter, the user would be forced to enter one. Subclasses inherit their parents'
device parameters (but can add more of their own). As a result, they *must* also include
these parameters for their constructors.

You can also provide a `Sequence` of possible values that a parameter can take, e.g.:

```py
class MyDevice3(
    MyBaseType,
    description="An example device",
    parameters={"my_param": ("An example parameter", range(10))}
):
    def __init__(self, my_param: int = 5) -> None:
        # ...
```

In this case, `my_param` must be a number in the range 0 to 9. The user will be able to
select from among these options in a dropdown box.

Subclasses can provide different default values for device parameters than their
parents, simply by providing a different default value in their constructors. This is
used by device classes for USB serial devices to choose a default baud rate. For
example:

```py
class MyUSBDevice(SerialDevice, MyBaseType, description="A USB serial device"):
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        # ...
```

Note that the constructor must have both the `port` and `baudrate` parameters as they
are defined as device parameters by the `SerialDevice` base class. The `SerialDevice`
class must be listed before `MyBaseType` unless `MyUSBDevice` defines its own `close()`
method, otherwise you will get an error about this abstract method not being
implemented.

### Communicating with devices via PyPubSub

Many messages for communicating with devices include a string indicating which device
the communication is intended for (prefixed by `device.`). This is composed of the
device base type's name and, if provided, the device's name. For example, this could be
`stepper_motor` for the stepper motor and `temperature_controller.hot_bb` for the hot
black body temperature controller.

To connect to a device, the frontend should send a `device.open` message, indicating
which device type should be opened, along with any device parameters. If the connection
is successful, a `device.opening.*` message is sent, followed by a `device.opened.*`
one. If the connection fails, a `device.error.*` message is sent instead.
(`device.error.*` messages can also be sent at any point during the device's lifetime to
indicate that an error has occurred.) Similarly, the `device.close` method is used to
close a connection to a device.

If the frontend sends a `device.list.request` message all of the plugins are loaded and
information about each device type (grouped by base type) is sent to the frontend with
the `device.list.response` message. Note that this step is not required in order to open
a device: if the name of the plugin and values for parameters are known (e.g. if the
user is connecting to a predefined hardware set), it is sufficient to just send the
`device.open` message.

Device types also need to define their own message types for communication. For example,
the `StepperMotorBase` class allows for setting the current angle of the stepper motor
with a `device.stepper_motor.move.begin` message.
