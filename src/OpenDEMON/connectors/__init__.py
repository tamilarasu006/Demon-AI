"""Data source connectors for Deep Research."""

from OpenDEMON.connectors._stubs import (
    Attachment,
    BaseConnector,
    Document,
    SyncStatus,
)
from OpenDEMON.connectors.store import KnowledgeStore

__all__ = ["Attachment", "BaseConnector", "Document", "KnowledgeStore", "SyncStatus"]

# Auto-register built-in connectors
import OpenDEMON.connectors.obsidian  # noqa: F401

try:
    import OpenDEMON.connectors.gmail  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.gmail_imap  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.gdrive  # noqa: F401
except ImportError:
    pass  # httpx may not be installed

try:
    import OpenDEMON.connectors.notion  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.granola  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.gcontacts  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.imessage  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.apple_notes  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.apple_music  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.apple_contacts  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.slack_connector  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.outlook  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.gcalendar  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.dropbox  # noqa: F401
except ImportError:
    pass  # httpx may not be installed

try:
    import OpenDEMON.connectors.whatsapp  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.oura  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.apple_health  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.strava  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.spotify  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.google_tasks  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.weather  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.github_notifications  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.hackernews  # noqa: F401
except ImportError:
    pass

try:
    import OpenDEMON.connectors.news_rss  # noqa: F401
except ImportError:
    pass
