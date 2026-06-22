"""Tools primitive — tool system with ABC interface and built-in tools."""

from __future__ import annotations

from DEMON.tools._stubs import BaseTool, ToolExecutor, ToolSpec

# Import built-in tools to trigger @ToolRegistry.register() decorators.
# Each is wrapped in try/except so the package loads even before the
# individual tool modules are created.
try:
    import DEMON.tools.calculator  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.think  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.retrieval  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.llm_tool  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.file_read  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.web_search  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.code_interpreter  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.code_interpreter_docker  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.repl  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.storage_tools  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.mcp_adapter  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.channel_tools  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.http_request  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.docker_shell_exec  # noqa: F401
    import DEMON.tools.shell_exec  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.memory_manage  # noqa: F401
except ImportError:
    pass
try:
    import DEMON.tools.user_profile_manage  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.skill_manage  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.file_write  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.apply_patch  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.git_tool  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.db_query  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.pdf_tool  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.image_tool  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.audio_tool  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.knowledge_tools  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.text_to_speech  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.tools.digest_collect  # noqa: F401
except ImportError:
    pass

__all__ = ["BaseTool", "ToolExecutor", "ToolSpec"]
