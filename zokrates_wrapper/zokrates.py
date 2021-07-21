import json
import os
import subprocess


class Zokrates:
    def __init__(self, zokrates_bin_path: str = None, zokrates_stdlib_path: str = None, out_dir: str = None):
        with open("../conf/zk_relay_config.json", "r") as json_data:
            config = json.load(json_data)
            if zokrates_bin_path is None:
                self.zokrates_bin_path = config["zokrates_bin_path"]
            if zokrates_stdlib_path is None:
                self.zokrates_stdlib_path = config["zokrates_stdlib_path"]
            if out_dir is None:
                if not os.path.exists("../out"):
                    os.mkdir("../out")
                self.out_dir = "../out/"
        self.basic_cmd = self.zokrates_bin_path + "/zokrates"

    def compile(self, file_path: str):
        cmd = [self.basic_cmd, "compile"]
        cmd += ["-i", file_path]
        cmd += ["-o", self.out_dir + "program"]
        cmd += ["--stdlib-path", self.zokrates_stdlib_path]

        print(">> Compile the program to r1cs form.")
        result = subprocess.run(cmd)
        return result

    # def setup(self, program_path: str):

if __name__ == "__main__":
    zk = Zokrates()
    zk.compile("../test/root.zok")