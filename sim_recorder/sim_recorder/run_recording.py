import subprocess
import time
import os
import sys
import psutil
from multiprocessing import Process, Pipe, Queue, Event
import signal
import io
try:
    import proc_monitor
    import proc_monitor_gui
except ModuleNotFoundError:
    from . import proc_monitor
    from . import proc_monitor_gui

import threading
import _thread


def kill_proc_tree(pids, procs,interrupt_event, including_parent=False):
    interrupt_event.set()
    for pid in pids:
        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            if including_parent:
                parent.kill()
        except:
            pass
    time.sleep(2) # Wait for everything ot close to prevent broken_pipe
    for proc in procs[:-1]:
        proc.kill()
    time.sleep(2) # Wait for everything ot close to prevent broken_pipe


# Reference : https://stackoverflow.com/a/40281422
def interrupt_handler(interrupt_event):
    interrupt_event.wait()
    _thread.interrupt_main()


def run_com(w, q, com):
    os.dup2(w.fileno(), 1)
    proc = subprocess.Popen("exec " + com, shell=True)
    q.put(proc.pid)


def run_recorder(q, interrupt_event, simulator, idx, gui=False):
    task = threading.Thread(target=interrupt_handler, args=(interrupt_event,))
    task.start()
    try:
        if gui:
            proc_monitor_gui.run(simulator, idx=idx)  # launch recording
        else:
            proc_monitor.run(simulator,idx=idx)
    except:
        q.put("Exit")


def generate_procs(simulator, commands, r, w, q, interrupt_event, idx):
    procs = []
    for com in commands:
        procs.append(Process(target=run_com, args=(w, q, com), name=com))
    procs.append(Process(target=run_recorder, args=(
        q, interrupt_event, simulator, idx), daemon=True, name="Recorder"))
    return procs


def start_proces(delay, procs, q):
    pids = []
    delay.append(0) # Out of bound exception prevention
    delay.append(0) # Out of bound exception prevention
    for idx, p in enumerate(procs):
        p.start()
        time.sleep(delay[idx])

    for proc in range(len(procs)-1):
        pids.append(q.get())

    return pids


class Webots():
    def __init__(self):
        self.name = "webots"
        self.timeout = 30
        self.commands = [
            "ros2 launch webots_simple_arm pick_place.launch.py",
            "ros2 launch webots_simple_arm collision_webots.launch.py",
            "ros2 launch webots_simple_arm moveit_webots.launch.py",
        ]
        self.delays = [5,5]
class Gazebo():
    def __init__(self):
        self.name = "gazebo"
        self.timeout = 30
        self.commands = [
            "ros2 launch simple_arm gazebo.launch.py",
            "ros2 launch simple_move_group run_move_group.launch.py",
            "ros2 launch simple_arm collision_gazebo.launch.py",
            "ros2 launch simple_arm moveit_gazebo.launch.py",
        ]
        self.delays = [5, 5, 5]
class Ignition():
    def __init__(self):
        self.name = "ignition"
        self.timeout = 35
        self.commands = [
            "ros2 launch simple_arm ign_place.launch.py",
            "ros2 launch simple_move_group run_move_group.launch.py",
            "ros2 launch simple_arm moveit_ign.launch.py",
        ]
        self.delays = [1,5]
class GithubIgnition():
    def __init__(self):
        self.name = "github_ignition"
        self.timeout = 25
        self.commands = [
            "ros2 launch ign_moveit2 example_place.launch.py",
        ]
        self.delays = []
class WebotsThrow():
    def __init__(self):
        self.name = "webots_throw"
        self.timeout = 40
        self.commands = [
            "ros2 launch webots_simple_arm pick_place.launch.py",
            "ros2 launch webots_simple_arm throw_collision.launch.py",
            "ros2 launch webots_simple_arm throw_moveit.launch.py",
        ]
        self.delays = [5,5]
class GazeboThrow():
    def __init__(self):
        self.name = "gazebo_throw"
        self.timeout = 40
        self.commands = [
            "ros2 launch simple_arm gazebo.launch.py",
            "ros2 launch simple_move_group run_move_group.launch.py",
            "ros2 launch simple_arm throw_collision.launch.py",
            "ros2 launch simple_arm throw_moveit.launch.py",
        ]
        self.delays = [5, 5, 5]
class IgnitionThrow():
    def __init__(self):
        self.name = "ignition_throw"
        self.timeout = 30
        self.commands = [
            "ros2 launch simple_arm ign_throw.launch.py",
            "ros2 launch simple_move_group run_move_group.launch.py",
            "ros2 launch simple_arm ign_throw_moveit.launch.py",
        ]
        self.delays = [1,5]
class GithubIgnitionThrow():
    def __init__(self):
        self.name = "github_ignition_throw"
        self.timeout = 25
        self.commands = [
            "ros2 launch ign_moveit2 example_throw.launch.py",
        ]
        self.delays = []

def handler(signum, frame):
    raise Exception("TimeOut")

def run(sim, idx):
    path = "/home/ubb/Documents/PersonalProject/VrController/sim_recorder/data/"
    r, w = Pipe()
    q = Queue()
    reader = os.fdopen(r.fileno(), 'r')
    interrupt_event = Event()
    procs = generate_procs(sim.name, sim.commands, r, w, q, interrupt_event, idx)
    time.sleep(1)
    pids = start_proces(sim.delays, procs, q)
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(sim.timeout)
    start_time = time.time()
    with open(path+f"{sim.name}/log/{idx}.txt", "w") as f,\
         open(path+f"{sim.name}/run.txt", "a") as out:
        try:    
            while True:
                text = reader.readline()
                f.write(text)
                if "Task completed Succesfully" in text or "ODE INTERNAL ERROR" in text:
                    print(f"Completed for {idx} in {time.time() - start_time }")
                    out.write(f"Completed for {idx} in {time.time() - start_time }\n")
                    signal.alarm(0)
                    kill_proc_tree(pids, procs, interrupt_event)
                    return 1,0
                if "Cube is not in bound" in text:
                    print(f"Failed for {idx} in {time.time() - start_time }")
                    out.write(f"Failed for {idx} in {time.time() - start_time }\n")
                    signal.alarm(0)
                    kill_proc_tree(pids, procs, interrupt_event)
                    return 0,1
        except:
            print(f"Timeout for {idx}")
            out.write(f"Timeout for {idx}\n")
            f.write("Timeout")
            kill_proc_tree(pids, procs, interrupt_event)
            return 0,0
            

def main(args=None):
    succ = 0
    fail = 0
    if len(sys.argv) == 1:
        raise Exception("Missing arguments")
    if sys.argv[1] == "webots":
        sim = Webots()
    elif sys.argv[1] == "webots_throw":
        sim = WebotsThrow()
    elif sys.argv[1] == "gazebo":
        sim = Gazebo()
    elif sys.argv[1] == "gazebo_throw":
        sim = GazeboThrow()
    elif sys.argv[1] == "github_ignition":
        sim = GithubIgnition()
    elif sys.argv[1] == "github_ignition_throw":
        sim = GithubIgnitionThrow()
    elif sys.argv[1] == "ignition":
        sim = Ignition()
    elif sys.argv[1] == "ignition_throw":
        sim = IgnitionThrow()

    if len(sys.argv) == 3:
        iteration = int(sys.argv[2])
    else:
        iteration = 1
    path = "/home/ubb/Documents/PersonalProject/VrController/sim_recorder/data/"
    try:
        os.mkdir(path+f"{sim.name}")
        os.mkdir(path+f"{sim.name}/log")
        os.mkdir(path+f"{sim.name}/ram")
        os.mkdir(path+f"{sim.name}/cpu")
    except Exception as e:
        print(e)
        print("Folder exist. Overwriting...")
    if os.path.exists(path+f"{sim.name}/run.txt"):
        os.remove(path+f"{sim.name}/run.txt")

    for idx in range(iteration):
        a, b = run(sim, idx)
        succ += a
        fail += b
    print(f"Success {succ}; Failure {fail}; Timeout {iteration-(succ + fail)}")


if __name__ == "__main__":
    main()
