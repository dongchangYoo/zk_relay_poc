import os
import subprocess
import toml

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
        cmd += ["-a"] + [str(arg) for arg in args]

        print(">> compute_witness")
        if subprocess.run(cmd, stdout=subprocess.PIPE).returncode != 0:
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
    zk.integrated_setup()
    # zk.prove(337, 113569)
    # zk.export_verifier()

    # print("validate.zok".format(i=0))
