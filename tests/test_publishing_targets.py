import uuid
import pytest
from datetime import datetime

from src.blog_writer_sdk.services.publishing_service import PublishingService
from src.blog_writer_sdk.models.publishing_models import (
    CreatePublishingTargetRequest,
    UpdatePublishingTargetRequest,
    CMSProvider,
    PublishingTargetStatus,
)


class FakeTable:
    def __init__(self, store, table_name):
        self.store = store
        self.table_name = table_name
        self.filters = []
        self.updates = None
        self.insert_payload = None
        self.operation = "select"

    def select(self, *_):
        self.operation = "select"
        return self

    def update(self, data):
        self.operation = "update"
        self.updates = data
        return self

    def insert(self, data):
        self.operation = "insert"
        self.insert_payload = data
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def neq(self, field, value):
        self.filters.append(("neq", field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.operation == "insert":
            record = dict(self.insert_payload)
            record.setdefault("id", str(uuid.uuid4()))
            self.store.append(record)
            return type("Resp", (), {"data": [record]})

        # apply filters
        records = list(self.store)
        for op, field, value in self.filters:
            if op == "eq":
                records = [r for r in records if r.get(field) == value]
            elif op == "neq":
                records = [r for r in records if r.get(field) != value]

        if self.operation == "update":
            updated = []
            for r in records:
                r.update(self.updates or {})
                updated.append(r)
            return type("Resp", (), {"data": updated})

        return type("Resp", (), {"data": records})


class FakeClient:
    def __init__(self, store):
        self.store = store

    def table(self, _name):
        return FakeTable(self.store, _name)


class FakeSupabaseClient:
    def __init__(self):
        self.environment = "dev"
        self._store = []
        self.client = FakeClient(self._store)

    def _get_table_name(self, base_name: str) -> str:
        return f"{base_name}_{self.environment}"

    async def list_publishing_targets(self, org_id: str, include_inactive: bool = False):
        records = [r for r in self._store if r.get("org_id") == org_id]
        if not include_inactive:
            records = [r for r in records if r.get("status") == "active"]
        # mimic Supabase ordering by created_at desc
        records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return records

    async def get_publishing_target(self, target_id: str, org_id: str):
        for r in self._store:
            if r.get("id") == target_id and r.get("org_id") == org_id:
                return r
        return None

    async def create_publishing_target(self, target_data):
        # ensure id
        record = dict(target_data)
        record["id"] = record.get("id") or str(uuid.uuid4())
        self._store.append(record)
        return record

    async def update_publishing_target(self, target_id: str, org_id: str, updates):
        for r in self._store:
            if r.get("id") == target_id and r.get("org_id") == org_id:
                r.update(updates)
                return r
        return {}

    async def soft_delete_publishing_target(self, target_id: str, org_id: str):
        for r in self._store:
            if r.get("id") == target_id and r.get("org_id") == org_id:
                r["status"] = "inactive"
                r["deleted_at"] = datetime.utcnow().isoformat()
                return True
        return False


@pytest.mark.asyncio
async def test_publishing_targets_crud_flow():
    supabase = FakeSupabaseClient()
    service = PublishingService(supabase_client=supabase)

    create_request = CreatePublishingTargetRequest(
        org_id="org_1",
        name="Primary Site",
        type=CMSProvider.webflow,
        site_url="https://example.com",
    )

    created = await service.create_publishing_target(create_request)
    assert created.org_id == "org_1"
    assert created.status == PublishingTargetStatus.active

    # Create another target and set as default
    create_request_2 = CreatePublishingTargetRequest(
        org_id="org_1",
        name="Secondary",
        type=CMSProvider.webflow,
        site_url="https://secondary.com",
        is_default=True,
    )
    created_2 = await service.create_publishing_target(create_request_2)
    # ensure first default unset
    first = await service.get_publishing_target(created.id, "org_1")
    assert created_2.is_default is True
    assert first.is_default is False

    # Update target status
    update_request = UpdatePublishingTargetRequest(status=PublishingTargetStatus.inactive)
    updated = await service.update_publishing_target(created.id, "org_1", update_request)
    assert updated.status == PublishingTargetStatus.inactive

    # Soft delete
    deleted = await service.delete_publishing_target(created.id, "org_1")
    assert deleted is True
    removed = await service.get_publishing_target(created.id, "org_1")
    assert removed.status == PublishingTargetStatus.inactive



