import json
import os
import subprocess
import toml

from zk_relay.libs.bitcoin_header import Header
from zokrates_libs.utils import convert_endian

PROVING_SCHEME = ["g16", "pghr13", "gm17", "marli"]
DEBUG_MODE = True


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

    @staticmethod
    def mk_dir(dir_path: str):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    @staticmethod
    def run_zokrates(cmd_name: str, cmd: list, debug: bool = False):
        print(">> {} starts".format(cmd_name))
        if debug:
            if subprocess.run(cmd).returncode != 0:
                raise Exception(cmd_name + " error")
        else:
            if subprocess.run(cmd, stdout=subprocess.PIPE).returncode != 0:
                raise Exception(cmd_name + " error")
        return True

    def integrated_setup(self):
        self.compile()
        self.setup()

    def prove(self, *args):
        self.compute_witness(*args)
        self.generate_proof()

    def compile(self):
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
        Zokrates.run_zokrates("compile", cmd, DEBUG_MODE)

    def setup(self):
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
        Zokrates.run_zokrates("setup", cmd, DEBUG_MODE)

    def compute_witness(self, *args):
        # set zokrates command
        cmd = [self.zokrates_bin_path, "compute-witness"]

        # set r1cs program path
        cmd += ["-i", self.prog_path]

        # set witness path
        Zokrates.mk_dir(self.proof_dir)
        cmd += ["-o", self.witness_path]

        # set and encode input
        cmd += ["-a"] + [str(item) for item in args[0]]

        # run the command
        Zokrates.run_zokrates("compute_witness", cmd, DEBUG_MODE)

    def generate_proof(self):
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
        Zokrates.run_zokrates("generate_proof", cmd, DEBUG_MODE)

    def export_verifier(self, curve_name: str = "bn128"):
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
        Zokrates.run_zokrates("export_verifier", cmd, DEBUG_MODE)


if __name__ == "__main__":
    zk = Zokrates("../conf/config.toml")

    header645120 = Header.from_raw_str("00e0ff2fd98ebb2a6aba647793c8851db51c9e79712332ca669a04000000000000000000a3e1762af56223c68eab02df4f65c6e982118f1a4aed87393ad553a221738a2d8b7b435fea071017acc0cd5c")
    header645134 = Header.from_raw_str("00e0ff3f38d2e594d34003865fb5d1792fcd2ec48ce3e68a4fd100000000000000000000b6b5a4db44ffb0f3ebbaadc6defe39d19f0356f1e86ac76312e8fd4cde8691300a28565fea0710174c711a2e")
    header647135 = Header.from_raw_str("00000020b12693ef5d5e06d1a8f989f7b3b50eaa1f9ea2deecc00e0000000000000000000450368c5f84ae83ecb8e7f59096a11dd85c4664dea2990f4302edcae1957ac94b2a565fea071017345cf613")
    header647136 = Header.from_raw_str("0000402006ab8f2d0115e32b99b9ca020c8ed149aa5c92aac75706000000000000000000f25a11bb8e935667a49e32e9247aca7f9d63a7c1e506891e16fa41680c5e2b76282c565f123a101749e4a793")

    epoch_head_time = header645120.time
    epoch_head_bits = header645120.bits
    epoch_tail_time = header647135.time
    next_epoch_head_bits = header647136.bits

    print("<expected>")
    print(" - ct: {}".format(header645120.target))
    print(" - td: {}".format(header647135.time - header645120.time))
    print(" - ut: {}".format(hex(header645120.target * (header647135.time - header645120.time) // 1209600)))

    encoded_input = list()
    encoded_input.append(convert_endian(epoch_head_time))
    encoded_input.append(convert_endian(epoch_head_bits))
    encoded_input.append(convert_endian(epoch_tail_time))

    # zk.integrated_setup()
    zk.prove(encoded_input)
