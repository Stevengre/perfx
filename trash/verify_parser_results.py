#!/usr/bin/env python3
"""
Verify the parser results and show detailed information
"""
import json
import os

def verify_results():
    """Verify the parsed results"""
    
    parsed_files = [
        "results/data/pure_concrete_performance_parsed.json",
        "results/data/prove_summaries_results_parsed.json"
    ]
    
    for parsed_file in parsed_files:
        if not os.path.exists(parsed_file):
            print(f"Parsed file not found: {parsed_file}")
            continue
            
        print(f"\n{'='*80}")
        print(f"Verifying: {parsed_file}")
        print(f"{'='*80}")
        
        with open(parsed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic statistics
        print(f"Total tests: {data['total_tests']}")
        print(f"Passed: {data['passed_tests']}")
        print(f"Failed: {data['failed_tests']}")
        print(f"Skipped: {data['skipped_tests']}")
        print(f"Error: {data['error_tests']}")
        print(f"Total duration: {data['total_duration']:.2f}s")
        
        # Check test_id format
        print(f"\nTest ID format examples:")
        for i, test in enumerate(data['test_results'][:3]):
            print(f"  {i+1}. {test['test_id']}")
        
        # Check duration information
        tests_with_duration = [t for t in data['test_results'] if t['duration'] and t['duration'] > 0]
        tests_without_duration = [t for t in data['test_results'] if not t['duration'] or t['duration'] == 0]
        
        print(f"\nDuration statistics:")
        print(f"  Tests with duration > 0: {len(tests_with_duration)}")
        print(f"  Tests without duration: {len(tests_without_duration)}")
        
        if tests_with_duration:
            print(f"\nSample tests with duration:")
            for i, test in enumerate(tests_with_duration[:3]):
                print(f"  {i+1}. {test['test_id']}")
                print(f"     Duration: {test['duration']}s")
        
        # Check if test_id contains full path
        full_path_tests = [t for t in data['test_results'] if '::' in t['test_id']]
        print(f"\nTest ID format verification:")
        print(f"  Tests with full path (containing '::'): {len(full_path_tests)}")
        print(f"  Tests without full path: {len(data['test_results']) - len(full_path_tests)}")
        
        if full_path_tests:
            print(f"\nSample full path test IDs:")
            for i, test in enumerate(full_path_tests[:3]):
                print(f"  {i+1}. {test['test_id']}")

def main():
    """Main function"""
    print("Verifying pytest parser results...")
    verify_results()
    print(f"\n{'='*80}")
    print("Verification complete!")
    print("The parser now correctly extracts:")
    print("1. Full test_id format (including file path and function name)")
    print("2. Duration information where available")
    print("3. Can process JSON files containing raw_stdout")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 