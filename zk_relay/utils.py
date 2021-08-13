from hashlib import sha256
from typing import Union


# useful
def double_hash_as_little(pre: Union[str, bytes]) -> str:
    if isinstance(pre, str):
        pre = bytes.fromhex(pre)
    elif not isinstance(pre, bytes):
        raise Exception("pre-image should has bytes or str types")
    return sha256(sha256(pre).digest()).digest().hex()


# useful
def double_hash_as_big(pre: str) -> str:
    hash_little = double_hash_as_little(pre)
    return bytes.fromhex(hash_little)[::-1].hex()


# necessary
def split_hex_to_int_array(target: str, unit_byte_len: int) -> list:
    unit_hex_len = unit_byte_len * 2
    if target.startswith("0x"):
        target = target[2:]
    ret = list()
    for i in range(len(target) // unit_hex_len):
        parsed_int = int(target[i * unit_hex_len:(i + 1)*unit_hex_len], 16)
        ret.append(parsed_int)
    return ret


# necessary
def padding(value: str):
    bit_len = len(value) * 4
    # determine number of blocks
    num_blocks = bit_len // 512 + 2 if bit_len % 512 > 448 else bit_len // 512 + 1

    # set length suffix
    bit_len_hex = hex(bit_len)[2:]
    bit_len_hex = "0" + bit_len_hex if len(bit_len_hex) % 2 == 1 else bit_len_hex

    # determine number of zero-bytes
    zeros = (num_blocks * 512 - bit_len - 8 - len(bit_len_hex) * 4) // 8

    return value[:] + "80" + "00" * zeros + bit_len_hex


# necessary
def convert_endian(value: Union[int, bytes, str]) -> Union[int, bytes, str]:
    if isinstance(value, int):
        target = bytes.fromhex(hex(value)[2:])
        return int(target[::-1].hex(), 16)
    elif isinstance(value, bytes):
        target = value
        return target[::-1]
    elif isinstance(value, str):
        target = bytes.fromhex(value)
        return target[::-1].hex()
    else:
        raise Exception("Expected type of input {}, but {}".format("Union[int, bytes, str]", type(value)))
