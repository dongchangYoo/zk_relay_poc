
def pack_max_variance(length: int):
    if length > 32:
        return 0
    return 2 ** (length * 4) - 1


def get_hex_length(bits: int):
    bit_length = bits.bit_length()
    return bit_length // 4 if bit_length % 4 == 0 else bit_length // 4 + 1


def bits_to_target(bits: int) -> int:
    # seperate exponent and coefficient
    exp = (bits & 0xff000000) >> 24
    coef = bits & 0x00ffffff
    # calculate and return target
    target = coef * 256 ** (exp - 3)
    return target


def pack_target(bits: int):
    exp = (bits & 0xff000000) >> 6
    coef = (bits & 0x00ffffff)
    return coef << (8 * exp + 152)


def to_big_endian(bits: int) -> int:
    return (bits & 0xff000000) >> 24 & (bits & 0x00ff0000) >> 8 & (bits & 0x0000ff00) << 8 & (bits & 0x000000ff) << 24


def validate_target(epoch_head: str, epoch_tail: str, next_epoch_head: str):
    time_head = int.from_bytes(bytes.fromhex(epoch_head[8:16])[::-1], byteorder="big")
    time_tail = int.from_bytes(bytes.fromhex(epoch_tail[8:16])[::-1], byteorder="big")

    epoch_head_bits = int.from_bytes(bytes.fromhex(epoch_head[16:24])[::-1], byteorder="big")
    next_epoch_head_bits = int.from_bytes(bytes.fromhex(next_epoch_head[16:24])[::-1], byteorder="big")

    time_delta = time_tail - time_head
    target_time_delta = 1209600  # 2016 * 600 (time interval of 10 minutes)

    current_target = pack_target(epoch_head_bits)
    current_target = bits_to_target(epoch_head_bits)
    target = current_target * time_delta  # target_time_delta

    encoded_target = pack_target(next_epoch_head_bits)
    encoded_target_extended = encoded_target * target_time_delta

    max_variance = pack_max_variance(get_hex_length(target) - get_hex_length(next_epoch_head_bits & 0xffffff))

    target = 95832923060582736897701037735936000 if target > 95832923060582736897701037735936000 else target
    delta = target - encoded_target_extended
    delta = delta if target >= encoded_target_extended else max_variance + 1
    valid = True if delta <= max_variance else False
    return valid, current_target


def target_floor(target: int):
    byte_len = len(bytes.fromhex(hex(target)[2:]))
    first_mask = 0xff * 256 ** (byte_len - 1)
    first_byte = (target & first_mask) / 256 ** (byte_len - 1)

    coef_len = 2 if first_byte > 0x7f else 3
    coef_mask = 0xffffff * 256 ** (byte_len - coef_len)

    return target & coef_mask


def div_1209600(target: int) -> (int, int):
    divisor = 1209600
    quate = 0
    for i in range(232, -1, -1):
        if 1209600 << i <= target:
            quate = (quate | (1 << i)) if 1209600 << i <= target else quate
            target = target - (1209600 << i) if (1209600 << i) <= target else target
            print(i)
    return target, quate


def div_1209600_zokrates(target: int) -> (int, int):
    divisor = 1209600
    quate = 0
    j = 232 - 29
    expanded_one = 2 ** j
    expanded_divisor = divisor * expanded_one
    condition = True if expanded_divisor <= target else False
    quate = quate + expanded_one if condition else quate
    target = target - expanded_divisor if condition else target
    return target, quate


if __name__ == "__main__":
    max_target = 26959535291011309493156476344723991336010898738574164086137773096960 # 0xffff * 256 ** (0x1d - 3)
    max_target_hex = hex(max_target)
    target = 1859734526474102007161661283304481249417820354151186432
    target_hex = hex(target)

    remainder, quate = div_1209600_zokrates(max_target)
    print(hex(quate))
    print(hex(max_target // 1209600))

    # expected_quata = "0xddeadeadeadeadeadeadeadeadeadeadeadeade"
    # print(expected_quata)