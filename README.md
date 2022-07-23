## Blender Add-on: Fireworks

Make Fireworks.

## Installation

- Download https://github.com/SaitoTsutomu/Fireworks/archive/refs/heads/master.zip
- Start Blender.
- Edit menu -> Preferences
  - Select the "Add-ons" tab.
  - Press the "Install ...".
  - Select the downloaded ZIP file and press the button "Install Add-on".
  - Check the "Object: Fireworks".

## Usage

### Make Yaml file

sample

```
shot1:
  radius: 0.1
  particle_size: 0.06
  material:
    color: [1, 1, 0.5, 1]
    strength: 30
  launch: 1
  launch_location: [0, 0, 0]
  explode: 60
  explode_location: [2, 3, 10]
  particle_systems:
    up:
      count: 200
      frame_start: launch + 0
      frame_end: explode + 15
      lifetime: 20
      material:
        color: [1, 1, 0.5, 1]
        strength: 30
    ex1:
      count: 400
      frame_start: explode + 0
      frame_end: explode + 5
      lifetime: 40
      factor_random: 1
      gravity: 0
      material:
        color_ramp:
          - position: 0.5
            color: [1, 1, 0, 1]
          - position: 1
            color: [1, 1, 0, 0.1]
        strength: 30
    ex2:
      count: 1000
      frame_start: explode - 2
      frame_end: explode + 10
      lifetime: 50
      factor_random: 2
      gravity: 0
      material:
        color_ramp:
          - position: 0.5
            color: [0, 1, 0, 1]
          - position: 1
            color: [1, 0, 0, 0.1]
        strength: 30
```

### Operation

- Show the Sidebar.
- Show the Edit tab.
- Set the fullpath of Yaml file.
- Press the "Make".
