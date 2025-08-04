#!/usr/bin/env python3
"""
Test script to verify duration parsing from pytest output
"""
import json
import os
from perfx.parsers.pytest import PytestParser

def test_duration_parsing():
    """Test the duration parsing functionality"""
    
    # Initialize parser
    parser = PytestParser({})
    
    # Test with prove_summaries_results.json
    json_file = "results/data/prove_summaries_results.json"
    
    if not os.path.exists(json_file):
        print(f"File not found: {json_file}")
        return
    
    print(f"Testing duration parsing with: {json_file}")
    print("=" * 60)
    
    try:
        # Parse the JSON file
        result = parser.parse_from_json_file(json_file)
        
        # Print summary
        print(f"Total tests: {result['total_tests']}")
        print(f"Total duration: {result['total_duration']:.2f}s")
        
        # Show tests with duration > 0
        tests_with_duration = [t for t in result['test_results'] if t['duration'] and t['duration'] > 0]
        tests_without_duration = [t for t in result['test_results'] if not t['duration'] or t['duration'] == 0]
        
        print(f"\nTests with duration > 0: {len(tests_with_duration)}")
        print(f"Tests without duration: {len(tests_without_duration)}")
        
        if tests_with_duration:
            print(f"\nSample tests with duration:")
            for i, test in enumerate(tests_with_duration[:10]):
                print(f"  {i+1}. {test['test_id']}")
                print(f"     Duration: {test['duration']}s")
                print()
        
        # Save the parsed result
        output_file = json_file.replace('.json', '_parsed_v2.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Parsed result saved to: {output_file}")
        
        # Show some statistics
        if tests_with_duration:
            durations = [t['duration'] for t in tests_with_duration]
            print(f"\nDuration statistics:")
            print(f"  Min duration: {min(durations):.2f}s")
            print(f"  Max duration: {max(durations):.2f}s")
            print(f"  Average duration: {sum(durations)/len(durations):.2f}s")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duration_parsing() 