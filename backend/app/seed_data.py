"""Database seeder with synthetic accounts, tariffs, statements, and transactions."""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.account import Account, AccountTier
from backend.app.models.tariff import TariffRule
from backend.app.models.statement import Statement, Transaction
from backend.app.mock_bank.synthetic_data import (
    get_default_tiers_data,
    get_default_tariff_rules_data,
    generate_synthetic_statement_bundle
)
from backend.app.services.audit_service import audit_service
from backend.app.logging_config import logger


async def seed_database(db: AsyncSession, run_initial_audit: bool = True) -> None:
    """Seeds the database with realistic synthetic banking scenarios."""
    # Check if already seeded
    existing = await db.execute(select(AccountTier))
    if existing.scalars().first():
        logger.info("Database already seeded with account tiers. Skipping tier creation.")
        return

    logger.info("Starting synthetic database seeding...")

    # 1. Create Tiers
    tiers_map = {}
    for tier_data in get_default_tiers_data():
        tier = AccountTier(**tier_data)
        db.add(tier)
        await db.flush()
        tiers_map[tier.code] = tier.id

    # 2. Create Tariff Rules
    tariff_rules_data = get_default_tariff_rules_data(tiers_map)
    for tr_data in tariff_rules_data:
        rule = TariffRule(**tr_data)
        db.add(rule)
    await db.flush()

    # 3. Create Accounts
    accounts_seed = [
        {
            "account_number": "ACT-8821-4902-1104",
            "holder_name": "Jordan Miller (Consumer)",
            "bank_name": "Apex National Bank",
            "routing_number": "021000021",
            "currency": "USD",
            "current_balance": 1936.20,
            "tier_id": tiers_map["TIER_EVERYDAY"],
            "electronic_statements_enrolled": True,
            "source_id": "SYNTH-ACC-JORDAN-01",
            "source_url": "mock://apexnational.internal/accounts/882149021104"
        },
        {
            "account_number": "ACT-9011-3829-5520",
            "holder_name": "Dr. Aris Thorne (Premier Client)",
            "bank_name": "Apex National Bank",
            "routing_number": "021000021",
            "currency": "USD",
            "current_balance": 63670.00,
            "tier_id": tiers_map["TIER_PREMIER"],
            "electronic_statements_enrolled": True,
            "source_id": "SYNTH-ACC-ARIS-02",
            "source_url": "mock://apexnational.internal/accounts/901138295520"
        },
        {
            "account_number": "ACT-4412-8830-9931",
            "holder_name": "Vanguard Logistics LLC",
            "bank_name": "Apex National Bank",
            "routing_number": "021000021",
            "currency": "USD",
            "current_balance": 10465.00,
            "tier_id": tiers_map["TIER_SMB"],
            "electronic_statements_enrolled": True,
            "source_id": "SYNTH-ACC-VANGUARD-03",
            "source_url": "mock://apexnational.internal/accounts/441288309931"
        }
    ]

    initial_statement_ids = []

    # Reverse lookup map for tier codes
    reverse_tiers_map = {v: k for k, v in tiers_map.items()}

    for acc_info in accounts_seed:
        account = Account(**acc_info)
        db.add(account)
        await db.flush()

        tier_code = reverse_tiers_map.get(account.tier_id, "TIER_EVERYDAY")

        # Generate Statement Bundle (initial + subsequent)
        bundle = generate_synthetic_statement_bundle(account.id, tier_code)

        # Initial statement
        init_meta = bundle["initial_statement"]
        tx_list = init_meta.pop("transactions")
        statement_initial = Statement(**init_meta)
        db.add(statement_initial)
        await db.flush()
        initial_statement_ids.append(statement_initial.id)

        for tx_dict in tx_list:
            tx = Transaction(
                statement_id=statement_initial.id,
                transaction_date=tx_dict["date"],
                posting_date=tx_dict["date"],
                description=tx_dict["desc"],
                transaction_type=tx_dict["type"],
                amount=tx_dict["amount"],
                balance_after=tx_dict["bal"],
                raw_category=tx_dict["cat"],
                source_transaction_id=f"TXN-{statement_initial.source_id[:10]}-{tx_dict['date'].strftime('%d%m')}-{int(tx_dict['amount'])}"
            )
            db.add(tx)

        # Subsequent statement (used for refund verification)
        sub_meta = bundle["subsequent_statement"]
        sub_tx_list = sub_meta.pop("transactions")
        sub_meta["verified_against_statement_id"] = statement_initial.id
        statement_subsequent = Statement(**sub_meta)
        db.add(statement_subsequent)
        await db.flush()

        for stx_dict in sub_tx_list:
            stx = Transaction(
                statement_id=statement_subsequent.id,
                transaction_date=stx_dict["date"],
                posting_date=stx_dict["date"],
                description=stx_dict["desc"],
                transaction_type=stx_dict["type"],
                amount=stx_dict["amount"],
                balance_after=stx_dict["bal"],
                raw_category=stx_dict["cat"],
                source_transaction_id=f"TXN-SUB-{statement_subsequent.source_id[:10]}-{stx_dict['date'].strftime('%d%m')}-{int(stx_dict['amount'])}"
            )
            db.add(stx)

    await db.commit()
    logger.info("Synthetic database seeding completed.")

    # 4. Optional initial audit pass
    if run_initial_audit:
        logger.info("Executing baseline audit pass on seeded statements...")
        for stmt_id in initial_statement_ids:
            try:
                await audit_service.audit_statement(db, stmt_id)
            except Exception as e:
                logger.error(f"Error auditing initial statement {stmt_id}: {e}")
        logger.info("Baseline audit pass completed.")


if __name__ == "__main__":
    import asyncio
    from backend.app.database import AsyncSessionLocal

    async def _run_manual_seed():
        async with AsyncSessionLocal() as session:
            await seed_database(session, run_initial_audit=True)
            print("Synthetic database seeding completed successfully.")

    asyncio.run(_run_manual_seed())

