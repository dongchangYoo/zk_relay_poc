import json
import os
import subprocess
import toml


"""
<Data architecture>

functions
- compile(code.zok) -> program
- setup(program) -> key-pair
- compute witness(program, input) -> witness
- generate proof(witness, proving-key) -> proof.json
- export verifier(verification.key) -> verifier.sol

data
- code.zok
- program
- verification.key
- proving.key
- witness
- proof.json
- verifier.sol
- zokrates binary
"""


class Zokrates:
    def __init__(self, config_path: str):
        self.config = toml.load(config_path)
        context = self.config["context"]

        program_root_dir = context["ROOT_DIR"]
        program_ctx = context["program"]
        self.code_dir = program_root_dir + program_ctx["CODE_DIR"]
        self.code_path = self.code_dir + program_ctx["CODE_FILE_NAME"]
        self.prog_path = self.code_dir + program_ctx["PROGRAM_FILE_NAME"]

        setup_ctx = context["setup"]
        self.setup_dir = program_root_dir + setup_ctx["SETUP_DIR"]
        self.vkey_path = self.setup_dir + setup_ctx["VKEY_FILE_NAME"]
        self.pkey_path = self.setup_dir + setup_ctx["PKEY_FILE_NAME"]

        proof_ctx = context["proof"]
        self.proof_dir = program_root_dir + proof_ctx["PROOF_DIR"]
        self.witness_path = self.proof_dir + proof_ctx["WITNESS_FILE_NAME"]
        self.proof_path = self.proof_dir + proof_ctx["PROOF_FILE_NAME"]

        verify_ctx = context["verify"]
        self.verifier_dir = program_root_dir + verify_ctx["VERIFICATION_DIR"]
        self.verifier_contract_path = self.verifier_dir + verify_ctx["CONTRACT_FILE_NAME"]

        self.zokrates_bin_path = self.config["zokrates"]["BIN_PATH"]
        self.zokrates_std_lib_path = self.config["zokrates"]["STDLIB_PATH"]

    def compile(self):
        cmd = [self.zokrates_bin_path, "compile"]
        cmd += ["-i", self.code_path]
        if not os.path.exists(self.proof_dir):
            os.mkdir(self.proof_dir)
        cmd += ["-o", self.proof_path]
        cmd += ["--stdlib-path", self.zokrates_std_lib_path]

        print(">> Compile the program to r1cs form.")
        result = subprocess.run(cmd)
        return result

    # def setup(self, program_path: str):


if __name__ == "__main__":
    zk = Zokrates("../conf/config.toml")
    zk.compile()
