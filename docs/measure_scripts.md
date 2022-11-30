# Measure scripts

FINESSE allows users to trigger a sequence of recordings with the mirror at different
angles. The exact sequence, defined in terms of what the sequence of angles is and how
many repeats to do, can be saved to a files, which we are calling "measure scripts".

These files are written in [YAML](https://yaml.org/) format, with certain properties.
Here is an example:

```yaml
measurements:
  count: 10
  sequence:
  - angle: zenith
    count: 1
  - angle: 10.0
    count: 3
```

Note that everything is under the top-level key, `measurements`. Next is the `count`
property, which specifies how many times *the entire sequence* is run. This sequence is
composed of two movements: first to the zenith and second to an angle of 10°. Note that
angles can be specified either as a string corresponding to one of the preset angles or
as a floating-point value in degrees. Each item in the sequence also has a `count`
property, which indicates how many recordings should be taken at the given angle.
