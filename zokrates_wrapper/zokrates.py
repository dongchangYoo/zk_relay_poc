import os
import subprocess
import toml
from hashlib import sha256

from zokrates_wrapper.utils import encode_zokrates_input, padding

PROVING_SCHEME = ["g16", "pghr13", "gm17", "marli"]


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
        self.proving_scheme = setup_ctx["PROVING_SCHEME_NAME"]
        if self.proving_scheme not in PROVING_SCHEME:
            raise Exception("Unknown proving_scheme: {}".format(self.proving_scheme))

        proof_ctx = context["proof"]
        self.proof_dir = program_root_dir + proof_ctx["PROOF_DIR"]
        self.witness_path = self.proof_dir + proof_ctx["WITNESS_FILE_NAME"]
        self.proof_path = self.proof_dir + proof_ctx["PROOF_FILE_NAME"]

        verify_ctx = context["verify"]
        self.verifier_dir = program_root_dir + verify_ctx["VERIFICATION_DIR"]
        self.verifier_contract_path = self.verifier_dir + verify_ctx["CONTRACT_FILE_NAME"]

        self.zokrates_bin_path = self.config["zokrates"]["BIN_PATH"]
        self.zokrates_std_lib_path = self.config["zokrates"]["STDLIB_PATH"]

    def integrated_setup(self):
        self.compile()
        self.setup()

    def prove(self, *args):
        self.compute_witness(*args)
        self.generate_proof()

    def compile(self):
        cmd = [self.zokrates_bin_path, "compile"]
        cmd += ["-i", self.code_path]
        if not os.path.exists(self.code_dir):
            os.mkdir(self.code_dir)
        cmd += ["-o", self.prog_path]
        cmd += ["--stdlib-path", self.zokrates_std_lib_path]

        print(">> Compile the program to r1cs form.")
        # if subprocess.run(cmd, stdout=subprocess.PIPE).returncode != 0:
        #     raise Exception("[err] compile error")
        if subprocess.run(cmd).returncode != 0:
            raise Exception("[err] compile error")
        return True

    def setup(self):
        cmd = [self.zokrates_bin_path, "setup"]
        cmd += ["-i", self.prog_path]
        if not os.path.exists(self.setup_dir):
            os.mkdir(self.setup_dir)
        cmd += ["-p", self.pkey_path]
        cmd += ["-v", self.vkey_path]
        cmd += ["-s", self.proving_scheme]

        print(">> Setup")
        if subprocess.run(cmd, stdout=subprocess.PIPE).returncode != 0:
            raise Exception("[err] setup error")
        return True

    def compute_witness(self, *args):
        cmd = [self.zokrates_bin_path, "compute-witness"]
        cmd += ["-i", self.prog_path]
        if not os.path.exists(self.proof_dir):
            os.mkdir(self.proof_dir)
        cmd += ["-o", self.witness_path]
        cmd += ["-a"] + [str(item) for item in args[0]]

        print(">> compute_witness")
        if subprocess.run(cmd).returncode != 0:
            raise Exception("[err] compute_witness error")
        return True

    def generate_proof(self):
        cmd = [self.zokrates_bin_path, "generate-proof"]
        cmd += ["-i", self.prog_path]
        cmd += ["-p", self.pkey_path]
        cmd += ["-w", self.witness_path]
        cmd += ["-s", self.proving_scheme]
        if not os.path.exists(self.proof_dir):
            os.mkdir(self.proof_dir)
        cmd += ["-j", self.proof_path]

        print(">> generate_proof")
        if subprocess.run(cmd, stdout=subprocess.PIPE).returncode != 0:
            raise Exception("[err] generate_proof error")
        return True

    def export_verifier(self, curve_name: str = "bn128"):
        cmd = [self.zokrates_bin_path, "export-verifier"]
        cmd += ["-i", self.vkey_path]
        cmd += ["-s", self.proving_scheme]
        cmd += ["-c", curve_name]
        if not os.path.exists(self.verifier_dir):
            os.mkdir(self.verifier_dir)
        cmd += ["-o", self.verifier_contract_path]

        print(">> export_verifier")
        if subprocess.run(cmd, stdout=subprocess.PIPE).returncode != 0:
            raise Exception("[err] export_verifier error")
        return True


if __name__ == "__main__":
    zk = Zokrates("../conf/config.toml")

    block0 = "0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c"
    block1 = "010000006fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000982051fd1e4ba744bbbe680e1fee14677ba1a3c3540bf7b1cdb606e857233e0e61bc6649ffff001d01e36299"
    block2 = "010000004860eb18bf1b1620e37e9490fc8a427514416fd75159ab86688e9a8300000000d5fdcc541e25de1c7a5addedf24858b8bb665c9f36ef744ee42c316022c90f9bb0bc6649ffff001d08d2bd61"

    reference_target = block1[-16:-8]
    prev_hash = sha256(sha256(bytes.fromhex(block0)).digest()).digest().hex()
    target_block = padding(block1)

    encoded_input = encode_zokrates_input(reference_target, prev_hash, target_block)

    zk.integrated_setup()
    zk.prove(encoded_input)
    # zk.export_verifier()




    # first_block_epoch = block0[-32:]  # 128
    # prev_block_hash = double_hash(block0)  # 256
    # intermediate_blocks = block1  # 640
    # final_block = block2  # 640
    #
    # encoded_input = encode_zokrates_input(first_block_epoch, prev_block_hash, intermediate_blocks, final_block)
