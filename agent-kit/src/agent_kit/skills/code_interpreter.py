"""受限代码解释器（仅允许 print 与简单赋值）。"""

import ast


class _SafeInterpreter(ast.NodeVisitor):
    def __init__(self) -> None:
        self._locals: dict = {}
        self.output: list[str] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise ValueError("only simple assignment allowed")
        value = self._eval(node.value)
        self._locals[node.targets[0].id] = value

    def visit_Expr(self, node: ast.Expr) -> None:
        self._eval(node.value)

    def _eval(self, node: ast.AST):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self._locals[node.id]
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
        ):
            left, right = self._eval(node.left), self._eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            args = [self._eval(a) for a in node.args]
            self.output.append(" ".join(str(a) for a in args))
            return None
        raise ValueError(f"disallowed node: {type(node).__name__}")


def run_code_snippet(code: str, **_: object) -> dict:
    tree = ast.parse(code, mode="exec")
    interp = _SafeInterpreter()
    for stmt in tree.body:
        if isinstance(stmt, (ast.Assign, ast.Expr)):
            interp.visit(stmt)
        else:
            raise ValueError("only assign and expr statements")
    return {"stdout": "\n".join(interp.output), "locals": interp._locals}