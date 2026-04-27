"""
MyBagHub — NiceGUI frontend entry point.

Pages
-----
/               → redirect to /login or /projects
/login          → Login form
/register       → Registration form
/projects       → Project list + create
/projects/{name}→ Versions, audit log, members management

Run:
    python -m frontend.app
"""
from __future__ import annotations

from nicegui import ui

from frontend.config import CONFIG

# Register all pages (importing the modules triggers the @ui.page decorators)
import frontend.pages.server_select    # noqa: F401, E402
import frontend.pages.root             # noqa: F401, E402
import frontend.pages.login            # noqa: F401, E402
import frontend.pages.register         # noqa: F401, E402
import frontend.pages.projects         # noqa: F401, E402
import frontend.pages.project_detail   # noqa: F401, E402

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host=CONFIG.get("FRONTEND_HOST", "0.0.0.0"),
        port=int(CONFIG.get("FRONTEND_PORT", 8080)),
        title="MyBagHub",
        storage_secret=CONFIG.get("STORAGE_SECRET", "nicegui-fallback-secret"),
        show=False,
        reload=False,
    )
