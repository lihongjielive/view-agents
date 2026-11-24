"""Copy article slide images into multi-agent/docx/ (idempotent)."""
from __future__ import annotations

import shutil
from pathlib import Path

ASSETS = Path(
    r"C:\Users\lihj-h\.cursor\projects\f-view-agents-langgraph-agent\assets"
)
ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / "docx"

PAIRS: list[tuple[str, str]] = [
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_cb5f7f5ea221de6cebe2bb87101b4eba-eabd3ad8-d699-41e3-9c65-5e8932402359.jpg",
        "01-execution-protocol-overview.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_16c69105d25a53841c4ed06540059eed-7e9888ac-153e-431e-8a96-d47cfb41186c.jpg",
        "02-refund-response-lost-timeout.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_ceaea6ab842c08928b897232aa692201-180fdcc0-a05c-4931-9bce-7b5eab22ec4f.jpg",
        "03-model-proposes-system-decides.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_f1e251c3685a6f6ef64bd63fbea16b0d-05c42c04-e03c-4512-ba37-8bee3fe4866d.jpg",
        "04-business-key-not-task-id.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_7c1627f65d29e3f28e0c20ce7a1d1289-9a770136-ceab-4644-b5da-daf6fb25dc44.jpg",
        "05-unknown-formal-state.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_aa7f919a686ad4eeb9f26d82efe06539-51e95dea-08d6-4468-b823-e8a683f385d6.jpg",
        "06-outbox-task-and-event.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_d7fbeed1826172f8c46eb4fe4a4f24a8-846870f6-9be8-45e2-8063-ab32feacd1e0.jpg",
        "07-lease-fencing-old-worker.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_50d45a94f97c3fa1e3fb11c0196724ef-177ea36c-b4eb-4ecf-815b-b714b6815c3e.jpg",
        "08-refund-timeout-query-first.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_81d258953492ebca79f95485821fca1b-2f33b598-6afa-4492-8386-dadcc5d1459f.jpg",
        "09-dag-and-tool-gateway-gates.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_ab28083e298c9965fc0bb85a7370a562-c4321892-531c-45bb-8365-21421ba49a87.jpg",
        "10-kafka-lag-vs-task-backlog.jpg",
    ),
    (
        "c__Users_lihj-h_AppData_Roaming_Cursor_User_workspaceStorage_43d6688c0719333b4968f655b1dbb602_images_3e31496c8868af9025334116fa359977-bd86bbb2-d28e-45e2-950b-e22e65a57838.jpg",
        "11-migration-four-steps.jpg",
    ),
]


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for src_name, dst_name in PAIRS:
        src = ASSETS / src_name
        if not src.is_file():
            raise SystemExit(f"missing source: {src}")
        shutil.copy2(src, DST / dst_name)
        print(f"copied -> {dst_name}")
    print(f"total {len(list(DST.glob('*.jpg')))} images in docx/")


if __name__ == "__main__":
    main()