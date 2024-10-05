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

### Make toml file

sample

```
[shot1]
explode = 60
explode_location = [2, 3, 10]
launch = 1
launch_location = [0, 0, 0]
particle_size = 0.06
radius = 0.1

    [shot1.material]
    color = [1, 1, 0.5, 1]
    strength = 30

    [shot1.particle_systems]
        [shot1.particle_systems.up]
        count = 200
        frame_end = "explode + 15"
        frame_start = "launch + 0"
        lifetime = 20
            [shot1.particle_systems.up.material]
            color = [1, 1, 0.5, 1]
            strength = 30

        [shot1.particle_systems.ex1]
        count = 400
        factor_random = 1
        frame_end = "explode + 5"
        frame_start = "explode + 0"
        gravity = 0.1
        lifetime = 40
            [shot1.particle_systems.ex1.material]
            strength = 30
                [[shot1.particle_systems.ex1.material.color_ramp]]
                color = [1, 1, 0, 1]
                position = 0.5
                [[shot1.particle_systems.ex1.material.color_ramp]]
                color = [1, 1, 0, 0.1]
                position = 1

        [shot1.particle_systems.ex2]
        count = 1000
        factor_random = 2
        frame_end = "explode + 10"
        frame_start = "explode - 2"
        gravity = 0.1
        lifetime = 50
            [shot1.particle_systems.ex2.material]
            strength = 30
                [[shot1.particle_systems.ex2.material.color_ramp]]
                color = [0, 1, 0, 1]
                position = 0.5
                [[shot1.particle_systems.ex2.material.color_ramp]]
                color = [1, 0, 0, 0.1]
                position = 1
```

### Operation

- Show the Sidebar.
- Show the Edit tab.
- Set the path of Toml file.
- Press the "Make".

## Reference

https://qiita.com/SaitoTsutomu/items/9c7aae103bf13d72dd5c
