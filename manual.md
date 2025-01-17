# Build instructions

Instructions only tested on Ubuntu Linux. They can also be found in the manual.md

## Requirements

### Software

Those software can be installed either through the package manager or though the instruction available on their website

- [Webots](https://cyberbotics.com/)
- [Gazebo 11](http://gazebosim.org/)
- [Ignition Dome](https://ignitionrobotics.org/)

### Package Manager

Those packages can be installed through the package manager if on linux or built from source is on Windows (not recommended)

- ROS2 Foxy
- webots_ros2
- gazebo_ros2_pkgs
- python3-colcon-common-extensions (in case not installed during ROS2 installation)

### Building from Source

Those packages do not have an official release and as such must be built from source and then sourced in all terminal in which we want to use this project

- MoveIt2 (Instructions available on [MoveIt2 Website](https://moveit.ros.org/install-moveit2/source/))
- ros_ign (Instructions available on [Github](https://github.com/ignitionrobotics/ros_ign/))
- ign_moveit2 (Instructions available on [Github](https://github.com/09ubberboy90/ign_moveit2))
- gazebo_ros2_control (Instructions available on [Github](https://github.com/ros-simulation/gazebo_ros2_control))

## Build steps

```bash
mkdir workspace
cd workspace
git clone https://github.com/09ubberboy90/ros2_sim_compare.git (This project)
rosdep install -r --from-paths . --ignore-src --rosdistro foxy -y
cd ..
colcon build
```

If the last step executed without any errors source the environment with `source workspace/install/local_setup.sh`

# Running the program

Individual simulation can be run either individually or automatically.

## Automatic Run

Automatic run allow to run the simulation and also record the resource usage. The general command is:
`ros2 run sim_recorder run_recording {simulation_name} {iterations}`

`simulation_name` can be replace with individual simulation name. Below are the list of names. `iterations` is the number of time the simulation should be repeated. If omitted defaults to 0.

Each results will be stored in `./sim_recorder/data`. Please refer to the README there for the data structure.

### Pick and Place

- webots
- gazebo
- ignition (JointStates)
- github_ignition (Trajectory)

### Throw

- webots_throw
- gazebo_throw
- ignition_throw (JointStates)
- github_ignition_throw (Trajectory)

### Graphing

Because the program was run automatically it is possible to graph the results using:

``` bash
cd ./sim_recorder/sim_recorder
python grapher.py {simulation_name}
```

The resulting graph will be stored in `./data/{simulation_name}` as a CSV file.

## Manual run

Manual run are also possible but requires multiple open terminal and the order of commands must be respected.

### Webots Pick and Place

- `ros2 launch webots_simple_arm pick_place.launch.py`,
- `ros2 launch webots_simple_arm collision_webots.launch.py`,
- `ros2 launch webots_simple_arm moveit_webots.launch.py`,

### Webots Throw

- `ros2 launch webots_simple_arm pick_place.launch.py`,
- `ros2 launch webots_simple_arm throw_collision.launch.py`,
- `ros2 launch webots_simple_arm throw_moveit.launch.py`,

### Gazebo Pick and Place

- `ros2 launch simple_arm gazebo.launch.py`,
- `ros2 launch simple_move_group run_move_group.launch.py`,
- `ros2 launch simple_arm collision_gazebo.launch.py`,
- `ros2 launch simple_arm moveit_gazebo.launch.py`,

### Gazebo Throw

- `ros2 launch simple_arm gazebo.launch.py`,
- `ros2 launch simple_move_group run_move_group.launch.py`,
- `ros2 launch simple_arm throw_collision.launch.py`,
- `ros2 launch simple_arm throw_moveit.launch.py`,

### Ignition JointStates Pick and Place

- `ros2 launch simple_arm ign_place.launch.py`,
- `ros2 launch simple_move_group run_move_group.launch.py`,
- `ros2 launch simple_arm moveit_ign.launch.py`,

### Ignition JointStates Throw

- `ros2 launch simple_arm ign_throw.launch.py`,
- `ros2 launch simple_move_group run_move_group.launch.py`,
- `ros2 launch simple_arm ign_throw_moveit.launch.py`,

### Ignition Trajectory Pick and Place

`ros2 launch ign_moveit2 example_place.launch.py`,

### Ignition Trajectory Throw

`ros2 launch ign_moveit2 example_throw.launch.py`,

### VR

On the first Windows machine run:

`ros2 run simple_arm vr_publish`

On the linux machine run:

`ros2 launch simple_arm ign_vr.launch.py`

