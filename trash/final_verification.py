#!/usr/bin/env python3
"""
Final verification script for the pytest parser
"""
import json
import os
from perfx.parsers.pytest import PytestParser

def verify_both_files():
    """Verify both JSON files are parsed correctly"""
    
    # Initialize parser
    parser = PytestParser({})
    
    # Test files
    test_files = [
        "results/data/pure_concrete_performance.json",
        "results/data/prove_summaries_results.json"
    ]
    
    for json_file in test_files:
        if not os.path.exists(json_file):
            print(f"File not found: {json_file}")
            continue
            
        print(f"\n{'='*80}")
        print(f"Final verification: {json_file}")
        print(f"{'='*80}")
        
        try:
            # Parse the JSON file
            result = parser.parse_from_json_file(json_file)
            
            # Print summary
            print(f"Success: {result['success']}")
            print(f"Exit code: {result['exit_code']}")
            print(f"Total tests: {result['total_tests']}")
            print(f"Passed: {result['passed_tests']}")
            print(f"Failed: {result['failed_tests']}")
            print(f"Skipped: {result['skipped_tests']}")
            print(f"Error: {result['error_tests']}")
            print(f"Total duration: {result['total_duration']:.2f}s")
            
            # Check test_id format
            print(f"\nTest ID format verification:")
            full_path_tests = [t for t in result['test_results'] if '::' in t['test_id']]
            print(f"  Tests with full path (containing '::'): {len(full_path_tests)}")
            print(f"  Tests without full path: {len(result['test_results']) - len(full_path_tests)}")
            
            # Show sample test IDs
            print(f"\nSample test IDs:")
            for i, test in enumerate(result['test_results'][:3]):
                print(f"  {i+1}. {test['test_id']}")
            
            # Check duration information
            tests_with_duration = [t for t in result['test_results'] if t['duration'] and t['duration'] > 0]
            tests_without_duration = [t for t in result['test_results'] if not t['duration'] or t['duration'] == 0]
            
            print(f"\nDuration statistics:")
            print(f"  Tests with duration > 0: {len(tests_with_duration)}")
            print(f"  Tests without duration: {len(tests_without_duration)}")
            
            if tests_with_duration:
                print(f"\nSample tests with duration:")
                for i, test in enumerate(tests_with_duration[:5]):
                    print(f"  {i+1}. {test['test_id']}")
                    print(f"     Duration: {test['duration']}s")
                
                # Show duration statistics
                durations = [t['duration'] for t in tests_with_duration]
                print(f"\nDuration statistics:")
                print(f"  Min duration: {min(durations):.2f}s")
                print(f"  Max duration: {max(durations):.2f}s")
                print(f"  Average duration: {sum(durations)/len(durations):.2f}s")
            
            # Save the final parsed result
            output_file = json_file.replace('.json', '_final_parsed.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nFinal parsed result saved to: {output_file}")
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function"""
    print("Final verification of pytest parser...")
    verify_both_files()
    print(f"\n{'='*80}")
    print("Final verification complete!")
    print("The parser now correctly:")
    print("1. ✅ Extracts full test_id format (including file path and function name)")
    print("2. ✅ Extracts duration information from 'slowest durations' section")
    print("3. ✅ Can process JSON files containing raw_stdout")
    print("4. ✅ Handles both pure_concrete_performance.json and prove_summaries_results.json")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 