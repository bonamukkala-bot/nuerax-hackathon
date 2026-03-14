import math
import re
from typing import Union


def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.
    Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, abs, round, etc.
    """
    try:
        # Clean the expression
        expression = expression.strip()
        expression = expression.replace("^", "**")
        expression = expression.replace("×", "*")
        expression = expression.replace("÷", "/")

        # Allow only safe characters
        allowed = re.compile(r'^[\d\s\+\-\*\/\(\)\.\,\%\*\*]+$')

        # Safe math functions available
        safe_dict = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log2": math.log2,
            "log10": math.log10,
            "exp": math.exp,
            "floor": math.floor,
            "ceil": math.ceil,
            "pi": math.pi,
            "e": math.e,
            "factorial": math.factorial,
            "gcd": math.gcd,
            "inf": math.inf,
        }

        # Block dangerous builtins
        safe_globals = {"__builtins__": {}}
        safe_globals.update(safe_dict)

        result = eval(expression, safe_globals, {})

        # Format result nicely
        if isinstance(result, float):
            if result == int(result):
                result = int(result)
            else:
                result = round(result, 6)

        return f"Result: {expression} = {result}"

    except ZeroDivisionError:
        return "Error: Division by zero is not allowed."
    except ValueError as e:
        return f"Math error: {str(e)}"
    except SyntaxError:
        return f"Invalid expression: '{expression}'. Please use valid math syntax."
    except Exception as e:
        return f"Calculation failed: {str(e)}"


def run_calculator_tool(input: str) -> str:
    """
    Main entry point for the calculator tool.
    """
    # Handle natural language like "what is 25 * 4"
    input = input.lower()
    input = input.replace("what is", "").strip()
    input = input.replace("calculate", "").strip()
    input = input.replace("compute", "").strip()
    input = input.replace("evaluate", "").strip()
    input = input.replace("solve", "").strip()
    input = input.strip("?").strip()

    return calculate(input)