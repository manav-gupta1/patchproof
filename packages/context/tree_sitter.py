from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SyntaxContext:
    enclosing_symbol: str | None
    node_type: str | None
    node_start_line: int | None
    node_end_line: int | None
    symbols: list[dict] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)


class TreeSitterUnavailable(RuntimeError):
    pass


class TreeSitterContextParser:
    """Extract structural context from Python and JavaScript/TypeScript source."""

    _SYMBOL_NODES = {
        "function_definition", "async_function_definition", "class_definition",
        "function_declaration", "generator_function_declaration", "method_definition",
        "class_declaration", "arrow_function",
    }
    _CALL_NODES = {"call", "call_expression"}

    def parse(self, source: str, language: str, finding_line: int) -> SyntaxContext:
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_javascript as tsjavascript
            import tree_sitter_python as tspython
        except ImportError as exc:
            raise TreeSitterUnavailable(
                "Tree-sitter dependencies are not installed; install the project dependencies first"
            ) from exc

        key = language.lower()
        if key in {"python", "py"}:
            grammar = Language(tspython.language())
        elif key in {"javascript", "js", "typescript", "ts"}:
            grammar = Language(tsjavascript.language())
        else:
            return SyntaxContext(None, None, None, None)

        parser = Parser(grammar)
        tree = parser.parse(source.encode("utf-8"))
        row = max(0, finding_line - 1)
        target = tree.root_node.descendant_for_point_range((row, 0), (row, 0))

        enclosing = None
        node = target
        while node is not None:
            if node.type in self._SYMBOL_NODES:
                enclosing = node
                break
            node = node.parent

        symbols: list[dict] = []
        calls: list[dict] = []
        self._walk(tree.root_node, source, symbols, calls)

        if enclosing is None:
            return SyntaxContext(None, None, None, None, symbols=symbols[:100], calls=calls[:100])

        return SyntaxContext(
            enclosing_symbol=self._symbol_name(enclosing, source),
            node_type=enclosing.type,
            node_start_line=enclosing.start_point[0] + 1,
            node_end_line=enclosing.end_point[0] + 1,
            symbols=symbols[:100],
            calls=calls[:100],
        )

    def _walk(self, node, source: str, symbols: list[dict], calls: list[dict]) -> None:
        if node.type in self._SYMBOL_NODES:
            name = self._symbol_name(node, source)
            if name:
                symbols.append({
                    "name": name, "kind": node.type,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "signature": self._signature(node, source),
                })

        if node.type in self._CALL_NODES:
            function_node = node.child_by_field_name("function")
            if function_node is not None:
                calls.append({
                    "name": self._node_text(function_node, source),
                    "line": node.start_point[0] + 1,
                    "receiver": self._receiver(function_node, source),
                })

        for child in node.children:
            self._walk(child, source, symbols, calls)

    @staticmethod
    def _node_text(node, source: str) -> str:
        raw = source.encode("utf-8")[node.start_byte:node.end_byte]
        return raw.decode("utf-8", errors="replace")

    def _symbol_name(self, node, source: str) -> str | None:
        for field in ("name", "property"):
            child = node.child_by_field_name(field)
            if child is not None:
                return self._node_text(child, source)
        if node.type == "arrow_function":
            return f"anonymous_arrow@{node.start_point[0] + 1}"
        return None

    def _signature(self, node, source: str) -> str | None:
        text = self._node_text(node, source)
        return (text.splitlines()[0].strip() if text else "")[:500] or None

    @staticmethod
    def _receiver(node, source: str) -> str | None:
        if node.type == "attribute":
            obj = node.child_by_field_name("object")
            if obj is not None:
                raw = source.encode("utf-8")[obj.start_byte:obj.end_byte]
                return raw.decode("utf-8", errors="replace")
        return None
