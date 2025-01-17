# Measure scripts

FROG allows users to trigger a sequence of recordings with the mirror at different
angles. The exact sequence, defined in terms of what the sequence of angles is and how
many repeats to do, can be saved to a files, which we are calling "measure scripts".

These files are written in [YAML](https://yaml.org/) format, with certain properties.
Here is an example:

```yaml
repeats: 10
sequence:
- angle: zenith
  measurements: 1
- angle: 10.0
  measurements: 3
```

First is the `repeats` property, which specifies how many times *the entire sequence* is
run. The `sequence` property specifies which angles the mirror should move to (`angle`)
and how many measurements should be recorded at each of these positions
(`measurements`). This example sequence is composed of two movements: first to the
zenith and second to an angle of 10°. Note that angles can be specified either as a
string corresponding to one of the preset angles or as a floating-point value in
degrees.
