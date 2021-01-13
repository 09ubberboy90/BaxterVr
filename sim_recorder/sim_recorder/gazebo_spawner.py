# Adapted from Xavier Weiss' code at: https://github.com/DEUCE1957/Automatic-Waste-Sorting

import os, sys, shutil
from os import path
import glob
import rclpy
from rclpy import Node
import random
import re
import numpy as np

from transforms3d.euler import euler2mat
from transforms3d.quaternions import mat2quat

import std_msgs,gazebo_msgs,geometry_msgs,moveit_msgs
from geometry_msgs.msg import Pose, Point, Quaternion
from gazebo_msgs.msg import LinkStates
from gazebo_msgs.srv import DeleteModel, SpawnModel, GetModelState, GetWorldProperties
from std_msgs.msg import String

# >>> Utilities <<<
def define_pose(x,y,z,**kwargs):
    """Returns a Pose based on x,y,z and optionally o_x,o_y,o_z and o_w"""
    pose_target = geometry_msgs.msg.Pose()
    pose_target.position.x = x
    pose_target.position.y = y
    pose_target.position.z = z

    pose_target.orientation.x = kwargs.get("o_x",0.0)
    pose_target.orientation.y = kwargs.get("o_y",1.0)
    pose_target.orientation.z = kwargs.get("o_z",0.0)
    pose_target.orientation.w = kwargs.get("o_w",0.0)
    return pose_target

def get_rpy_quaternion(roll,pitch,yaw):
    """Converts human readable roll (about x-axis), pitch (about y-axis)
    and yaw (about z-axis) format to a 4D quaternion"""
    return mat2quat(euler2mat(roll, pitch, yaw, 'sxyz'))

def isclose(a,b,rel_tol=1e-9,abs_tol=0.0):
    """Returns whether 2 floats are equal with a relative and absolute 
    tolerance to prevent problems from floating point precision"""
    return abs(a-b) <= max( rel_tol * max(abs(a), abs(b)), abs_tol )

class BoundingBox(object):
    """Defines a cuboid volume to represent an object's bounding volume
    If only x is supplied, constructs a x*x*x cube
    If y is also supplied, constructs a x*y*x cuboid
    If y and z are supplied, constructs a x*y*z cuboid"""
    def __init__(self, x, y=None, z=None):  # x,y,z
        self.x = x
        self.y = x if y is None else y
        self.z = x if z is None and y is None else (y if z is None else z)


class ObjectSpawner(object):
    """Provides convenient API for spawning any objects in the Gazebo model directory
    
    Attributes:
        -- Provided at initalization --
        reference_frame: coordinates are used relative to ref frame [default: 'world']
        bounding_box: defines a bounding volume for the object [default: 0.04*0.04*0.04]
        model_name: if not provided, interactively choose model [default: None]
        model_directory: if not provided, use default directory [default: None]
        verbose: How much daignostic info to print [default: 1]
        -- Generated --
        nested_dir: Gazebo models can only be used if placed at root of Gazebo model directory"""
    instances = {}

    def __init__(self, reference_frame="world", bounding_box=BoundingBox(0.04),
                 model_name=None, model_directory=None,
                 verbose=1):
        self.reference_frame = reference_frame
        self.bounding_box = bounding_box

        self.default_dir = path.join(os.getcwd(), "workspace", "src",
                                     "baxter_simulator",
                                     "baxter_sim_examples", "models")
        if model_directory is None:
            self.model_dir = self.default_dir
        else:
            self.model_dir = model_directory

        if model_name is None:
            self.model_name = self._choose_model()
        else:
            self.model_name = model_name

        # True if model is found in root model_path
        if not hasattr(self, "nested_dir"):
            self.nested_dir = self.model_dir

        self.verbose = verbose

    def spawn_model(self, pose):
        """Spawns a model at the target pose (position and orientation).
        
        If Spawning service failed: Returns None
        Else: Returns name of generated object and its real pose"""
        
        model_path = path.join(self.nested_dir, self.model_name, "model.sdf")
        with open(model_path, "r") as f:
            xml = f.read()

        if self.verbose >= 3:
            print(">> Loaded Model {} <<<\n{}".format(self.model_name, xml))

        rospy.wait_for_service('/gazebo/spawn_sdf_model')
        try:
            spawn_sdf = rospy.ServiceProxy('/gazebo/spawn_sdf_model',
                                           SpawnModel)

            # Enforce unique names
            if len(self.instances) == 0:
                name = self.model_name
            else:
                "{}_{}".format(self.model_name, len(self.instances))

            spawn_sdf(name, xml.replace("\n", ""),
                      "/", pose, self.reference_frame)

            self.instances[name] = pose
            return name, pose
        except rospy.ServiceException, e:
            rospy.logerr("Spawn {} failed: {}".format(self.model_name, e))
            return None

    def _choose_model(self):
        """Interactively select model by traversing Gazebo model subdirectories
        Copies chosen model to top of Gazebo Model path so that it is accessible
        Returns the chosen model name"""
        # Only descend into N levels of file path tree
        def walklevel(some_dir, level=1):
            some_dir = some_dir.rstrip(os.path.sep)
            assert os.path.isdir(some_dir)
            num_sep = some_dir.count(os.path.sep)
            for root, dirs, files in os.walk(some_dir):
                yield root, dirs, files
                num_sep_this = root.count(os.path.sep)
                if num_sep + level <= num_sep_this:
                    del dirs[:]

        # Get all VALID folders with mesh options
        def get_listdir(path, verbose=True):
            valid_dirs = {}
            count = 0
            for dir_name, child_dirs, files in walklevel(path, level=1):
                if child_dirs in [[], ['meshes'], ['materials', 'meshes']]:
                    continue
                else:
                    if verbose: print("{}: {}".format(count, dir_name))
                    valid_dirs[count] = dir_name
                    count += 1
            return valid_dirs

        # Ask user to pick directory by number
        def select_by_number(options, option_desc):
            while True:
                resp = raw_input("Type no of desired {}".format(option_desc))
                if re.match("\d+", resp):
                    if int(resp) in options.keys():
                        return options[int(resp)]  # Selected option
                print("Please pick desired {} by number".format(option_desc))

        if self.model_dir != self.default_dir:
            valid_folders = get_listdir(self.model_dir)
            category = select_by_number(valid_folders, "Category")
            self.nested_dir = path.join(self.model_dir, category)
            valid_models = os.listdir(self.nested_dir)
        else:  # Default Directory does not have categories
            valid_models = os.listdir(self.model_dir)

        # Final Choice: One Specific Model
        valid_models = dict(enumerate(valid_models, start=0))
        for key, value in valid_models.items():
            print("{}: {}".format(key, value))
        model_name = select_by_number(valid_models, "Model")

        if self.verbose >= 1: print("You selected: {}".format(model_name))

        return model_name

    def spawn_on_table(self, spawn=True, random_face=True,
                       table_bbox = BoundingBox(0.32, 0.5, 0.7825),
                       table_offset = Point(0.38, -0.1, 0.0)):
        """Spawns an object on a table's surface with random location and yaw. 
        
        Attributes:
            spawn: Whether to actually spawn the object [default:True]
            random_face: Whether to vary which face is front-facing (24 possibilities) [default: True]
            table_bbox: Defines table's bounding box, ensure this is reachable [default: 0.32*0.5*0.7825]
            table_offset: Where table is placed relative to world origin (0,0,0)
        Returns:
            Unique name in simulation, overhead RPY and real pose
        """
        x = random.uniform(table_offset.x, table_offset.x + table_bbox.x)  # Default: 0.38->0.7
        y = random.uniform(table_offset.y, table_offset.y + table_bbox.y)  # Default: -0.1->0.4)
        z = table_offset.z + table_bbox.z  # Default: 0.7825
        fixed_rotations = numpy.arange(0, 2*numpy.pi, numpy.pi/2)
        if random_face:
            roll, pitch, yaw = random.choice(fixed_rotations), \
                               random.choice(fixed_rotations), \
                               random.uniform(0, 2*numpy.pi)
        else:
            roll, pitch, yaw = numpy.pi, 0, random.uniform(0, 2*numpy.pi)

        q = get_rpy_quaternion(roll, pitch, yaw)

        pose = define_pose(x=x, y=y, z=z, o_x=q[0],
                           o_y=q[1], o_z=q[2], o_w=q[3])

        # ToDo: Use bounding boxes to avoid overlap

        name = None
        if spawn:
            name, _ = self.spawn_model(pose)

            # Make model available at top level of Model directory
            root_model_dir = path.join(self.model_dir, self.model_name)
            if not path.exists(root_model_dir):
                nested_model_dir = path.join(self.nested_dir, self.model_name)
                shutil.copytree(nested_model_dir, root_model_dir)

            if self.verbose >= 2:
                print("Spawned {} at (x={},y={},z={})".format(self.model_name,
                                                              x, y, z))

        return name if name is not None else "EMPTY", (numpy.pi, 0, yaw), pose

    def delete_models(self, instance_name=None):
        """Use class-wide instances attribute to delete models. 
        instance_name: if specified, deletes specific model [default: None]"""
        try:
            delete_model = rospy.ServiceProxy("/gazebo/delete_model",
                                              DeleteModel)
            if instance_name is None:
                for instance_name in self.instances.keys():
                    delete_model(instance_name)
                    del self.instances[instance_name]
            elif instance_name in self.instances:
                delete_model(instance_name)
                del self.instances[instance_name]
        except rospy.ServiceException as e:
            rospy.loginfo("Delete Model failed: {}\n{}".format(e, instances))
