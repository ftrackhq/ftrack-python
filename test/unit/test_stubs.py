"""Verify completeness and correctness of .pyi stub files against source."""

import ast
import pathlib
import textwrap

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SOURCE_ROOT = PROJECT_ROOT / "source" / "ftrack_api"
STUBS_ROOT = PROJECT_ROOT / "stubs" / "ftrack_api"

# Dunder methods conventionally omitted from stubs.
EXCLUDED_DUNDERS = frozenset({"__repr__", "__str__"})

# ── AST helpers ──────────────────────────────────────────────────────────────


def _extract_params(func_node):
    """Return a list of parameter names from a function/method AST node."""
    args = func_node.args
    params = [a.arg for a in args.posonlyargs]
    params.extend(a.arg for a in args.args)
    if args.vararg:
        params.append(f"*{args.vararg.arg}")
    params.extend(a.arg for a in args.kwonlyargs)
    if args.kwarg:
        params.append(f"**{args.kwarg.arg}")
    return params


def _decorator_names(node):
    """Return set of decorator name strings for a function/class node."""
    names = set()
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            names.add(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.add(dec.attr)
    return names


def _is_property(func_node):
    return "property" in _decorator_names(func_node)


def _is_property_setter(func_node):
    return "setter" in _decorator_names(func_node)


def _is_namedtuple_assignment(node):
    """Check if an ast.Assign is a collections.namedtuple() call."""
    if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
        return False
    func = node.value.func
    if isinstance(func, ast.Attribute) and func.attr == "namedtuple":
        return True
    if isinstance(func, ast.Name) and func.id == "namedtuple":
        return True
    return False


def _extract_class_api(class_node):
    """Extract methods, properties, and class-level attrs from a ClassDef."""
    methods = {}
    properties = {}
    attrs = []

    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_property(item):
                has_setter = False
                # Look ahead for setter in same class body
                for sibling in class_node.body:
                    if (
                        isinstance(sibling, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and sibling.name == item.name
                        and _is_property_setter(sibling)
                    ):
                        has_setter = True
                        break
                properties[item.name] = {"has_setter": has_setter}
            elif _is_property_setter(item):
                # Already handled via the getter above
                pass
            else:
                methods[item.name] = _extract_params(item)
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    attrs.append(target.id)
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            attrs.append(item.target.id)

    return {"methods": methods, "properties": properties, "attrs": attrs}


def _parse_module_api(filepath):
    """Parse a .py/.pyi file and return its API surface.

    Returns dict with keys: classes, functions, module_attrs.
    """
    tree = ast.parse(filepath.read_text(), filename=str(filepath))
    api = {"classes": {}, "functions": {}, "module_attrs": []}

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            api["classes"][node.name] = _extract_class_api(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            api["functions"][node.name] = _extract_params(node)
        elif _is_namedtuple_assignment(node):
            # Treat namedtuple assignments as classes (stubs define them as
            # NamedTuple classes).
            for target in node.targets:
                if isinstance(target, ast.Name):
                    api["classes"][target.id] = {
                        "methods": {},
                        "properties": {},
                        "attrs": [],
                    }
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    api["module_attrs"].append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            api["module_attrs"].append(node.target.id)

    return api


# ── Caching & discovery ─────────────────────────────────────────────────────

_api_cache = {}


def _get_api(filepath):
    """Return parsed API for *filepath*, caching the result."""
    filepath = filepath.resolve()
    if filepath not in _api_cache:
        if filepath.exists():
            _api_cache[filepath] = _parse_module_api(filepath)
        else:
            _api_cache[filepath] = {
                "classes": {},
                "functions": {},
                "module_attrs": [],
            }
    return _api_cache[filepath]


def _discover_source_modules():
    """Return sorted list of relative paths for all source .py files."""
    return sorted(p.relative_to(SOURCE_ROOT) for p in SOURCE_ROOT.rglob("*.py"))


def _stub_path_for(source_rel):
    """Return the expected stub path for a source module relative path."""
    return STUBS_ROOT / source_rel.with_suffix(".pyi")


def _is_public(name):
    """True for names that should appear in stubs (public + most dunders)."""
    if name.startswith("__") and name.endswith("__"):
        return name not in EXCLUDED_DUNDERS
    return not name.startswith("_")


# ── Discovery for parametrization ───────────────────────────────────────────

_source_modules = _discover_source_modules()


def _discover_classes():
    items = []
    for mod in _source_modules:
        source_api = _get_api(SOURCE_ROOT / mod)
        for class_name in source_api["classes"]:
            items.append((mod, class_name))
    return items


def _discover_public_methods():
    items = []
    for mod in _source_modules:
        source_api = _get_api(SOURCE_ROOT / mod)
        for class_name, class_info in source_api["classes"].items():
            for method_name in class_info["methods"]:
                if _is_public(method_name):
                    items.append((mod, class_name, method_name))
            for prop_name in class_info["properties"]:
                if _is_public(prop_name):
                    items.append((mod, class_name, prop_name))
    return items


def _discover_public_functions():
    items = []
    for mod in _source_modules:
        source_api = _get_api(SOURCE_ROOT / mod)
        for func_name in source_api["functions"]:
            if _is_public(func_name):
                items.append((mod, func_name))
    return items


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "module_rel_path",
    _source_modules,
    ids=[str(p) for p in _source_modules],
)
def test_stub_file_exists(module_rel_path):
    """Every source module must have a corresponding .pyi stub."""
    stub = _stub_path_for(module_rel_path)
    assert stub.exists(), f"Missing stub file for {module_rel_path}"


_classes = _discover_classes()


@pytest.mark.parametrize(
    "module_path,class_name",
    _classes,
    ids=[f"{m}::{c}" for m, c in _classes],
)
def test_class_exists_in_stub(module_path, class_name):
    """Every class in source must exist in the stub."""
    stub = _stub_path_for(module_path)
    if not stub.exists():
        pytest.skip("stub file missing")
    stub_api = _get_api(stub)
    assert (
        class_name in stub_api["classes"]
    ), f"Class {class_name!r} missing from stub {stub.relative_to(PROJECT_ROOT)}"


_methods = _discover_public_methods()


@pytest.mark.parametrize(
    "module_path,class_name,method_name",
    _methods,
    ids=[f"{m}::{c}::{meth}" for m, c, meth in _methods],
)
def test_method_exists_in_stub(module_path, class_name, method_name):
    """Every public method/property in a source class must exist in the stub."""
    stub = _stub_path_for(module_path)
    if not stub.exists():
        pytest.skip("stub file missing")
    stub_api = _get_api(stub)
    if class_name not in stub_api["classes"]:
        pytest.skip("class missing from stub")

    stub_class = stub_api["classes"][class_name]
    in_methods = method_name in stub_class["methods"]
    in_properties = method_name in stub_class["properties"]
    in_attrs = method_name in stub_class["attrs"]

    assert (
        in_methods or in_properties or in_attrs
    ), f"Method/property {class_name}.{method_name!r} missing from stub"


@pytest.mark.parametrize(
    "module_path,class_name,method_name",
    _methods,
    ids=[f"{m}::{c}::{meth}" for m, c, meth in _methods],
)
def test_method_params_match(module_path, class_name, method_name):
    """Parameter names must match between source and stub for each method."""
    stub = _stub_path_for(module_path)
    if not stub.exists():
        pytest.skip("stub file missing")
    stub_api = _get_api(stub)
    source_api = _get_api(SOURCE_ROOT / module_path)

    if class_name not in stub_api["classes"]:
        pytest.skip("class missing from stub")

    source_class = source_api["classes"][class_name]
    stub_class = stub_api["classes"][class_name]

    # Property getters always have just (self) — skip param comparison.
    if method_name in source_class["properties"]:
        # But verify the setter signature if present in source.
        source_prop = source_class["properties"][method_name]
        if source_prop["has_setter"]:
            stub_prop = stub_class.get("properties", {}).get(method_name)
            if stub_prop is not None:
                assert stub_prop["has_setter"], (
                    f"Property {class_name}.{method_name} has setter in source "
                    f"but not in stub"
                )
        return

    # Regular method — compare parameter names.
    if method_name not in stub_class["methods"]:
        # Already flagged by test_method_exists_in_stub; may be an attr in stub.
        pytest.skip("method not present as a callable in stub")

    source_params = source_class["methods"][method_name]
    stub_params = stub_class["methods"][method_name]

    assert source_params == stub_params, (
        f"{class_name}.{method_name} params differ:\n"
        f"  source: {source_params}\n"
        f"  stub:   {stub_params}"
    )


_functions = _discover_public_functions()


@pytest.mark.parametrize(
    "module_path,func_name",
    _functions,
    ids=[f"{m}::{f}" for m, f in _functions],
)
def test_function_exists_in_stub(module_path, func_name):
    """Every public module-level function in source must exist in the stub."""
    stub = _stub_path_for(module_path)
    if not stub.exists():
        pytest.skip("stub file missing")
    stub_api = _get_api(stub)
    assert func_name in stub_api["functions"], (
        f"Function {func_name!r} missing from stub " f"{stub.relative_to(PROJECT_ROOT)}"
    )


@pytest.mark.parametrize(
    "module_path,func_name",
    _functions,
    ids=[f"{m}::{f}" for m, f in _functions],
)
def test_function_params_match(module_path, func_name):
    """Parameter names must match between source and stub for functions."""
    stub = _stub_path_for(module_path)
    if not stub.exists():
        pytest.skip("stub file missing")
    stub_api = _get_api(stub)
    source_api = _get_api(SOURCE_ROOT / module_path)

    if func_name not in stub_api["functions"]:
        pytest.skip("function missing from stub")

    source_params = source_api["functions"][func_name]
    stub_params = stub_api["functions"][func_name]

    assert source_params == stub_params, (
        f"Function {func_name} params differ:\n"
        f"  source: {source_params}\n"
        f"  stub:   {stub_params}"
    )


# ── Self-tests for the harness helpers ───────────────────────────────────────


def _write_temp_py(tmp_path, code, name="module.py"):
    """Write *code* to a temp file and return its Path."""
    p = tmp_path / name
    p.write_text(textwrap.dedent(code))
    return p


def test_parse_detects_classes(tmp_path):
    """_parse_module_api should find all classes by name."""
    source = _write_temp_py(
        tmp_path,
        """\
        class Foo:
            pass

        class _Bar:
            pass
        """,
    )
    api = _parse_module_api(source)
    assert "Foo" in api["classes"]
    assert "_Bar" in api["classes"]
    assert len(api["classes"]) == 2


def test_parse_detects_methods(tmp_path):
    """Public methods and dunders extracted; private methods excluded from public API."""
    source = _write_temp_py(
        tmp_path,
        """\
        class Foo:
            def __init__(self, x):
                pass
            def public(self, a, b):
                pass
            def _private(self):
                pass
            def __len__(self):
                return 0
        """,
    )
    api = _parse_module_api(source)
    methods = api["classes"]["Foo"]["methods"]
    # All methods are extracted (filtering is done by _is_public, not the parser).
    assert "__init__" in methods
    assert "public" in methods
    assert "_private" in methods
    assert "__len__" in methods
    # _is_public filters correctly.
    assert _is_public("__init__")
    assert _is_public("public")
    assert not _is_public("_private")
    assert _is_public("__len__")


def test_parse_detects_properties(tmp_path):
    """@property and @x.setter detected with has_setter flag."""
    source = _write_temp_py(
        tmp_path,
        """\
        class Foo:
            @property
            def read_only(self):
                return 1

            @property
            def read_write(self):
                return 2

            @read_write.setter
            def read_write(self, value):
                pass
        """,
    )
    api = _parse_module_api(source)
    props = api["classes"]["Foo"]["properties"]
    assert "read_only" in props
    assert props["read_only"]["has_setter"] is False
    assert "read_write" in props
    assert props["read_write"]["has_setter"] is True
    # Properties should not appear in methods.
    assert "read_only" not in api["classes"]["Foo"]["methods"]
    assert "read_write" not in api["classes"]["Foo"]["methods"]


def test_parse_detects_namedtuple(tmp_path):
    """collections.namedtuple() assignments parsed as classes."""
    source = _write_temp_py(
        tmp_path,
        """\
        import collections

        Point = collections.namedtuple("Point", ["x", "y"])
        CONSTANT = 42
        """,
    )
    api = _parse_module_api(source)
    assert "Point" in api["classes"]
    # CONSTANT should be a module attr, not a class.
    assert "Point" not in api["module_attrs"]
    assert "CONSTANT" in api["module_attrs"]


def test_parse_detects_functions(tmp_path):
    """Module-level functions extracted with full param signatures."""
    source = _write_temp_py(
        tmp_path,
        """\
        def simple(a, b):
            pass

        def with_varargs(a, *args, key=None, **kwargs):
            pass
        """,
    )
    api = _parse_module_api(source)
    assert api["functions"]["simple"] == ["a", "b"]
    assert api["functions"]["with_varargs"] == ["a", "*args", "key", "**kwargs"]


def test_parse_detects_module_attrs(tmp_path):
    """Module-level assignments and annotated assignments detected."""
    source = _write_temp_py(
        tmp_path,
        """\
        CONSTANT = 42
        logger: object = None
        """,
    )
    api = _parse_module_api(source)
    assert "CONSTANT" in api["module_attrs"]
    assert "logger" in api["module_attrs"]


def test_is_public_filtering():
    """_is_public accepts public + most dunders, rejects private + excluded dunders."""
    assert _is_public("foo") is True
    assert _is_public("Bar") is True
    assert _is_public("__init__") is True
    assert _is_public("__getitem__") is True
    # Private.
    assert _is_public("_private") is False
    assert _is_public("_PrivateClass") is False
    # Excluded dunders.
    assert _is_public("__repr__") is False
    assert _is_public("__str__") is False


def test_missing_class_detected(tmp_path):
    """A class present in source but absent in stub is detectable."""
    source = _write_temp_py(
        tmp_path,
        """\
        class Foo:
            pass

        class Bar:
            pass
        """,
        name="source.py",
    )
    stub = _write_temp_py(
        tmp_path,
        """\
        class Foo: ...
        """,
        name="stub.pyi",
    )
    source_api = _parse_module_api(source)
    stub_api = _parse_module_api(stub)
    assert "Foo" in stub_api["classes"]
    assert "Bar" not in stub_api["classes"]
    # Confirm source has both.
    assert "Foo" in source_api["classes"]
    assert "Bar" in source_api["classes"]


def test_missing_method_detected(tmp_path):
    """A method present in source class but absent in stub class is detectable."""
    source = _write_temp_py(
        tmp_path,
        """\
        class Foo:
            def bar(self):
                pass
            def baz(self, x):
                pass
        """,
        name="source.py",
    )
    stub = _write_temp_py(
        tmp_path,
        """\
        class Foo:
            def bar(self): ...
        """,
        name="stub.pyi",
    )
    source_api = _parse_module_api(source)
    stub_api = _parse_module_api(stub)
    stub_methods = stub_api["classes"]["Foo"]["methods"]
    source_methods = source_api["classes"]["Foo"]["methods"]
    assert "bar" in stub_methods
    assert "baz" not in stub_methods
    assert "baz" in source_methods


def test_param_mismatch_detected(tmp_path):
    """Differing parameter lists between source and stub are detectable."""
    source = _write_temp_py(
        tmp_path,
        """\
        class Foo:
            def bar(self, a, b):
                pass
        """,
        name="source.py",
    )
    stub = _write_temp_py(
        tmp_path,
        """\
        class Foo:
            def bar(self, a): ...
        """,
        name="stub.pyi",
    )
    source_params = _parse_module_api(source)["classes"]["Foo"]["methods"]["bar"]
    stub_params = _parse_module_api(stub)["classes"]["Foo"]["methods"]["bar"]
    assert source_params == ["self", "a", "b"]
    assert stub_params == ["self", "a"]
    assert source_params != stub_params
