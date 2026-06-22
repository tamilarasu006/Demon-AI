"""Tools primitive — tool system with ABC interface and built-in tools."""

from __future__ import annotations

from OpenDEMON.tools._stubs import BaseTool, ToolExecutor, ToolSpec

# Import built-in tools to trigger @ToolRegistry.register() decorators.
# Each is wrapped in try/except so the package loads even before the
# individual tool modules are created.
try:
    import OpenDEMON.tools.calculator  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.think  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.retrieval  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.llm_tool  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.file_read  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.web_search  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.code_interpreter  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.code_interpreter_docker  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.repl  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.storage_tools  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.mcp_adapter  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.channel_tools  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.http_request  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.docker_shell_exec  # noqa: F401
    import OpenDEMON.tools.shell_exec  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.memory_manage  # noqa: F401
except ImportError:
    pass
try:
    import OpenDEMON.tools.user_profile_manage  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.skill_manage  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.file_write  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.apply_patch  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.git_tool  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.db_query  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.pdf_tool  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.image_tool  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.audio_tool  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.knowledge_tools  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.text_to_speech  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.tools.digest_collect  # noqa: F401
except ImportError:
    pass

__all__ = ["BaseTool", "ToolExecutor", "ToolSpec"]
