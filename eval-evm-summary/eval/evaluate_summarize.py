import time
import traceback
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from kevm_pyk.summarizer import OPCODES, summarize
from kevm_pyk.summarizer import get_summary_status, OPCODES_SUMMARY_STATUS

SUMMARIZE_TIME_OUT = 10 * 60 # 10 minutes

# Opcode categories for evaluation
OPCODE_CATEGORIES = {
    # 1. Arithmetic and Bitwise Operations
    'ARITHMETIC_AND_BITWISE': [
        'ADD',
        'MUL',
        'SUB',
        'DIV',
        'SDIV',
        'MOD',
        'SMOD',
        'ADDMOD',
        'MULMOD',
        'EXP',
        'SIGNEXTEND',
        'LT',
        'GT',
        'SLT',
        'SGT',
        'EQ',
        'ISZERO',
        'AND',
        'EVMOR',
        'XOR',
        'NOT',
        'BYTE',
        'SHL',
        'SHR',
        'SAR',
    ],
    # 2. Flow Control Operations
    'FLOW_CONTROL': ['STOP', 'JUMP', 'JUMPI', 'PC', 'JUMPDEST', 'RETURN', 'REVERT', 'INVALID', 'UNDEFINED'],
    # 3. Block and Transaction Information
    'BLOCK_AND_TRANSACTION': [
        'ADDRESS',
        'BALANCE',
        'ORIGIN',
        'CALLER',
        'CALLVALUE',
        'CALLDATALOAD',
        'CALLDATASIZE',
        'CALLDATACOPY',
        'CODESIZE',
        'CODECOPY',
        'GASPRICE',
        'EXTCODESIZE',
        'EXTCODECOPY',
        'RETURNDATASIZE',
        'RETURNDATACOPY',
        'EXTCODEHASH',
        'BLOCKHASH',
        'COINBASE',
        'TIMESTAMP',
        'NUMBER',
        'PREVRANDAO',
        'DIFFICULTY',
        'GASLIMIT',
        'CHAINID',
        'SELFBALANCE',
        'BASEFEE',
        'BLOBHASH',
        'BLOBBASEFEE',
    ],
    # 4. Stack Operations
    'STACK_OPERATIONS': [
        'POP',
        'PUSHZERO',
        'PUSH',
        'DUP',
        'SWAP',
    ],
    # 5. Memory Operations
    'MEMORY_OPERATIONS': ['MLOAD', 'MSTORE', 'MSTORE8', 'MSIZE', 'MCOPY'],
    # 6. Storage Operations
    'STORAGE_OPERATIONS': ['SLOAD', 'SSTORE'],
    # 7. Transient Storage Operations
    'TRANSIENT_STORAGE_OPERATIONS': ['TLOAD', 'TSTORE'],
    # 8. System and Call Operations
    'SYSTEM_AND_CALLS': ['CREATE', 'CREATE2', 'CALL', 'CALLCODE', 'DELEGATECALL', 'STATICCALL', 'SELFDESTRUCT', 'GAS'],
    # 9. Logging Operations
    'LOGGING': ['LOG'],
    # 10. Hashing Operations
    'HASHING': ['SHA3'],  # Also known as KECCAK256
}

def get_opcode_category(opcode: str) -> str:
    for cat, op_list in OPCODE_CATEGORIES.items():
        if opcode in op_list:
            return cat
    return "UNKNOWN"


def summarize_worker(opcode: str) -> Dict[str, Any]:
    entry = {
        "opcode": opcode,
        "category": get_opcode_category(opcode),
        "success": False,
        "time": None,
        "rewriting_steps": None,  # list of edge.depth
        "error": None,
        "summary_status": get_summary_status(opcode) if opcode in OPCODES_SUMMARY_STATUS else None
    }
    start = time.time()
    try:
        from pyk.kcfg import KCFG
        _, proofs = summarize(opcode)
        proof_success = True
        steps_list = []
        for proof in proofs:
            # 1. All leaves not pending/stuck/vacuous/bounded
            for leaf in proof.kcfg.leaves:
                if proof.is_pending(leaf.id) or proof.kcfg.is_stuck(leaf.id) or proof.kcfg.is_vacuous(leaf.id) or proof.is_bounded(leaf.id):
                    proof_success = False
                    break
            if not proof_success:
                break
            # 2. Only one successor from init
            successors = proof.kcfg.successors(proof.init)
            if len(successors) != 1:
                proof_success = False
                break
            successor = successors[0]
            # 3. Edge/terminal/covered check
            if isinstance(successor, KCFG.Split):
                targets = successor.targets
                if len(proof.kcfg.edges()) != len(targets):
                    proof_success = False
                    break
                for target in targets:
                    s2 = proof.kcfg.successors(target.id)
                    if len(s2) != 1:
                        proof_success = False
                        break
                    edge = s2[0]
                    if not isinstance(edge, KCFG.Edge):
                        proof_success = False
                        break
                    if not (proof.is_terminal(edge.target.id) or proof.kcfg.is_covered(edge.target.id)):
                        proof_success = False
                        break
                    steps_list.append(edge.depth)
            else:
                if len(proof.kcfg.edges()) != 1:
                    proof_success = False
                    break
                if not isinstance(successor, KCFG.Edge):
                    proof_success = False
                    break
                if not (proof.is_terminal(successor.target.id) or proof.kcfg.is_covered(successor.target.id)):
                    proof_success = False
                    break
                steps_list.append(successor.depth)
        entry["success"] = proof_success
        entry["rewriting_steps"] = steps_list
    except Exception as e:
        entry["error"] = str(e) + "\n" + traceback.format_exc()
    finally:
        entry["time"] = time.time() - start
    return entry


def evaluate_summarize_effectiveness(timeout_sec: int = 600, max_workers: int = 4, skip_opcodes: List[str] = None) -> List[Dict[str, Any]]:
    """
    Evaluate summarize() for all opcodes: success, time, rewriting steps, error.
    Returns a list of dicts for each opcode.
    
    Args:
        timeout_sec: Timeout for each opcode evaluation in seconds
        max_workers: Maximum number of parallel workers
        skip_opcodes: List of opcodes to skip (e.g., ['JUMP', 'JUMPI'])
    """
    if skip_opcodes is None:
        skip_opcodes = []
    
    # Filter out opcodes to skip
    opcodes_to_evaluate = {opcode: info for opcode, info in OPCODES.items() if opcode not in skip_opcodes}
    
    if skip_opcodes:
        print(f"Skipping opcodes: {', '.join(skip_opcodes)}")
        print(f"Evaluating {len(opcodes_to_evaluate)} opcodes out of {len(OPCODES)} total")
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_opcode = {executor.submit(summarize_worker, opcode): opcode for opcode in opcodes_to_evaluate.keys()}
        for future in as_completed(future_to_opcode):
            opcode = future_to_opcode[future]
            try:
                result = future.result(timeout=timeout_sec)
            except Exception as e:
                result = {
                    "opcode": opcode,
                    "category": get_opcode_category(opcode),
                    "success": False,
                    "time": None,
                    "rewriting_steps": None,
                    "error": f"timeout or error: {str(e)}",
                    "summary_status": get_summary_status(opcode) if opcode in OPCODES_SUMMARY_STATUS else None
                }
            results.append(result)
    
    # Add skipped opcodes to results with skip status
    for opcode in skip_opcodes:
        results.append({
            "opcode": opcode,
            "category": get_opcode_category(opcode),
            "success": False,
            "time": None,
            "rewriting_steps": None,
            "error": "SKIPPED",
            "summary_status": get_summary_status(opcode) if opcode in OPCODES_SUMMARY_STATUS else None
        })
    
    return results