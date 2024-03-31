from pathlib import Path
import time
import psutil
import os

from stegl.logging import print_log

class ProcessCapture:
    """Launches a process and keeps track of all running derived processes using
    a custom-set environment variable."""

    COUNTER = 0

    def __init__(
        self,
        exe_path : str,
        args = [],
        max_launch_waiting  : int = 10,
        min_launch_stable   : int = 3,
        termination_timeout : int = 5,
        termination_retries : int = 3
    ):
        self.exe_path = exe_path
        self.args = args
        self.max_launch_waiting = max_launch_waiting
        self.min_launch_stable = min_launch_stable
        self.termination_timeout = termination_timeout
        self.termination_retries = termination_retries
        
        self.root_pid = psutil.Process().pid # PID of the python process
        self.ID = f"STEGL_{self.root_pid}_{ProcessCapture.COUNTER}"
        self.launched = False
        
        ProcessCapture.COUNTER += 1
    
    def launch(self):
        if self.launched:
            raise RuntimeError("ProcessCapture can only be launched once. Create a new instance.")
        try:
            print_log(f"Running {repr(Path(self.exe_path).name)} using STEGL ID {repr(self.ID)}.")
            os.environ[self.ID] = str(time.time())
            psutil.Popen([self.exe_path] + self.args)

            # Perform "launch waiting" - observe child processes and wait until
            # a stable state was reached (e.g. the PIDs dont change any more).
            print_log("Waiting for stable process-tree: ", end="")
            stable_counter = 0
            pid_set = set(p.pid for p in self.find_descendent_processes())
            for _ in range(self.max_launch_waiting):
                time.sleep(1)
                new_pid_set = set(p.pid for p in self.find_descendent_processes())
                diff = pid_set.difference(new_pid_set)
                if not diff:
                    stable_counter += 1
                    print_log(stable_counter, end=" ")
                    if stable_counter >= self.min_launch_stable:
                        break
                else:
                    stable_counter = 0
                    print_log("X", end=" ")
                pid_set = new_pid_set
            print_log("")

            if stable_counter < self.min_launch_stable:
                print_log("Max. waiting time reached. Assuming launched.")
        except:
            raise
        finally:
            self.launched = True

    def find_descendent_processes(self):

        # Derived processes will inherit the STEGL_PID value,
        # and therefore can be identified by it
        processes = [p for p in psutil.process_iter(["environ"]) 
                     if (p.info["environ"] is not None) and (self.ID in p.info["environ"]) and (self.root_pid != p.pid)]
        return processes
    
    def terminate(self):

        print_log(f"Launch group with STEGL ID {repr(self.ID)} is terminating:", end=" ")
        # Running multiple loops, as sometimes processes are restarted
        # by other processes and might be missed
        for _ in range(self.termination_retries):

            # Try to kill oldest process first, as this is most likely the main one,
            # which would also be restarting the child processes
            processes = sorted(self.find_descendent_processes(), key=lambda p: p.create_time())
            if len(processes) == 0:
                print_log("Done.")
                return
            
            print_log(".", end="")
            
            for p in processes:
                p.suspend()
            for p in processes:
                if p.is_running():
                    p.terminate()
                try:
                    p.wait(self.termination_timeout)
                except psutil.TimeoutExpired:
                    # Last resort
                    p.kill()
        
        processes = self.find_descendent_processes()
        if len(processes) > 0:
            raise RuntimeError(f"Termination failed after {self.termination_retries} repetitions.")

    def wait_for_termination(self, timeout=None):
        psutil.wait_procs(
            self.find_descendent_processes(),
            timeout=timeout
        )


class ExternalGame:
    def __init__(
        self,
        game_search_paths,
        game_starter : ProcessCapture,
        dependencies : ProcessCapture = [],
        game_search_timeout : int = 30,
        after_game_wait : int = 10
    ):
        self.game_search_paths = game_search_paths
        self.game_starter = game_starter
        self.dependencies = dependencies
        self.game_search_timeout = game_search_timeout
        self.after_game_wait = after_game_wait

    def _process_in_searchpaths(self, process):
        if not process.is_running():
            return False
        exe_path = process.exe()
        if exe_path is None:
            return False
        return any(Path(exe_path).is_relative_to(sp) for sp in self.game_search_paths)

    def _search_game_process(self):
        processes = self.game_starter.find_descendent_processes()
        return next((p for p in processes if self._process_in_searchpaths(p)), None)

    def terminate(self):
        for dep in reversed(self.dependencies + [self.game_starter]):
            try:
                dep.terminate()
            except RuntimeError as e:
                # TODO: Log
                pass

    def run(self):
        if len(self.dependencies) > 0:
            print_log("Launching game dependencies.")
        for dep in self.dependencies:
            dep.launch()
        
        print_log("Launching game.")
        self.game_starter.launch()
        
        # Wait until a game-process was found
        print_log("Waiting for game process.", end=" ")
        game_process = None
        for _ in range(self.game_search_timeout):
            game_process = self._search_game_process()
            if game_process is not None:
                print_log("")
                break
            print_log(".", end="")
            time.sleep(1)

        if game_process is not None:
            print_log(f"Detected game process with PID {game_process.pid}.")
            print_log("Waiting for game to terminate.")
        else:
            print_log("No game process could be detected!")

        while game_process is not None:
            game_process.wait()
            # Wait for a short moment to make sure that pot. child-processes
            # are ready to be detected (it could happen that the original process
            # immediately launches another and closes)
            time.sleep(1)
            game_process = self._search_game_process()

        print_log("No more game process found.")
        print_log(f"Waiting for {self.after_game_wait} seconds (after_game_wait).")
        time.sleep(self.after_game_wait)

        print_log("Stopping remaining processes & dependencies.")

        # Will start with the game started and than
        # walk backwards through the dependencies
        self.terminate()

        print_log("Success.")
