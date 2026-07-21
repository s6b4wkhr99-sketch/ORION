"""Volume 16 — Seed role, permission, provider reference tables."""

from sqlalchemy.orm import Session

from app.mapping.data_dictionary import EXPORT_PROVIDER_MAPPINGS
from app.models.v16_schema import PermissionDefinition, ProviderFieldMapping, ProviderMaster, RoleDefinition
from app.providers.constants import PROVIDER_MAPPING_VERSION, SUPPORTED_PROVIDERS
from app.security.permissions import MODULE_PERMISSIONS
from app.security.roles import ALL_ROLES


def seed_v16_reference_schema(db: Session) -> None:
    if db.query(RoleDefinition).count() == 0:
        for role in sorted(ALL_ROLES):
            db.add(RoleDefinition(role_name=role, description=f"CIOS role: {role}"))

    if db.query(PermissionDefinition).count() == 0:
        for module, roles in MODULE_PERMISSIONS.items():
            db.add(
                PermissionDefinition(
                    permission_name=module,
                    module=module,
                    description=f"Allowed roles: {', '.join(sorted(roles))}",
                )
            )

    provider_rows = {p.provider_name: p for p in db.query(ProviderMaster).all()}
    for name in SUPPORTED_PROVIDERS:
        if name not in provider_rows:
            row = ProviderMaster(provider_name=name, provider_version=PROVIDER_MAPPING_VERSION, status="active")
            db.add(row)
            db.flush()
            provider_rows[name] = row

    if db.query(ProviderFieldMapping).count() == 0:
        seen: set[tuple[int, str]] = set()
        for provider_name, field, target_name, _order, required in EXPORT_PROVIDER_MAPPINGS:
            master = provider_rows.get(provider_name)
            if not master:
                continue
            key = (master.provider_id, field)
            if key in seen:
                continue
            seen.add(key)
            db.add(
                ProviderFieldMapping(
                    provider_id=master.provider_id,
                    internal_field=field,
                    provider_field=target_name,
                    required=required,
                )
            )

    db.commit()
