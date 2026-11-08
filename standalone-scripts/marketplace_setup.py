# Подготавливает структуру и данные проекта marketplace.
from __future__ import annotations

import asyncio
import os
import traceback
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, TypeVar

import discord
from dotenv import load_dotenv


GUILD_ID_ENV = "GUILD_ID"
TOKEN_ENV = "DISCORD_TOKEN"

CATEGORY_NAME = "🛒 MARKETPLACE"

VERIFIED_ROLE_NAME = "Verified"
SELLER_ROLE_NAME = "Seller"
VERIFIED_SELLER_ROLE_NAME = "Verified Seller"

OUR_PRODUCTS_CHANNEL_NAME = "our-products"
MARKETPLACE_CHANNEL_NAME = "marketplace"
REVIEWS_CHANNEL_NAME = "reviews"

OUR_PRODUCTS_TAGS = ("AI", "Software", "Services", "Other", "Official")
MARKETPLACE_TAGS = ("AI", "Software", "Services", "Design", "Other")

AUDIT_REASON = "SatashiDcs marketplace setup"

REQUIRED_BOT_PERMISSIONS = ("view_channel", "manage_channels", "manage_roles")

DANGEROUS_MARKETPLACE_ROLE_PERMISSIONS = (
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "ban_members",
    "kick_members",
)

STAFF_ROLE_NAMES = {
    "admin",
    "admins",
    "administrator",
    "administrators",
    "moderator",
    "moderators",
    "mod",
    "mods",
    "staff",
}

STAFF_PERMISSION_SIGNALS = (
    "administrator",
    "manage_guild",
    "manage_channels",
    "manage_roles",
    "manage_messages",
    "manage_threads",
    "ban_members",
    "kick_members",
)

PermissionSpec = Dict[str, Optional[bool]]
ChannelT = TypeVar("ChannelT", bound=discord.abc.GuildChannel)


class SetupError(RuntimeError):
    pass


@dataclass
class Report:
    created: list[str] = field(default_factory=list)
    existing: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_created(self, message: str) -> None:
        self.created.append(message)

    def add_existing(self, message: str) -> None:
        self.existing.append(message)

    def add_updated(self, message: str) -> None:
        self.updated.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def print(self) -> None:
        print("\n=== SatashiDcs Marketplace Setup Report ===")
        self._print_group("Created", self.created)
        self._print_group("Already existed / unchanged", self.existing)
        self._print_group("Updated", self.updated)
        self._print_group("Warnings", self.warnings)
        print("=== Done ===")

    @staticmethod
    def _print_group(title: str, items: list[str]) -> None:
        print(f"\n{title}:")
        if not items:
            print("  - none")
            return
        for item in items:
            print(f"  - {item}")


def make_overwrite(spec: PermissionSpec) -> discord.PermissionOverwrite:
    return discord.PermissionOverwrite(**spec)


def make_overwrites(
    specs: dict[discord.Role, PermissionSpec],
) -> dict[discord.Role, discord.PermissionOverwrite]:
    return {target: make_overwrite(spec) for target, spec in specs.items()}


def target_name(target: discord.Role) -> str:
    return "@everyone" if target.is_default() else target.name


def permission_summary(spec: PermissionSpec) -> str:
    parts = [f"{name}={value}" for name, value in sorted(spec.items())]
    return ", ".join(parts)


def get_unique_role(guild: discord.Guild, name: str, *, required: bool) -> discord.Role | None:
    matches = [role for role in guild.roles if role.name == name]
    if len(matches) > 1:
        ids = ", ".join(str(role.id) for role in matches)
        raise SetupError(f"Found multiple roles named {name!r}: {ids}. Resolve duplicates manually.")
    if not matches:
        if required:
            raise SetupError(
                f"Role {name!r} was not found. The existing verification system must create it; "
                "this setup script will not create Verified automatically."
            )
        return None
    return matches[0]


def get_unique_category(guild: discord.Guild, name: str) -> discord.CategoryChannel | None:
    matches = [channel for channel in guild.categories if channel.name == name]
    if len(matches) > 1:
        ids = ", ".join(str(channel.id) for channel in matches)
        raise SetupError(f"Found multiple categories named {name!r}: {ids}. Resolve duplicates manually.")
    return matches[0] if matches else None


def validate_bot_permissions(guild: discord.Guild) -> None:
    me = guild.me
    if me is None:
        raise SetupError("Could not resolve the bot member in this guild.")

    permissions = me.guild_permissions
    missing = [name for name in REQUIRED_BOT_PERMISSIONS if not getattr(permissions, name)]
    if missing:
        pretty = ", ".join(missing)
        raise SetupError(f"Bot is missing required guild permissions: {pretty}.")


async def ensure_marketplace_role(
    guild: discord.Guild,
    name: str,
    report: Report,
) -> discord.Role:
    role = get_unique_role(guild, name, required=False)
    if role is None:
        role = await guild.create_role(
            name=name,
            permissions=discord.Permissions.none(),
            hoist=False,
            mentionable=False,
            reason=AUDIT_REASON,
        )
        report.add_created(f"role {name}")
        return role

    report.add_existing(f"role {name}")
    return await ensure_no_dangerous_permissions(role, report)


async def ensure_no_dangerous_permissions(role: discord.Role, report: Report) -> discord.Role:
    permissions = discord.Permissions(role.permissions.value)
    removed: list[str] = []

    for permission_name in DANGEROUS_MARKETPLACE_ROLE_PERMISSIONS:
        if getattr(permissions, permission_name):
            setattr(permissions, permission_name, False)
            removed.append(permission_name)

    if not removed:
        return role

    try:
        updated_role = await role.edit(permissions=permissions, reason=AUDIT_REASON)
    except discord.Forbidden as exc:
        raise SetupError(
            f"Role {role.name!r} has dangerous permissions ({', '.join(removed)}), "
            "but the bot cannot edit that role."
        ) from exc

    report.add_updated(f"role {role.name}: removed {', '.join(removed)}")
    return updated_role or role


async def ensure_verified_seller_above_seller(
    seller_role: discord.Role,
    verified_seller_role: discord.Role,
    report: Report,
) -> discord.Role:
    if verified_seller_role > seller_role:
        report.add_existing("role order: Verified Seller is above Seller")
        return verified_seller_role

    try:
        updated_role = await verified_seller_role.edit(
            position=seller_role.position + 1,
            reason=AUDIT_REASON,
        )
    except discord.Forbidden:
        report.add_warning(
            "Could not move Verified Seller above Seller. Move it manually in Server Settings > Roles."
        )
        return verified_seller_role

    report.add_updated("role order: moved Verified Seller above Seller")
    return updated_role or verified_seller_role


def find_staff_roles(
    guild: discord.Guild,
    *,
    verified_role: discord.Role,
    seller_role: discord.Role,
    verified_seller_role: discord.Role,
) -> list[discord.Role]:
    excluded_role_ids = {
        guild.default_role.id,
        verified_role.id,
        seller_role.id,
        verified_seller_role.id,
    }

    staff_roles: list[discord.Role] = []
    for role in guild.roles:
        if role.id in excluded_role_ids or role.managed:
            continue

        permissions = role.permissions
        name_matches = role.name.casefold() in STAFF_ROLE_NAMES
        permission_matches = any(getattr(permissions, name) for name in STAFF_PERMISSION_SIGNALS)
        if name_matches or permission_matches:
            staff_roles.append(role)

    return staff_roles


async def ensure_category(
    guild: discord.Guild,
    verified_role: discord.Role,
    seller_role: discord.Role,
    verified_seller_role: discord.Role,
    staff_roles: Iterable[discord.Role],
    report: Report,
) -> discord.CategoryChannel:
    category_specs: dict[discord.Role, PermissionSpec] = {
        guild.default_role: {"view_channel": False},
        verified_role: {
            "view_channel": True,
            "read_message_history": True,
        },
        seller_role: {
            "view_channel": True,
            "read_message_history": True,
        },
        verified_seller_role: {
            "view_channel": True,
            "read_message_history": True,
        },
    }

    for staff_role in staff_roles:
        category_specs[staff_role] = {
            "view_channel": True,
            "read_message_history": True,
        }

    category = get_unique_category(guild, CATEGORY_NAME)
    if category is None:
        category = await guild.create_category_channel(
            CATEGORY_NAME,
            overwrites=make_overwrites(category_specs),
            reason=AUDIT_REASON,
        )
        report.add_created(f"category {CATEGORY_NAME}")
        return category

    report.add_existing(f"category {CATEGORY_NAME}")
    await ensure_permission_overwrites(category, category_specs, report)
    return category


def find_channels_by_name(guild: discord.Guild, name: str) -> list[discord.abc.GuildChannel]:
    return [channel for channel in guild.channels if channel.name == name]


async def get_existing_channel_or_none(
    guild: discord.Guild,
    category: discord.CategoryChannel,
    name: str,
    expected_type: type[ChannelT],
    report: Report,
) -> ChannelT | None:
    matches = find_channels_by_name(guild, name)
    in_category = [channel for channel in matches if getattr(channel, "category_id", None) == category.id]

    if len(in_category) > 1:
        ids = ", ".join(str(channel.id) for channel in in_category)
        report.add_warning(f"multiple channels named #{name} exist inside {CATEGORY_NAME}: {ids}; skipped")
        return None

    if in_category:
        channel = in_category[0]
        if not isinstance(channel, expected_type):
            report.add_warning(
                f"#{name} exists inside {CATEGORY_NAME}, but has type {channel.__class__.__name__}; skipped"
            )
            return None

        report.add_existing(f"channel #{name}")
        return channel

    if len(matches) > 1:
        ids = ", ".join(f"{channel.__class__.__name__}:{channel.id}" for channel in matches)
        report.add_warning(f"multiple channels named #{name} exist outside {CATEGORY_NAME}: {ids}; skipped")
        return None

    if len(matches) == 1:
        channel = matches[0]
        if not isinstance(channel, expected_type):
            report.add_warning(
                f"#{name} exists, but has type {channel.__class__.__name__}; expected "
                f"{expected_type.__name__}; skipped"
            )
            return None

        updated_channel = await channel.edit(category=category, reason=AUDIT_REASON)
        report.add_updated(f"moved #{name} into {CATEGORY_NAME}")
        return updated_channel or channel

    return None


async def ensure_forum_channel(
    guild: discord.Guild,
    category: discord.CategoryChannel,
    name: str,
    tags: tuple[str, ...],
    permission_specs: dict[discord.Role, PermissionSpec],
    report: Report,
) -> discord.ForumChannel | None:
    channel = await get_existing_channel_or_none(
        guild,
        category,
        name,
        discord.ForumChannel,
        report,
    )

    if channel is None and not find_channels_by_name(guild, name):
        try:
            channel = await category.create_forum(
                name,
                available_tags=[discord.ForumTag(name=tag_name) for tag_name in tags],
                overwrites=make_overwrites(permission_specs),
                reason=AUDIT_REASON,
            )
        except discord.Forbidden as exc:
            raise SetupError(f"Bot cannot create ForumChannel #{name}. Check Manage Channels permission.") from exc
        except discord.HTTPException as exc:
            raise SetupError(
                f"Discord rejected ForumChannel #{name}: {exc}. "
                "Make sure the server has Community enabled; Discord forums require it."
            ) from exc

        report.add_created(f"forum channel #{name}")
        return channel

    if channel is None:
        return None

    await ensure_forum_tags(channel, tags, report)
    await ensure_permission_overwrites(channel, permission_specs, report)
    return channel


async def ensure_text_channel(
    guild: discord.Guild,
    category: discord.CategoryChannel,
    name: str,
    permission_specs: dict[discord.Role, PermissionSpec],
    report: Report,
) -> discord.TextChannel | None:
    channel = await get_existing_channel_or_none(
        guild,
        category,
        name,
        discord.TextChannel,
        report,
    )

    if channel is None and not find_channels_by_name(guild, name):
        try:
            channel = await category.create_text_channel(
                name,
                overwrites=make_overwrites(permission_specs),
                reason=AUDIT_REASON,
            )
        except discord.Forbidden as exc:
            raise SetupError(f"Bot cannot create TextChannel #{name}. Check Manage Channels permission.") from exc

        report.add_created(f"text channel #{name}")
        return channel

    if channel is None:
        return None

    await ensure_permission_overwrites(channel, permission_specs, report)
    return channel


async def ensure_forum_tags(
    channel: discord.ForumChannel,
    required_tags: tuple[str, ...],
    report: Report,
) -> None:
    existing_names = {tag.name for tag in channel.available_tags}
    missing_tags = [tag_name for tag_name in required_tags if tag_name not in existing_names]

    if not missing_tags:
        report.add_existing(f"#{channel.name}: forum tags")
        return

    new_tags = list(channel.available_tags)
    new_tags.extend(discord.ForumTag(name=tag_name) for tag_name in missing_tags)

    try:
        await channel.edit(available_tags=new_tags, reason=AUDIT_REASON)
    except discord.Forbidden as exc:
        raise SetupError(f"Bot cannot edit tags for ForumChannel #{channel.name}.") from exc

    report.add_updated(f"#{channel.name}: added forum tags {', '.join(missing_tags)}")


async def ensure_permission_overwrites(
    channel: discord.abc.GuildChannel,
    specs: dict[discord.Role, PermissionSpec],
    report: Report,
) -> None:
    for target, desired_permissions in specs.items():
        current = channel.overwrites_for(target)
        changed_permissions: PermissionSpec = {}

        for permission_name, desired_value in desired_permissions.items():
            if getattr(current, permission_name) != desired_value:
                setattr(current, permission_name, desired_value)
                changed_permissions[permission_name] = desired_value

        if not changed_permissions:
            report.add_existing(
                f"{channel.name}: overwrite for {target_name(target)} ({permission_summary(desired_permissions)})"
            )
            continue

        try:
            await channel.set_permissions(target, overwrite=current, reason=AUDIT_REASON)
        except discord.Forbidden as exc:
            raise SetupError(
                f"Bot cannot set permissions for {target_name(target)} on {channel.name}."
            ) from exc

        report.add_updated(
            f"{channel.name}: overwrite for {target_name(target)} ({permission_summary(changed_permissions)})"
        )


def build_our_products_permissions(
    guild: discord.Guild,
    verified_role: discord.Role,
    staff_roles: Iterable[discord.Role],
) -> dict[discord.Role, PermissionSpec]:
    specs: dict[discord.Role, PermissionSpec] = {
        guild.default_role: {
            "view_channel": False,
        },
        verified_role: {
            "view_channel": True,
            "read_message_history": True,
            "send_messages": False,
            "create_public_threads": False,
            "create_private_threads": False,
            "send_messages_in_threads": True,
        },
    }

    for staff_role in staff_roles:
        specs[staff_role] = {
            "view_channel": True,
            "read_message_history": True,
            "send_messages": True,
            "create_public_threads": True,
            "send_messages_in_threads": True,
        }

    return specs


def build_marketplace_permissions(
    guild: discord.Guild,
    verified_role: discord.Role,
    seller_role: discord.Role,
    verified_seller_role: discord.Role,
) -> dict[discord.Role, PermissionSpec]:
    return {
        guild.default_role: {
            "view_channel": False,
        },
        verified_role: {
            "view_channel": True,
            "read_message_history": True,
            "send_messages": False,
            "create_public_threads": False,
            "create_private_threads": False,
            "send_messages_in_threads": True,
        },
        seller_role: {
            "view_channel": True,
            "read_message_history": True,
            "send_messages": True,
            "create_public_threads": True,
            "send_messages_in_threads": True,
        },
        verified_seller_role: {
            "view_channel": True,
            "read_message_history": True,
            "send_messages": True,
            "create_public_threads": True,
            "send_messages_in_threads": True,
        },
    }


def build_reviews_permissions(
    guild: discord.Guild,
    verified_role: discord.Role,
) -> dict[discord.Role, PermissionSpec]:
    return {
        guild.default_role: {
            "view_channel": False,
        },
        verified_role: {
            "view_channel": True,
            "read_message_history": True,
            "send_messages": True,
        },
    }


async def setup_marketplace(guild: discord.Guild, report: Report) -> None:
    validate_bot_permissions(guild)

    verified_role = get_unique_role(guild, VERIFIED_ROLE_NAME, required=True)
    assert verified_role is not None
    report.add_existing(f"role {VERIFIED_ROLE_NAME}")

    seller_role = await ensure_marketplace_role(guild, SELLER_ROLE_NAME, report)
    verified_seller_role = await ensure_marketplace_role(guild, VERIFIED_SELLER_ROLE_NAME, report)
    verified_seller_role = await ensure_verified_seller_above_seller(
        seller_role,
        verified_seller_role,
        report,
    )

    staff_roles = find_staff_roles(
        guild,
        verified_role=verified_role,
        seller_role=seller_role,
        verified_seller_role=verified_seller_role,
    )
    if staff_roles:
        staff_role_names = ", ".join(role.name for role in staff_roles)
        report.add_existing(f"staff roles detected for official product posting: {staff_role_names}")
    else:
        report.add_warning(
            "No staff roles detected by name/permissions. Administrators can still bypass channel overwrites."
        )

    category = await ensure_category(
        guild,
        verified_role,
        seller_role,
        verified_seller_role,
        staff_roles,
        report,
    )

    await ensure_forum_channel(
        guild,
        category,
        OUR_PRODUCTS_CHANNEL_NAME,
        OUR_PRODUCTS_TAGS,
        build_our_products_permissions(guild, verified_role, staff_roles),
        report,
    )
    await ensure_forum_channel(
        guild,
        category,
        MARKETPLACE_CHANNEL_NAME,
        MARKETPLACE_TAGS,
        build_marketplace_permissions(guild, verified_role, seller_role, verified_seller_role),
        report,
    )
    await ensure_text_channel(
        guild,
        category,
        REVIEWS_CHANNEL_NAME,
        build_reviews_permissions(guild, verified_role),
        report,
    )


class MarketplaceSetupClient(discord.Client):
    def __init__(self, guild_id: int) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(intents=intents)
        self.guild_id = guild_id
        self.exit_code = 0
        self.report = Report()

    async def on_ready(self) -> None:
        try:
            print(f"Connected as {self.user} ({self.user.id if self.user else 'unknown id'})")
            guild = self.get_guild(self.guild_id)
            if guild is None:
                raise SetupError(
                    f"Guild {self.guild_id} was not found. Check GUILD_ID and make sure the bot is in that server."
                )

            print(f"Target guild: {guild.name} ({guild.id})")
            await setup_marketplace(guild, self.report)
        except SetupError as exc:
            self.exit_code = 1
            print(f"\nERROR: {exc}")
        except Exception:
            self.exit_code = 1
            print("\nUNEXPECTED ERROR:")
            traceback.print_exc()
        finally:
            self.report.print()
            await self.close()


def load_config() -> tuple[str, int]:
    load_dotenv()

    token = os.getenv(TOKEN_ENV)
    guild_id_raw = os.getenv(GUILD_ID_ENV)

    if not token:
        raise SetupError(f"{TOKEN_ENV} is missing. Create .env from .env.example.")
    if not guild_id_raw:
        raise SetupError(f"{GUILD_ID_ENV} is missing. Create .env from .env.example.")

    try:
        guild_id = int(guild_id_raw)
    except ValueError as exc:
        raise SetupError(f"{GUILD_ID_ENV} must be a Discord guild ID number.") from exc

    return token, guild_id


async def main() -> int:
    try:
        token, guild_id = load_config()
    except SetupError as exc:
        print(f"ERROR: {exc}")
        return 1

    client = MarketplaceSetupClient(guild_id)
    try:
        await client.start(token)
    except discord.LoginFailure:
        print("ERROR: Discord login failed. Check DISCORD_TOKEN.")
        return 1

    return client.exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
