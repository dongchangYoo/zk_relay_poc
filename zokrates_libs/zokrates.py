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

        code_ctx = context["code"]
        self.code_dir = root_dir + code_ctx["CODE_DIR"]
        self.code_path = self.code_dir + code_ctx["CODE_FILE_NAME"]

        prog_ctx = context["program"]
        self.prog_dir = root_dir + prog_ctx["PROGRAM_DIR"]
        self.prog_path = self.prog_dir + prog_ctx["PROGRAM_FILE_NAME"]
        self.abi_path = self.prog_dir + prog_ctx["ABI_FILE_NAME"]

        setup_ctx = context["setup"]
        self.setup_dir = root_dir + setup_ctx["SETUP_DIR"]
        self.vkey_path = self.setup_dir + setup_ctx["VKEY_FILE_NAME"]
        self.pkey_path = self.setup_dir + setup_ctx["PKEY_FILE_NAME"]
        self.proving_scheme = setup_ctx["PROVING_SCHEME_NAME"]
        if self.proving_scheme not in PROVING_SCHEME:
            raise Exception("Unknown proving_scheme: {}".format(self.proving_scheme))

        proof_ctx = context["proof"]
        self.proof_dir = root_dir + proof_ctx["PROOF_DIR"]
        self.witness_path = self.proof_dir + proof_ctx["WITNESS_FILE_NAME"]
        self.proof_path = self.proof_dir + proof_ctx["PROOF_FILE_NAME"]

        verify_ctx = context["verify"]
        self.verifier_dir = root_dir + verify_ctx["VERIFICATION_DIR"]
        self.verifier_contract_path = self.verifier_dir + verify_ctx["CONTRACT_FILE_NAME"]

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
        Zokrates.mk_dir(self.prog_dir)
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
        Zokrates.mk_dir(self.setup_dir)
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
        Zokrates.mk_dir(self.proof_dir)
        cmd += ["-o", self.witness_path]

        # set and encode input
        cmd += ["-a"] + [str(item) for item in args]

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
        Zokrates.mk_dir(self.verifier_dir)
        cmd += ["-o", self.verifier_contract_path]

        # run the command
        return Zokrates.run_zokrates("export_verifier", cmd)

    @staticmethod
    def mk_dir(dir_path: str):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

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