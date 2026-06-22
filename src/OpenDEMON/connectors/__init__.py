"""Data source connectors for Deep Research."""

from DEMON.connectors._stubs import (
    Attachment,
    BaseConnector,
    Document,
    SyncStatus,
)
from DEMON.connectors.store import KnowledgeStore

__all__ = ["Attachment", "BaseConnector", "Document", "KnowledgeStore", "SyncStatus"]

# Auto-register built-in connectors
import DEMON.connectors.obsidian  # noqa: F401

try:
    import DEMON.connectors.gmail  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.gmail_imap  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.gdrive  # noqa: F401
except ImportError:
    pass  # httpx may not be installed

try:
    import DEMON.connectors.notion  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.granola  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.gcontacts  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.imessage  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.apple_notes  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.apple_music  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.apple_contacts  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.slack_connector  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.outlook  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.gcalendar  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.dropbox  # noqa: F401
except ImportError:
    pass  # httpx may not be installed

try:
    import DEMON.connectors.whatsapp  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.oura  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.apple_health  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.strava  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.spotify  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.google_tasks  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.weather  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.github_notifications  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.hackernews  # noqa: F401
except ImportError:
    pass

try:
    import DEMON.connectors.news_rss  # noqa: F401
except ImportError:
    pass
