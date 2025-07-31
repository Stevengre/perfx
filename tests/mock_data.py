# 自动生成的真实 Mock 数据
# 生成时间: 2025-07-30 12:15:03
# 此文件由 generate_mocks.py 自动生成，请勿手动修改

# ECHO 命令的真实输出
real_echo_output = {
    "command": "echo 'Hello, World! This is a test output.'",
    "stdout": "Hello, World! This is a test output.\n",
    "stderr": "",
    "exit_code": 0,
    "duration": 0.006,
    "success": True,
}

# SLEEP 命令的真实输出
real_sleep_output = {
    "command": "sleep 0.1",
    "stdout": "",
    "stderr": "",
    "exit_code": 0,
    "duration": 0.106,
    "success": True,
}

# FAIL 命令的真实输出
real_fail_output = {
    "command": "nonexistent_command",
    "stdout": "",
    "stderr": "/bin/sh: nonexistent_command: command not found\n",
    "exit_code": 127,
    "duration": 0.005,
    "success": False,
}

# PYTEST 命令的真实输出
real_pytest_output = {
    "command": "pytest /var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py",
    "stdout": '============================= test session starts ==============================\nplatform darwin -- Python 3.10.17, pytest-8.4.1, pluggy-1.6.0 -- /Users/steven/Desktop/projs/perfx/.venv/bin/python\ncachedir: .pytest_cache\nrootdir: /var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T\nplugins: cov-6.2.1, mock-3.14.1\ncollecting ... collected 8 items\n\n../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_simple PASSED [ 12%]\n../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_math PASSED [ 25%]\n../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_string PASSED [ 37%]\n../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_failing FAILED [ 50%]\n../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_passing PASSED [ 62%]\n../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_list PASSED [ 75%]\n../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_slow PASSED [ 87%]\n../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_medium PASSED [100%]\n\n=================================== FAILURES ===================================\n_________________________________ test_failing _________________________________\n\n    def test_failing():\n        """失败的测试"""\n>       assert False, "This test should fail"\nE       AssertionError: This test should fail\nE       assert False\n\n/var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py:21: AssertionError\n============================== slowest durations ===============================\n0.11s call     tmp50ymjfxh.py::test_slow\n0.05s call     tmp50ymjfxh.py::test_medium\n0.00s teardown tmp50ymjfxh.py::test_medium\n0.00s teardown tmp50ymjfxh.py::test_slow\n0.00s setup    tmp50ymjfxh.py::test_medium\n0.00s call     tmp50ymjfxh.py::test_failing\n0.00s setup    tmp50ymjfxh.py::test_simple\n0.00s teardown tmp50ymjfxh.py::test_failing\n0.00s teardown tmp50ymjfxh.py::test_math\n0.00s call     tmp50ymjfxh.py::test_simple\n0.00s teardown tmp50ymjfxh.py::test_simple\n0.00s setup    tmp50ymjfxh.py::test_math\n0.00s setup    tmp50ymjfxh.py::test_list\n0.00s setup    tmp50ymjfxh.py::test_passing\n0.00s setup    tmp50ymjfxh.py::test_slow\n0.00s setup    tmp50ymjfxh.py::test_string\n0.00s teardown tmp50ymjfxh.py::test_passing\n0.00s call     tmp50ymjfxh.py::test_math\n0.00s call     tmp50ymjfxh.py::test_passing\n0.00s teardown tmp50ymjfxh.py::test_list\n0.00s call     tmp50ymjfxh.py::test_string\n0.00s call     tmp50ymjfxh.py::test_list\n0.00s setup    tmp50ymjfxh.py::test_failing\n0.00s teardown tmp50ymjfxh.py::test_string\n=========================== short test summary info ============================\nFAILED ../../../../../var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmp50ymjfxh.py::test_failing - AssertionError: This test should fail\nassert False\n========================= 1 failed, 7 passed in 0.21s ==========================\n',
    "stderr": "",
    "exit_code": 1,
    "duration": 0.425,
    "success": False,
}

# JSON 命令的真实输出
real_json_output = {
    "command": "python /var/folders/tv/w56gdfyn7lj8s3t4r_5cp7540000gn/T/tmpefoe4fmp.py",
    "stdout": '{\n  "results": {\n    "total_tests": 6,\n    "passed_tests": 5,\n    "failed_tests": 1,\n    "skipped_tests": 0,\n    "duration": 1.234,\n    "timestamp": "2024-01-01T12:00:00Z"\n  },\n  "details": [\n    {\n      "test": "test_simple",\n      "status": "PASSED",\n      "duration": 0.1,\n      "message": ""\n    },\n    {\n      "test": "test_math",\n      "status": "PASSED",\n      "duration": 0.2,\n      "message": ""\n    },\n    {\n      "test": "test_string",\n      "status": "PASSED",\n      "duration": 0.15,\n      "message": ""\n    },\n    {\n      "test": "test_failing",\n      "status": "FAILED",\n      "duration": 0.05,\n      "message": "AssertionError: This test should fail"\n    },\n    {\n      "test": "test_passing",\n      "status": "PASSED",\n      "duration": 0.12,\n      "message": ""\n    },\n    {\n      "test": "test_list",\n      "status": "PASSED",\n      "duration": 0.18,\n      "message": ""\n    }\n  ],\n  "summary": {\n    "success_rate": 83.33,\n    "average_duration": 0.133,\n    "slowest_test": "test_math",\n    "fastest_test": "test_failing"\n  }\n}\n',
    "stderr": "",
    "exit_code": 0,
    "duration": 0.027,
    "success": True,
}

# LS 命令的真实输出
real_ls_output = {
    "command": "ls -la",
    "stdout": "total 1200\ndrwxr-xr-x@ 16 steven  staff     512  7 30 12:14 .\ndrwxr-xr-x@ 24 steven  staff     768  7 30 09:43 ..\ndrwxr-xr-x@ 13 steven  staff     416  7 30 11:44 .git\n-rw-r--r--@  1 steven  staff    6298  7 30 11:47 .gitignore\ndrwxr-xr-x@  6 steven  staff     192  7 30 11:40 .pytest_cache\ndrwxr-xr-x@  9 steven  staff     288  7 30 11:50 .venv\ndrwxr-xr-x@  8 steven  staff     256  7 30 11:23 configs\n-rw-r--r--@  1 steven  staff   11357  7 29 12:00 LICENSE\n-rw-r--r--@  1 steven  staff    4149  7 30 12:14 Makefile\ndrwxr-xr-x@ 11 steven  staff     352  7 30 12:14 perfx\n-rw-r--r--@  1 steven  staff    1599  7 30 11:56 pyproject.toml\n-rw-r--r--@  1 steven  staff    8484  7 30 12:14 PYTEST_PARSER_FIX.md\n-rw-r--r--@  1 steven  staff    5953  7 30 10:11 README.md\ndrwxr-xr-x@  5 steven  staff     160  7 30 12:14 test_output\ndrwxr-xr-x@ 14 steven  staff     448  7 30 12:14 tests\n-rw-r--r--@  1 steven  staff  558275  7 30 11:39 uv.lock\n",
    "stderr": "",
    "exit_code": 0,
    "duration": 0.007,
    "success": True,
}

# DATE 命令的真实输出
real_date_output = {
    "command": "date",
    "stdout": "2025年 7月30日 星期三 12时15分03秒 CST\n",
    "stderr": "",
    "exit_code": 0,
    "duration": 0.005,
    "success": True,
}
