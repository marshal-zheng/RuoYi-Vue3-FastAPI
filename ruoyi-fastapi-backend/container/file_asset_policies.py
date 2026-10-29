"""Composition root for file asset owner policies.

Every business field that stores assets registers its policy here explicitly (generated businesses
included); an unregistered purpose or owner type is rejected by the file asset module.
"""

from __future__ import annotations

from modules.file_assets.application.composition import set_policy_loader


def build_file_asset_policies():
    from modules.system.application.file_asset_policies import NoticeImagePolicy, UserAvatarPolicy  # noqa: PLC0415

    return [
        UserAvatarPolicy(),
        NoticeImagePolicy(),
        # Generated business policies are appended here, e.g. `DemoAttachmentAssetPolicy()`.
    ]


set_policy_loader(build_file_asset_policies)
