import json
import os
import subprocess
from unittest import TestCase

import toml

PROVING_SCHEME = ["g16", "pghr13", "gm17", "marli"]


class Zokrates:
    def __init__(self, config_path: str):
        self.config = toml.load(config_path)
        context = self.config["context"]
        root_dir = context["ROOT_DIR"]

        ctx_code = context["code"]
        self.code_dir = root_dir + ctx_code["CODE_DIR"]
        self.code_path = self.code_dir + ctx_code["CODE_FILE_NAME"]

        ctx_data = context["data"]
        self.data_dir = root_dir + ctx_data["DATA_DIR"]
        self.prog_path = self.data_dir + ctx_data["PROGRAM_FILE_NAME"]
        self.abi_path = self.data_dir + ctx_data["ABI_FILE_NAME"]
        self.vkey_path = self.data_dir + ctx_data["VKEY_FILE_NAME"]
        self.pkey_path = self.data_dir + ctx_data["PKEY_FILE_NAME"]
        self.witness_path = self.data_dir + ctx_data["WITNESS_FILE_NAME"]
        self.proof_path = self.data_dir + ctx_data["PROOF_FILE_NAME"]

        self.proving_scheme = context["PROVING_SCHEME_NAME"]
        if self.proving_scheme not in PROVING_SCHEME:
            raise Exception("Unknown proving_scheme: {}".format(self.proving_scheme))

        ctx_contract = context["contract"]
        self.contract_dir = root_dir + ctx_contract["CONTRACT_DIR"]
        self.verifier_contract_path = self.contract_dir + ctx_contract["CONTRACT_FILE_NAME"]

        self.zokrates_bin_path = self.config["zokrates"]["BIN_PATH"]
        self.zokrates_std_lib_path = self.config["zokrates"]["STDLIB_PATH"]

    # TODO need?
    def change_code(self, file_name: str):
        self.code_path = self.code_dir + file_name

    def integrated_setup(self):
        self.compile()
        self.setup()

    def prove(self, *args):
        self.compute_witness(*args)
        self.generate_proof()

    def compile(self) -> str:
        # set zokrates command
        cmd = [self.zokrates_bin_path, "compile"]

        # set zokrates code path
        Zokrates.mk_dir(self.code_dir)
        cmd += ["-i", self.code_path]

        # set r1cs program path
        Zokrates.mk_dir(self.data_dir)
        cmd += ["-o", self.prog_path]
        cmd += ["-s", self.abi_path]

        # set standard library path
        cmd += ["--stdlib-path", self.zokrates_std_lib_path]

        # run the command
        return Zokrates.run_zokrates("compile", cmd)

    def setup(self) -> str:
        # set zokrates command
        cmd = [self.zokrates_bin_path, "setup"]

        # set r1cs program path
        cmd += ["-i", self.prog_path]

        # set output files path
        Zokrates.mk_dir(self.data_dir)
        cmd += ["-p", self.pkey_path]
        cmd += ["-v", self.vkey_path]

        # select proving scheme
        cmd += ["-s", self.proving_scheme]

        # run the command
        return Zokrates.run_zokrates("setup", cmd)

    def compute_witness(self, *args) -> str:
        # set zokrates command
        cmd = [self.zokrates_bin_path, "compute-witness"]

        # set r1cs program path
        cmd += ["-i", self.prog_path]

        # set witness path
        Zokrates.mk_dir(self.data_dir)
        cmd += ["-o", self.witness_path]

        # set and encode input
        encoded = list()
        for arg in args:
            if isinstance(arg, int):
                encoded.append(str(arg))
            elif isinstance(arg, list):
                encoded += [str(item) for item in arg]
            else:
                raise Exception("Invalid Input: {}".format(arg))

        cmd += ["-a"] + encoded

        # run the command
        return Zokrates.run_zokrates("compute_witness", cmd)

    def generate_proof(self) -> str:
        # set zokrates command
        cmd = [self.zokrates_bin_path, "generate-proof"]

        # set r1cs program path
        cmd += ["-i", self.prog_path]

        # set parameters
        cmd += ["-p", self.pkey_path]
        cmd += ["-w", self.witness_path]
        cmd += ["-s", self.proving_scheme]
        cmd += ["-j", self.proof_path]

        # run the command
        return Zokrates.run_zokrates("generate_proof", cmd)

    def export_verifier(self, curve_name: str = "bn128") -> str:
        # set zokrates command
        cmd = [self.zokrates_bin_path, "export-verifier"]

        # set parameters
        cmd += ["-i", self.vkey_path]
        cmd += ["-s", self.proving_scheme]
        cmd += ["-c", curve_name]

        # set verifier contract path
        Zokrates.mk_dir(self.contract_dir)
        cmd += ["-o", self.verifier_contract_path]

        # run the command
        return Zokrates.run_zokrates("export_verifier", cmd)

    @staticmethod
    def mk_dir(dir_path: str):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    @staticmethod
    def run_zokrates(cmd_name: str, cmd: list) -> str:
        # print(">> {} starts".format(cmd_name))
        return_obj = subprocess.run(cmd, stdout=subprocess.PIPE)
        if return_obj.returncode != 0:
            raise Exception(cmd_name + " error")
        return return_obj.stdout.hex()


class ZokratesTest(TestCase):
    def setUp(self) -> None:
        config_path = "test_config.toml"
        self.zok = Zokrates(config_path)

        Zokrates.mk_dir("./test_data")
        with open("./test_data/example.zok", "w") as f:
            f.write("""
def main(private field a, field b) -> bool:
    return a * a == b
        """)

    def tearDown(self) -> None:
        """ remove all test files and directory at the end of the test"""
        test_path = "./test_data"
        if os.path.exists(test_path):
            files = os.listdir("./test_data")
            for file in files:
                os.remove(test_path + "/" + file)
            os.rmdir("./test_data/")

    def test_compile(self):
        """ raises exception in each process when the process fails """
        self.zok.compile()
        self.zok.setup()
        self.zok.compute_witness(337, 113569)
        self.zok.generate_proof()
        self.zok.export_verifier()
