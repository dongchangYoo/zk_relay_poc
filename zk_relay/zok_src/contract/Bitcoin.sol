pragma solidity ^0.8.0;

import "./verifier3.sol";

contract Bitcoin is Verifier {

    struct Branch{
        // 자기 자신의 길이가 6이 넘어가면 부모 Branch를 실행한다.
        uint256 parentBranchIndex;
        uint256 branchStartHeight;

        mapping(uint256 => uint256) heightToBlockHash;
        mapping(uint256 => uint256) blockHashToHeight;
        mapping(uint256 => BlockData) heightToBlock;
        uint256 headTimeAndBits;

        // execute_tx는 confirmedHeight 부터 latestHeight까지 block을 돌면서 tx를 실행한다.
        uint256 confirmedHeight;  // 제출 height - 6
        uint256 latestHeight; // 마지막 제출 height로 갱신
    }

    struct BlockData {
        Transaction[] txs;
    }

    struct Transaction {
        uint256 amount;
        address recipient;
    }

    mapping(uint256 => Branch) branches;  // branch index => Branch
    uint256 numBranch = 0;

    uint256 constant BATCH_NUM = 3;

    // timeBits 값은 startHeight 가 2019인 경우, 2016의 timeBits값을 입력한다.
    // startHeight가 2019인 경우, 2016의 timeBits값을 입력한다.
    // 0x9dfdd, "0x00000000000000000000d14f8ae6e38cc42ecd2f79d1b55f860340d394e5d238", "0x0000000000000000000000000000000021738a2d8b7b435fea071017acc0cd5c"
    constructor(uint256 startHeight, uint256 startHash, uint256 timeBits) {
        Branch storage mainBranch = branches[++numBranch];
        mainBranch.parentBranchIndex = 0;
        mainBranch.branchStartHeight = startHeight;
        mainBranch.heightToBlockHash[startHeight] = startHash;
        mainBranch.blockHashToHeight[startHash] = startHeight;
        mainBranch.headTimeAndBits = timeBits;
        mainBranch.confirmedHeight = startHeight;
        mainBranch.latestHeight = startHeight;
    }


    /*
    description of inputs
    [0]: 16 bytes word including start header's time and bits
    [1]: start header's previous hash (32 bytes)
    [2:7]: 5 word of final header (16 bytes * 5)
    [7]: final header's hash (32 bytes)
    [8]: next target (32 bytes)
    */
    // 1, [["0x14f529c1f6976ccb65f3dda4645a723c784749214fc16f832861d7fa394bc01f", "0x25ab0e5ed6d5a7a465409708ab85ad18eebcc4b448102cf909359918a990fe7a"], [["0x2b7e3357ce14cf31d3512e55f8b43a8dcfc690dc50028a7df4f2d6cb78b3c73c", "0x2fdfc27a38f7c861c1d2e46ebe4209866a50f7429a4350e5e9341c086a7c8f7c"], ["0x129c874a29fc2370e7800c1a24b3486704d59514c9b7dcf434df8e5b4a6b25a0", "0x019d3dadfbd1728501b44a0b99b8a53f1dd116d89fd3136d65b77c659f7d280d"]], ["0x0f28360bd7e9be3e52d722af53dc36ff13479b0233de93872c43a187cc047e50", "0x21cd11d54fd11d3228d318c51b94afd21adc079be23879b3bc6ee89fcdd09e9e"]], ["0x0000000000000000000000000000000021738a2d8b7b435fea071017acc0cd5c", "0x00000000000000000000d14f8ae6e38cc42ecd2f79d1b55f860340d394e5d238", "0x000000000000000000000000000000000000402006ab8f2d0115e32b99b9ca02", "0x000000000000000000000000000000000c8ed149aa5c92aac757060000000000", "0x0000000000000000000000000000000000000000f25a11bb8e935667a49e32e9", "0x00000000000000000000000000000000247aca7f9d63a7c1e506891e16fa4168", "0x000000000000000000000000000000000c5e2b76282c565f123a101749e4a793", "0x000000000000000000003355843ef2eefc24ef9a55a9ac5162f5a968552003c2", "0x000000000000000000103a12b0eca8641fdb97530eca8641fdb97530eca8641f"]
    function relay3(uint256 branchIndex, Proof memory proof, uint[9] memory input) external returns (bool) {
        // check zk_proof
        bool result = verifyTx(proof, input);
        require(result == true, "Proof validation fails");

        // check connectivity between branch and submitted headers
        Branch storage branch = branches[branchIndex];
        uint256 predecessor_height = branch.blockHashToHeight[input[1]];
        require(predecessor_height != 0, "There is no predecessor.");

        // check wheather headTimeAndBits stored in the bitcoin contract equals to starting header's timeAndBits.
        require(branch.headTimeAndBits == input[0]);


        uint256 local_height = branch.latestHeight;
        bool difficulty_updating = is_updating_submit(local_height);

        if (difficulty_updating) {
            //check target
            uint256 expected_bits = targetToLittleBits(input[8]);  // little bits
            uint256 actual_bits = (input[6] & 0xffffffff00000000) >> 32;
            require(expected_bits == actual_bits, "Invalid updated bits");

            // update headTimeAndBits
            branch.headTimeAndBits = input[6];  // next timeAndBits
        }

        // execute txs
        branch.confirmedHeight = local_height + BATCH_NUM - 6;
        branch.latestHeight = local_height + BATCH_NUM;
        // store new header

        branch.heightToBlockHash[predecessor_height + BATCH_NUM] = input[7];
        branch.blockHashToHeight[input[7]] = predecessor_height + BATCH_NUM;

        return true;
    }

    function is_updating_submit(uint256 local_height) pure internal returns (bool) {
        uint256 updatingHeight = local_height % 2016 != 0 ? (local_height) / 2016 * 2016 + 2016 : local_height;
        require(updatingHeight > local_height, "last header height must be less than or equal to updatingHeight");
        return (local_height + BATCH_NUM) % 2016 == 0;
    }

    function targetToLittleBits(uint256 target) internal pure returns (uint32) {
        uint256 i;
        uint256 firstByte = 0xFF00000000000000000000000000000000000000000000000000000000000000;

        // find first index
        while(true) {
            if( ( (target << i) & firstByte ) != 0 ) {

                if((target << i) & firstByte > 0x7F00000000000000000000000000000000000000000000000000000000000000) {
                    // exception case.
                    if(i!=0) i-=8;
                }
                break;
            }
            i+=8;
        }

        uint32 little_bits = uint32( ( (256-i) << 21) | (target >> (232-i)) & 0xFFFFFF );

        uint32[4] memory tmp;
        tmp[0] = (little_bits & 0xff000000) >> 24;
        tmp[1] = (little_bits & 0x00ff0000) >> 8;
        tmp[2] = (little_bits & 0x0000ff00) << 8;
        tmp[3] = (little_bits & 0x000000ff) << 24;

        return tmp[0] | tmp[1] | tmp[2] | tmp[3];
    }

    function get_branch_info(uint256 branchIndex) view external returns (uint256, uint256, uint256, uint256) {
        Branch storage branch = branches[branchIndex];
        return (branch.latestHeight, branch.headTimeAndBits, branch.confirmedHeight, branch.latestHeight);
    }
}
