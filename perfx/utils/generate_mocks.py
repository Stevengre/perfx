#!/usr/bin/env python3
"""
真实 Mock 数据生成工具
直接运行真实命令，然后生成 mock 数据到 tests 目录
"""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path


def run_real_command_and_get_output(command: str, timeout: int = 10):
    """运行真实命令并获取完整输出"""
    print(f"运行命令: {command}")

    start_time = time.time()
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        duration = time.time() - start_time

        return {
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "duration": round(duration, 3),
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "exit_code": -1,
            "duration": timeout,
            "success": False,
        }
    except Exception as e:
        return {
            "command": command,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "duration": 0,
            "success": False,
        }


def create_temp_test_file():
    """创建临时测试文件"""
    test_content = '''
import pytest
import time

def test_simple():
    """简单测试"""
    assert True

def test_math():
    """数学测试"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6

def test_string():
    """字符串测试"""
    assert "hello" == "hello"
    assert "world" in "hello world"

def test_failing():
    """失败的测试"""
    assert False, "This test should fail"

def test_passing():
    """通过的测试"""
    assert "test" in "this is a test"

def test_list():
    """列表测试"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15

def test_slow():
    """慢速测试 - 有实际耗时"""
    time.sleep(0.1)  # 100ms
    assert True

def test_medium():
    """中等速度测试"""
    time.sleep(0.05)  # 50ms
    assert 1 == 1
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_content)
        return f.name


def run_real_pytest_and_get_output():
    """运行真实的 pytest 并获取输出"""
    print("创建临时测试文件...")
    test_file = create_temp_test_file()

    try:
        print(f"运行 pytest: {test_file}")

        # 运行 pytest 并捕获输出，使用 --durations=0 和 -vv 显示所有测试耗时
        start_time = time.time()
        result = subprocess.run(
            ["python", "-m", "pytest", test_file, "--durations=0", "-vv"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        duration = time.time() - start_time

        return {
            "command": f"pytest {test_file}",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "duration": round(duration, 3),
            "success": result.returncode == 0,
        }
    finally:
        # 清理临时文件
        try:
            os.unlink(test_file)
        except:
            pass


def run_real_json_command():
    """运行生成 JSON 输出的命令"""
    # 创建一个简单的 Python 脚本来生成 JSON 输出
    json_script = """
import json
import time
import random

# 模拟测试结果
test_results = {
    "results": {
        "total_tests": 6,
        "passed_tests": 5,
        "failed_tests": 1,
        "skipped_tests": 0,
        "duration": 1.234,
        "timestamp": "2024-01-01T12:00:00Z"
    },
    "details": [
        {"test": "test_simple", "status": "PASSED", "duration": 0.1, "message": ""},
        {"test": "test_math", "status": "PASSED", "duration": 0.2, "message": ""},
        {"test": "test_string", "status": "PASSED", "duration": 0.15, "message": ""},
        {"test": "test_failing", "status": "FAILED", "duration": 0.05, "message": "AssertionError: This test should fail"},
        {"test": "test_passing", "status": "PASSED", "duration": 0.12, "message": ""},
        {"test": "test_list", "status": "PASSED", "duration": 0.18, "message": ""}
    ],
    "summary": {
        "success_rate": 83.33,
        "average_duration": 0.133,
        "slowest_test": "test_math",
        "fastest_test": "test_failing"
    }
}

print(json.dumps(test_results, indent=2))
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(json_script)
        script_file = f.name

    try:
        return run_real_command_and_get_output(f"python {script_file}")
    finally:
        try:
            os.unlink(script_file)
        except:
            pass


def generate_mock_data():
    """生成所有真实的 mock 数据"""
    print("=" * 60)
    print("生成真实的 Mock 数据")
    print("=" * 60)

    # 1. 运行简单的 echo 命令
    print("\n1. 运行 echo 命令...")
    echo_result = run_real_command_and_get_output(
        "echo 'Hello, World! This is a test output.'"
    )

    # 2. 运行 sleep 命令
    print("\n2. 运行 sleep 命令...")
    sleep_result = run_real_command_and_get_output("sleep 0.1")

    # 3. 运行失败的命令
    print("\n3. 运行失败的命令...")
    fail_result = run_real_command_and_get_output("nonexistent_command")

    # 4. 运行 pytest
    print("\n4. 运行 pytest...")
    pytest_result = run_real_pytest_and_get_output()

    # 5. 运行 JSON 生成命令
    print("\n5. 运行 JSON 生成命令...")
    json_result = run_real_json_command()

    # 6. 运行一些其他有用的命令
    print("\n6. 运行其他命令...")
    ls_result = run_real_command_and_get_output("ls -la")
    date_result = run_real_command_and_get_output("date")

    # 汇总结果
    all_results = {
        "echo": echo_result,
        "sleep": sleep_result,
        "fail": fail_result,
        "pytest": pytest_result,
        "json": json_result,
        "ls": ls_result,
        "date": date_result,
    }

    return all_results


def save_mock_data_to_tests(all_results, tests_dir: Path):
    """保存 mock 数据到 tests 目录"""
    # 创建 mock 数据文件
    mock_file = tests_dir / "mock_data.py"

    with open(mock_file, "w", encoding="utf-8") as f:
        f.write("# 自动生成的真实 Mock 数据\n")
        f.write("# 生成时间: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write("# 此文件由 generate_mocks.py 自动生成，请勿手动修改\n\n")

        for name, result in all_results.items():
            f.write(f"# {name.upper()} 命令的真实输出\n")
            f.write(f"real_{name}_output = {{\n")
            f.write(f'    "command": {repr(result["command"])},\n')
            f.write(f'    "stdout": {repr(result["stdout"])},\n')
            f.write(f'    "stderr": {repr(result["stderr"])},\n')
            f.write(f'    "exit_code": {result["exit_code"]},\n')
            f.write(f'    "duration": {result["duration"]},\n')
            f.write(f'    "success": {result["success"]}\n')
            f.write("}\n\n")

    print(f"\n真实数据已保存到: {mock_file}")
    return mock_file


def update_conftest_py(tests_dir: Path):
    """更新 conftest.py 文件以使用生成的 mock 数据"""
    conftest_file = tests_dir / "conftest.py"

    # 读取现有的 conftest.py
    if conftest_file.exists():
        with open(conftest_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否已经导入了 mock_data
        if "from .mock_data import" not in content:
            # 在文件开头添加导入
            import_line = "from .mock_data import *\n\n"
            content = import_line + content

            # 保存更新后的文件
            with open(conftest_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"已更新 {conftest_file} 以导入 mock 数据")
        else:
            print(f"{conftest_file} 已经导入了 mock 数据")
    else:
        print(f"警告: {conftest_file} 不存在")


def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        print(f"错误: tests 目录不存在: {tests_dir}")
        return

    # 生成真实数据
    all_results = generate_mock_data()

    # 打印结果摘要
    print("\n" + "=" * 60)
    print("生成的真实 Mock 数据摘要")
    print("=" * 60)

    for name, result in all_results.items():
        print(f"\n{name.upper()} 命令结果:")
        print(f"  命令: {result['command']}")
        print(f"  退出码: {result['exit_code']}")
        print(f"  持续时间: {result['duration']}s")
        print(f"  成功: {result['success']}")
        print(f"  输出长度: {len(result['stdout'])} 字符")
        print(f"  错误长度: {len(result['stderr'])} 字符")

    # 保存到 tests 目录
    mock_file = save_mock_data_to_tests(all_results, tests_dir)

    # 更新 conftest.py
    update_conftest_py(tests_dir)

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"Mock 数据已保存到: {mock_file}")
    print("conftest.py 已更新以使用这些 mock 数据")
    print("\n现在可以在测试中直接使用这些真实的 mock 数据了！")


if __name__ == "__main__":
    main()
