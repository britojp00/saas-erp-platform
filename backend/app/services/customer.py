from asyncpg import UniqueViolationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomerNotFoundError, DuplicateCustomerError
from app.db.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CustomerRepository(session)

    async def list(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Customer], int]:
        offset = (page - 1) * page_size
        return await self.repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            search=search,
            sort=sort,
            order=order,
        )

    async def get_by_id(
        self,
        customer_id: int,
        tenant_id: int,
    ) -> Customer:
        customer = await self.repo.get_by_id(customer_id, tenant_id)
        if customer is None:
            raise CustomerNotFoundError()
        return customer

    async def create(
        self,
        tenant_id: int,
        data: CustomerCreate,
    ) -> Customer:
        if data.document:
            exists = await self.repo.exists_by_document(tenant_id, data.document)
            if exists:
                raise DuplicateCustomerError()

        customer = Customer(
            tenant_id=tenant_id,
            name=data.name.strip(),
            document=data.document,
            email=data.email,
            phone=data.phone,
            notes=data.notes,
        )

        try:
            return await self.repo.create(customer)
        except UniqueViolationError:
            raise DuplicateCustomerError()

    async def update(
        self,
        customer_id: int,
        tenant_id: int,
        data: CustomerUpdate,
    ) -> Customer:
        customer = await self.repo.get_by_id(customer_id, tenant_id)
        if customer is None:
            raise CustomerNotFoundError()

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            customer.name = update_data["name"].strip()
        if "document" in update_data:
            new_document = update_data["document"]
            if new_document is not None and new_document != customer.document:
                exists = await self.repo.exists_by_document(
                    tenant_id, new_document, exclude_id=customer.id
                )
                if exists:
                    raise DuplicateCustomerError()
            customer.document = new_document
        if "email" in update_data:
            customer.email = update_data["email"]
        if "phone" in update_data:
            customer.phone = update_data["phone"]
        if "notes" in update_data:
            customer.notes = update_data["notes"]

        try:
            return await self.repo.update(customer)
        except UniqueViolationError:
            raise DuplicateCustomerError()

    async def soft_delete(
        self,
        customer_id: int,
        tenant_id: int,
    ) -> None:
        customer = await self.repo.get_by_id(customer_id, tenant_id)
        if customer is None:
            raise CustomerNotFoundError()
        await self.repo.soft_delete(customer)
