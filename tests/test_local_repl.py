"""Comprehensive tests for LocalREPL environment."""

import os

from rlm.environments.local_repl import LocalREPL


class TestLocalREPLBasic:
    """Basic functionality tests for LocalREPL."""

    def test_simple_execution(self):
        """Test basic code execution."""
        repl = LocalREPL()
        result = repl.execute_code("x = 1 + 2")
        assert result.stderr == ""
        assert repl.locals["x"] == 3
        repl.cleanup()

    def test_print_output(self):
        """Test that print statements are captured."""
        repl = LocalREPL()
        result = repl.execute_code("print('Hello, World!')")
        assert "Hello, World!" in result.stdout
        repl.cleanup()

    def test_error_handling(self):
        """Test that errors are captured in stderr."""
        repl = LocalREPL()
        result = repl.execute_code("1 / 0")
        assert "ZeroDivisionError" in result.stderr
        repl.cleanup()

    def test_syntax_error(self):
        """Test syntax error handling."""
        repl = LocalREPL()
        result = repl.execute_code("def broken(")
        assert "SyntaxError" in result.stderr
        repl.cleanup()


class TestLocalREPLPersistence:
    """Tests for state persistence across executions."""

    def test_variable_persistence(self):
        """Test that variables persist across multiple code executions."""
        repl = LocalREPL()

        result1 = repl.execute_code("x = 42")
        assert result1.stderr == ""
        assert repl.locals["x"] == 42

        result2 = repl.execute_code("y = x + 8")
        assert result2.stderr == ""
        assert repl.locals["y"] == 50

        result3 = repl.execute_code("print(y)")
        assert "50" in result3.stdout

        repl.cleanup()

    def test_function_persistence(self):
        """Test that defined functions persist."""
        repl = LocalREPL()

        repl.execute_code(
            """
def greet(name):
    return f"Hello, {name}!"
"""
        )

        result = repl.execute_code("print(greet('World'))")
        assert "Hello, World!" in result.stdout
        repl.cleanup()

    def test_list_comprehension(self):
        """Test that list comprehensions work."""
        repl = LocalREPL()

        repl.execute_code("squares = [x**2 for x in range(5)]")
        assert repl.locals["squares"] == [0, 1, 4, 9, 16]

        result = repl.execute_code("print(sum(squares))")
        assert "30" in result.stdout
        repl.cleanup()


class TestLocalREPLBuiltins:
    """Tests for safe builtins and blocked functions."""

    def test_safe_builtins_available(self):
        """Test that safe builtins are available."""
        repl = LocalREPL()

        # Test various safe builtins
        _ = repl.execute_code("x = len([1, 2, 3])")
        assert repl.locals["x"] == 3

        _ = repl.execute_code("y = sum([1, 2, 3, 4])")
        assert repl.locals["y"] == 10

        _ = repl.execute_code("z = sorted([3, 1, 2])")
        assert repl.locals["z"] == [1, 2, 3]

        repl.cleanup()

    def test_imports_work(self):
        """Test that imports work."""
        repl = LocalREPL()
        result = repl.execute_code("import math\nx = math.pi")
        assert result.stderr == ""
        assert abs(repl.locals["x"] - 3.14159) < 0.001
        repl.cleanup()


class TestLocalREPLContextManager:
    """Tests for context manager usage."""

    def test_context_manager(self):
        """Test using LocalREPL as context manager."""
        with LocalREPL() as repl:
            _ = repl.execute_code("x = 100")
            assert repl.locals["x"] == 100


class TestLocalREPLHelpers:
    """Tests for helper functions (FINAL_VAR, etc.)."""

    def test_final_var_existing(self):
        """Test FINAL_VAR with existing variable."""
        repl = LocalREPL()
        repl.execute_code("answer = 42")
        _ = repl.execute_code("result = FINAL_VAR('answer')")
        assert repl.locals["result"] == "42"
        repl.cleanup()

    def test_final_var_missing(self):
        """Test FINAL_VAR with non-existent variable."""
        repl = LocalREPL()
        _ = repl.execute_code("result = FINAL_VAR('nonexistent')")
        assert "Error" in repl.locals["result"]
        repl.cleanup()

    def test_llm_query_no_handler(self):
        """Test llm_query without handler configured."""
        repl = LocalREPL()
        _ = repl.execute_code("response = llm_query('test')")
        assert "Error" in repl.locals["response"]
        repl.cleanup()


class TestLocalREPLContext:
    """Tests for context loading."""

    def test_string_context(self):
        """Test loading string context."""
        repl = LocalREPL(context_payload="This is the context data.")
        assert "context" in repl.locals
        assert repl.locals["context"] == "This is the context data."
        repl.cleanup()

    def test_dict_context(self):
        """Test loading dict context."""
        repl = LocalREPL(context_payload={"key": "value", "number": 42})
        assert "context" in repl.locals
        assert repl.locals["context"]["key"] == "value"
        assert repl.locals["context"]["number"] == 42
        repl.cleanup()

    def test_list_context(self):
        """Test loading list context."""
        repl = LocalREPL(context_payload=[1, 2, 3, "four"])
        assert "context" in repl.locals
        assert repl.locals["context"] == [1, 2, 3, "four"]
        repl.cleanup()


class TestLocalREPLCleanup:
    """Tests for cleanup behavior."""

    def test_cleanup_clears_state(self):
        """Test that cleanup clears the namespace."""
        repl = LocalREPL()
        repl.execute_code("x = 42")
        assert "x" in repl.locals
        repl.cleanup()
        assert len(repl.locals) == 0

    def test_temp_dir_created_and_cleaned(self):
        """Test that temp directory is created and cleaned up."""
        repl = LocalREPL()
        temp_dir = repl.temp_dir
        assert os.path.exists(temp_dir)
        repl.cleanup()
        assert not os.path.exists(temp_dir)


class TestLocalREPLMultiContext:
    """Tests for multi-context support."""

    def test_add_context_versioning(self):
        """Test that add_context creates versioned variables."""
        repl = LocalREPL()
        repl.add_context("First", 0)
        repl.add_context("Second", 1)
        assert repl.locals["context_0"] == "First"
        assert repl.locals["context_1"] == "Second"
        assert repl.locals["context"] == "First"
        assert repl.get_context_count() == 2
        repl.cleanup()

    def test_update_handler_address(self):
        """Test handler address can be updated."""
        repl = LocalREPL(lm_handler_address=("127.0.0.1", 5000))
        repl.update_handler_address(("127.0.0.1", 6000))
        assert repl.lm_handler_address == ("127.0.0.1", 6000)
        repl.cleanup()

    def test_add_context_auto_increment(self):
        """Test that add_context auto-increments when no index provided."""
        repl = LocalREPL()
        idx1 = repl.add_context("First")
        idx2 = repl.add_context("Second")
        assert idx1 == 0
        assert idx2 == 1
        assert repl.locals["context_0"] == "First"
        assert repl.locals["context_1"] == "Second"
        assert repl.get_context_count() == 2
        repl.cleanup()


class TestLocalREPLHistory:
    """Tests for message history storage in LocalREPL."""

    def test_add_history_basic(self):
        """Test that add_history stores message history correctly."""
        repl = LocalREPL()

        history = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        index = repl.add_history(history)

        assert index == 0
        assert "history_0" in repl.locals
        assert "history" in repl.locals  # alias
        assert repl.locals["history_0"] == history
        assert repl.locals["history"] == history
        assert repl.get_history_count() == 1

        repl.cleanup()

    def test_add_multiple_histories(self):
        """Test adding multiple conversation histories."""
        repl = LocalREPL()

        history1 = [{"role": "user", "content": "First conversation"}]
        history2 = [{"role": "user", "content": "Second conversation"}]

        repl.add_history(history1)
        repl.add_history(history2)

        assert repl.get_history_count() == 2
        assert repl.locals["history_0"] == history1
        assert repl.locals["history_1"] == history2
        assert repl.locals["history"] == history1  # alias stays on first

        repl.cleanup()

    def test_history_accessible_via_code(self):
        """Test that stored history is accessible via code execution."""
        repl = LocalREPL()

        history = [{"role": "user", "content": "Test message"}]
        repl.add_history(history)

        result = repl.execute_code("msg = history[0]['content']")
        assert result.stderr == ""
        assert repl.locals["msg"] == "Test message"

        repl.cleanup()

    def test_history_is_copy(self):
        """Test that stored history is a copy, not a reference."""
        repl = LocalREPL()

        history = [{"role": "user", "content": "Original"}]
        repl.add_history(history)

        # Modify original
        history[0]["content"] = "Modified"

        # Stored copy should be unchanged
        assert repl.locals["history_0"][0]["content"] == "Original"

        repl.cleanup()
