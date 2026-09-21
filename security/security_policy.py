"""Central Jarvis action policy.

Edit this file when adding or changing policy categories. Keep the policy separate
from individual tools so the security model remains auditable and consistent.
"""
from __future__ import annotations

from enum import Enum


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    RESTRICT = "restrict"


# ============================================================
# ALLOW: ordinary local operations.
# ============================================================
ALLOWED_ACTIONS = {
    "open_app", "close_app", "open_file", "open_folder",
    "read_file", "search_local_files", "create_file", "modify_project",
    "run_tests", "run_local_program", "browser_navigate", "browser_read",
    "web_search", "project_learn", "project_refresh", "calculate",
}

# ============================================================
# CONFIRM: actions that can cause irreversible or external effects.
# ============================================================
CONFIRMATION_REQUIRED = {
    "delete_file", "delete_folder", "overwrite_file", "install_software",
    "upload_file", "send_message", "submit_form", "publish_content",
    "git_push", "change_system_settings", "shutdown", "restart",
}

# ============================================================
# RESTRICT: harmful/unauthorized categories.
# These are policy categories, not implementations.
# ============================================================
RESTRICTED_CATEGORIES = {
    "unauthorized_access",
    "credential_theft",
    "malware_deployment",
    "ransomware",
    "data_theft",
    "destructive_activity",
    "security_control_bypass",
    "unauthorized_surveillance",
    "unauthorized_data_exfiltration",
    "fraud_or_theft",
}


def decide(action: str) -> PolicyDecision:
    if action in CONFIRMATION_REQUIRED:
        return PolicyDecision.CONFIRM
    if action in ALLOWED_ACTIONS:
        return PolicyDecision.ALLOW
    return PolicyDecision.RESTRICT
