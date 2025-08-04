#!/usr/bin/env python3
"""
Test script for the modified pytest parser
"""
import json
import sys
import os
from perfx.parsers.pytest import PytestParser

def test_parser():
    """Test the modified pytest parser with the JSON files"""
    
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
            
        print(f"\n{'='*60}")
        print(f"Processing: {json_file}")
        print(f"{'='*60}")
        
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
            
            # Show first few test results with full test_id
            print(f"\nFirst 5 test results:")
            for i, test in enumerate(result['test_results'][:5]):
                print(f"  {i+1}. {test['test_id']}")
                print(f"     Status: {test['status']}")
                print(f"     Duration: {test['duration']}s")
                print()
            
            # Show tests with duration > 0
            tests_with_duration = [t for t in result['test_results'] if t['duration'] and t['duration'] > 0]
            if tests_with_duration:
                print(f"Tests with duration > 0 ({len(tests_with_duration)}):")
                for i, test in enumerate(tests_with_duration[:5]):
                    print(f"  {i+1}. {test['test_id']} - {test['duration']}s")
                if len(tests_with_duration) > 5:
                    print(f"  ... and {len(tests_with_duration) - 5} more")
            else:
                print("No tests with duration > 0 found")
            
            # Save the parsed result to a new file
            output_file = json_file.replace('.json', '_parsed.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nParsed result saved to: {output_file}")
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_parser() 