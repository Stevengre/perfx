#!/usr/bin/env python3
"""
用于复现实验结果的主入口。
"""

from .kevm_builder import auto_build
from .test_runner import (
    run_conformance_test_with_summary, 
    run_prove_summaries_test_with_recording,
    run_concrete_execution_performance_comparison,
    run_symbolic_execution_performance_comparison,
    run_conformance_test_with_semantics
)
from .evaluation_recorder import recorder
from .evaluate_summarize import evaluate_summarize_effectiveness
from . import PROJECT_ROOT, EVM_SEMANTICS_DIR
import sys
import argparse


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="EVM Summarization Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 执行所有评估步骤
  python -m eval
  
  # 只执行构建步骤
  python -m eval --build-only
  
  # 只执行summarize评估
  python -m eval --summarize-only
  
  # 只执行prove summaries测试
  python -m eval --prove-only
  
  # 只执行concrete execution性能评估
  python -m eval --concrete-only
  
  # 组合执行多个步骤
  python -m eval --build --summarize --prove
  
  # 跳过特定步骤
  python -m eval --skip-build --skip-summarize --skip-concrete
        """
    )
    
    # 主要步骤选择
    parser.add_argument(
        '--build-only', 
        action='store_true',
        help='只执行构建步骤（STEP 1和STEP 3）'
    )
    parser.add_argument(
        '--summarize-only', 
        action='store_true',
        help='只执行summarize评估（STEP 2）'
    )
    parser.add_argument(
        '--prove-only', 
        action='store_true',
        help='只执行prove summaries测试（STEP 4）'
    )
    parser.add_argument(
        '--concrete-only', 
        action='store_true',
        help='只执行concrete execution性能评估（STEP 5）'
    )
    parser.add_argument(
        '--symbolic-only', 
        action='store_true',
        help='只执行symbolic execution性能评估（STEP 6）'
    )
    parser.add_argument(
        '--process-data-only', 
        action='store_true',
        help='只处理已保存的数据并生成图表，不执行任何命令'
    )
    
    # 单独步骤控制
    parser.add_argument(
        '--build', 
        action='store_true',
        help='执行构建步骤（STEP 1和STEP 3）'
    )
    parser.add_argument(
        '--summarize', 
        action='store_true',
        help='执行summarize评估（STEP 2）'
    )
    parser.add_argument(
        '--prove', 
        action='store_true',
        help='执行prove summaries测试（STEP 4）'
    )
    parser.add_argument(
        '--concrete', 
        action='store_true',
        help='执行concrete execution性能评估（STEP 5）'
    )
    parser.add_argument(
        '--symbolic', 
        action='store_true',
        help='执行symbolic execution性能评估（STEP 6）'
    )
    
    # 跳过步骤
    parser.add_argument(
        '--skip-build', 
        action='store_true',
        help='跳过构建步骤'
    )
    parser.add_argument(
        '--skip-summarize', 
        action='store_true',
        help='跳过summarize评估'
    )
    parser.add_argument(
        '--skip-prove', 
        action='store_true',
        help='跳过prove summaries测试'
    )
    parser.add_argument(
        '--skip-concrete', 
        action='store_true',
        help='跳过concrete execution性能评估'
    )
    parser.add_argument(
        '--skip-symbolic', 
        action='store_true',
        help='跳过symbolic execution性能评估'
    )
    
    # 其他选项
    parser.add_argument(
        '--skip-opcodes', 
        nargs='+',
        default=[
            'BASEFEE', 'CALL', 'CALLCODE', 'CALLVALUE', 'CREATE', 'CREATE2',
            'DELEGATECALL', 'EXTCODECOPY', 'EXTCODEHASH', 'EXTCODESIZE',
            'JUMP', 'JUMPI', 'MUL', 'SELFDESTRUCT', 'STATICCALL'
        ],
        help='指定要跳过的opcode列表（默认跳过当前失败的opcode）'
    )
    parser.add_argument(
        '--no-save', 
        action='store_true',
        help='不保存结果到文件'
    )
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='显示详细输出'
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # 确定要执行的步骤
    if args.process_data_only:
        # 只处理数据，不执行任何命令
        print("="*60)
        print("数据处理模式：只处理已保存的数据并生成图表")
        print("="*60)
        
        try:
            from .data_processor import DataProcessor
            processor = DataProcessor("evaluation_results")
            processor.process_all_data()
            print("\n✓ 数据处理完成！")
            return
        except Exception as e:
            print(f"✗ 数据处理失败: {e}")
            return
    elif args.build_only:
        steps_to_run = {'build'}
    elif args.summarize_only:
        steps_to_run = {'summarize'}
    elif args.prove_only:
        steps_to_run = {'prove'}
    elif args.concrete_only:
        steps_to_run = {'concrete'}
    elif args.symbolic_only:
        steps_to_run = {'symbolic'}
    else:
        # 检查是否有明确指定的步骤
        specified_steps = set()
        if args.build:
            specified_steps.add('build')
        if args.summarize:
            specified_steps.add('summarize')
        if args.prove:
            specified_steps.add('prove')
        if args.concrete:
            specified_steps.add('concrete')
        if args.symbolic:
            specified_steps.add('symbolic')
        
        # 如果有明确指定的步骤，只执行这些步骤
        if specified_steps:
            steps_to_run = specified_steps
        else:
            # 默认执行所有步骤，除非被跳过
            steps_to_run = {'build', 'summarize', 'prove', 'concrete', 'symbolic'}
        
        # 应用跳过选项
        if args.skip_build:
            steps_to_run.discard('build')
        if args.skip_summarize:
            steps_to_run.discard('summarize')
        if args.skip_prove:
            steps_to_run.discard('prove')
        if args.skip_concrete:
            steps_to_run.discard('concrete')
        if args.skip_symbolic:
            steps_to_run.discard('symbolic')
    
    if args.verbose:
        print(f"将要执行的步骤: {', '.join(sorted(steps_to_run))}")
        print(f"跳过的opcode: {', '.join(args.skip_opcodes)}")
    
    # 初始化结果跟踪
    results = {
        'build': None,  # None表示未执行，True表示成功，False表示失败
        'summarize': None,
        'prove': None,
        'concrete': None,
        'symbolic': None
    }
    
    # 记录跳过的步骤
    skipped_steps = set()
    
    # STEP 1: 第一次构建（在项目根目录）
    first_build_success = False
    if 'build' in steps_to_run:
        print("="*60)
        print("STEP 1: BUILDING KEVM SEMANTICS (FIRST TIME IN PROJECT ROOT)")
        print("="*60)
        recorder.start_test("build_step1")
        first_build_success = auto_build(build_dir=PROJECT_ROOT)
        recorder.end_test("build_step1", first_build_success)
        results['build'] = first_build_success
    else:
        # 如果跳过构建，假设构建成功（用于依赖检查）
        first_build_success = True
        skipped_steps.add('build')
        print("构建步骤已跳过")

    # STEP 2: summarize评估
    if 'summarize' in steps_to_run and first_build_success:
        print("\n" + "="*60)
        print("STEP 2: SUMMARIZE EVALUATION")
        print("="*60)
        print(f"跳过opcode: {', '.join(args.skip_opcodes)}")
        recorder.start_test("summarize_evaluation")
        summarize_eval_results = evaluate_summarize_effectiveness(skip_opcodes=args.skip_opcodes)
        recorder.results["summarize_eval"] = summarize_eval_results
        recorder.end_test("summarize_evaluation", True)
        results['summarize'] = True
    elif 'summarize' in steps_to_run:
        print("STEP 2: SKIPPED (BUILD FAILED OR SKIPPED)")
        skipped_steps.add('summarize')
        results['summarize'] = None

    # STEP 3: 第二次构建（在evm-semantics目录）
    second_build_success = False
    if 'build' in steps_to_run:
        print("\n" + "="*60)
        print("STEP 3: RE-BUILDING BEFORE CONFORMANCE TESTING (IN EVM-SEMANTICS)")
        print("="*60)
        recorder.start_test("build_step2")
        second_build_success = auto_build(build_dir=EVM_SEMANTICS_DIR, project_name="kevm-pyk")
        recorder.end_test("build_step2", second_build_success)
        results['build'] = results['build'] and second_build_success
    else:
        # 如果跳过构建，假设构建成功（用于依赖检查）
        second_build_success = True
        print("构建步骤已跳过")

    # STEP 4: Prove summaries测试
    if 'prove' in steps_to_run and second_build_success:
        print("\n" + "="*60)
        print("STEP 4: PROVE SUMMARIES TESTING")
        print("="*60)
        recorder.start_test("prove_summaries_test")
        prove_success = run_prove_summaries_test_with_recording()
        recorder.end_test("prove_summaries_test", prove_success)
        results['prove'] = prove_success
    elif 'prove' in steps_to_run:
        print("STEP 4: SKIPPED (BUILD FAILED OR SKIPPED)")
        skipped_steps.add('prove')
        results['prove'] = None
    
    # STEP 5: Concrete execution性能评估
    if 'concrete' in steps_to_run and second_build_success:
        print("\n" + "="*60)
        print("STEP 5: CONCRETE EXECUTION PERFORMANCE EVALUATION")
        print("="*60)
        print("Comparing performance between original (llvm-pure) and summarized (llvm-summary) semantics")
        print("Using make test-conformance as the benchmark")
        
        recorder.start_test("concrete_execution_performance")
        concrete_success = run_concrete_execution_performance_comparison()
        recorder.end_test("concrete_execution_performance", concrete_success)
        results['concrete'] = concrete_success
        
        if concrete_success:
            print("\n✓ Concrete execution performance evaluation completed successfully")
            print("Results include:")
            print("  - Detailed test case timing analysis")
            print("  - Performance comparison charts (PNG/PDF)")
            print("  - Academic paper tables (LaTeX/Markdown/CSV)")
            print("  - Statistical analysis of improvements")
        else:
            print("\n✗ Concrete execution performance evaluation failed")
    elif 'concrete' in steps_to_run:
        print("STEP 5: SKIPPED (BUILD FAILED OR SKIPPED)")
        skipped_steps.add('concrete')
        results['concrete'] = None

    # STEP 6: Symbolic execution性能评估
    if 'symbolic' in steps_to_run and second_build_success:
        print("\n" + "="*60)
        print("STEP 6: SYMBOLIC EXECUTION PERFORMANCE EVALUATION")
        print("="*60)
        print("Comparing prove performance between original and summarized semantics")
        
        recorder.start_test("symbolic_execution_performance")
        symbolic_success = run_symbolic_execution_performance_comparison()
        recorder.end_test("symbolic_execution_performance", symbolic_success)
        results['symbolic'] = symbolic_success
        
        if symbolic_success:
            print("\n✓ Symbolic execution performance evaluation completed successfully")
        else:
            print("\n✗ Symbolic execution performance evaluation failed")
    elif 'symbolic' in steps_to_run:
        print("STEP 6: SKIPPED (BUILD FAILED OR SKIPPED)")
        skipped_steps.add('symbolic')
        results['symbolic'] = None
    
    # STEP 7: 保存结果并打印摘要
    if not args.no_save:
        print("\n" + "="*60)
        print("STEP 7: SAVING RESULTS AND PRINTING SUMMARY")
        print("="*60)
        recorder.save_and_print_summary(skipped_steps)
    
    # 返回整体成功状态
    executed_steps = [step for step, executed in results.items() if step in steps_to_run and executed is not None]
    overall_success = all(results[step] for step in executed_steps) if executed_steps else True
    
    print("\n" + "="*60)
    print("EVALUATION COMPLETED")
    print("="*60)
    print(f"执行的步骤: {', '.join(sorted(steps_to_run))}")
    if skipped_steps:
        print(f"跳过的步骤: {', '.join(sorted(skipped_steps))}")
    print(f"Overall Success: {'✓ YES' if overall_success else '✗ NO'}")
    
    if 'prove' in steps_to_run:
        if 'prove' in skipped_steps:
            print(f"RQ1 (Effectiveness): ⏭️ SKIPPED")
        else:
            print(f"RQ1 (Effectiveness): {'✓ PASSED' if results['prove'] else '✗ FAILED'}")
    if 'concrete' in steps_to_run:
        if 'concrete' in skipped_steps:
            print(f"RQ2 (Concrete Efficiency): ⏭️ SKIPPED")
        else:
            print(f"RQ2 (Concrete Efficiency): {'✓ PASSED' if results['concrete'] else '✗ FAILED'}")
    if 'symbolic' in steps_to_run:
        if 'symbolic' in skipped_steps:
            print(f"RQ2 (Symbolic Efficiency): ⏭️ SKIPPED")
        else:
            print(f"RQ2 (Symbolic Efficiency): {'✓ PASSED' if results['symbolic'] else '✗ FAILED'}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
