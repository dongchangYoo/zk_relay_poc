import json
import os
import subprocess
import toml
from hashlib import sha256

from zokrates_wrapper.utils import encode_zokrates_input, padding, double_hash_as_little, hex_to_word_array

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

    block645120 = "00e0ff2fd98ebb2a6aba647793c8851db51c9e79712332ca669a04000000000000000000a3e1762af56223c68eab02df4f65c6e982118f1a4aed87393ad553a221738a2d8b7b435fea071017acc0cd5c"
    block645134 = "00e0ff3f38d2e594d34003865fb5d1792fcd2ec48ce3e68a4fd100000000000000000000b6b5a4db44ffb0f3ebbaadc6defe39d19f0356f1e86ac76312e8fd4cde8691300a28565fea0710174c711a2e"
    block647135 = "00000020b12693ef5d5e06d1a8f989f7b3b50eaa1f9ea2deecc00e0000000000000000000450368c5f84ae83ecb8e7f59096a11dd85c4664dea2990f4302edcae1957ac94b2a565fea071017345cf613"
    block647136 = "0000402006ab8f2d0115e32b99b9ca020c8ed149aa5c92aac75706000000000000000000f25a11bb8e935667a49e32e9247aca7f9d63a7c1e506891e16fa41680c5e2b76282c565f123a101749e4a793"

    epoch_head_time = block645120[-24:-16]
    epoch_head_bits = block645120[-16:-8]
    epoch_tail_time = block647135[-24:-16]
    next_epoch_head_bits = block647136[-16:-8]
    print(epoch_head_time)
    print(epoch_tail_time)
    print(epoch_head_bits)
    print(next_epoch_head_bits)

    encoded_input = list()
    encoded_input.append(int(epoch_head_time, 16))
    encoded_input.append(int(epoch_head_bits, 16))
    encoded_input.append(int(epoch_tail_time, 16))

    zk.integrated_setup()
    zk.prove(encoded_input)



    # f2_prev_hash = [double_hash_as_little(block645134)[0:32], double_hash_as_little(block645134)[32:64]]
    # u32_32_intermediate_blocks = hex_to_word_array(padding(block647135))
    # f5_final_block = [block647136[0:32], block647136[32:64], block647136[64:96], block647136[96: 128], block647136[128:160]]
    #
    # encoded_input = list()
    # encoded_input.append(int(epoch_head_time_and_bits, 16))
    # encoded_input += [int(item, 16) for item in f2_prev_hash]
    # encoded_input += u32_32_intermediate_blocks
    # encoded_input += [int(item, 16) for item in f5_final_block]


    # epoch_head = block645120[-32:]
    # epoch_tail = block647135[-32:]
    # next_epoch_head = block647136[-32:]
    #
    # encoded_input = list()
    # encoded_input.append(int(epoch_head, 16))
    # encoded_input.append(int(epoch_tail, 16))
    # encoded_input.append(int(next_epoch_head, 16))

    # encoded_input = list()
    # encoded_input.append(0xffff * 256 ** (0x1d - 3))
    # zk.integrated_setup()
    # zk.prove(encoded_input)
    # with open("../data/proof/proof.json") as json_data:
    #     inputs = json.load(json_data)["inputs"]

    # print(" r: {}".format(inputs[1]))
    # print(" q: {}".format(inputs[2]))
    # print("qq: {}".format(hex(0xffff * 256 ** (0x1d - 3) // 1209600)))
    # if int(inputs[2], 16) == 0xffff * 256 ** (0x1d - 3) // 1209600:
    #     print("true")
    # else:
    #     print("false")

    # zk.export_verifier()
