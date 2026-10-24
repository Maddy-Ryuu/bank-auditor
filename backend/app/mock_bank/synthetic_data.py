"""Synthetic bank statements, accounts, and tariff data generator."""
import hashlib
from datetime import date, timedelta
from typing import Dict, List, Any


def sha256_hash(data: str) -> str:
    """Generate SHA-256 hash for synthetic statement immutability."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def get_default_tiers_data() -> List[Dict[str, Any]]:
    """Return standard synthetic account tiers."""
    return [
        {
            "name": "Everyday Checking",
            "code": "TIER_EVERYDAY",
            "description": "Standard consumer retail checking with balance and direct deposit fee waivers.",
            "monthly_maintenance_fee": 12.00,
            "min_balance_waiver": 1500.00,
            "min_direct_deposit_waiver": 500.00,
            "overdraft_fee_amount": 35.00,
            "max_daily_overdraft_fees": 3,
            "overdraft_threshold_cents": 500,  # $5.00
            "wire_incoming_domestic_fee": 15.00,
            "wire_outgoing_domestic_fee": 25.00,
            "wire_outgoing_international_fee": 45.00,
            "paper_statement_fee": 3.00,
            "foreign_transaction_fee_rate": 0.03,
        },
        {
            "name": "Premier Relationship Checking",
            "code": "TIER_PREMIER",
            "description": "High-net-worth tier featuring complimentary incoming wires and dedicated relationship banker.",
            "monthly_maintenance_fee": 25.00,
            "min_balance_waiver": 10000.00,
            "min_direct_deposit_waiver": 2500.00,
            "overdraft_fee_amount": 30.00,
            "max_daily_overdraft_fees": 2,
            "overdraft_threshold_cents": 1000,  # $10.00
            "wire_incoming_domestic_fee": 0.00,  # Complimentary incoming wires
            "wire_outgoing_domestic_fee": 20.00,
            "wire_outgoing_international_fee": 35.00,
            "paper_statement_fee": 0.00,  # Free paper statements
            "foreign_transaction_fee_rate": 0.01,
        },
        {
            "name": "Small Business Commercial",
            "code": "TIER_SMB",
            "description": "Commercial operating checking account for small-to-medium enterprises.",
            "monthly_maintenance_fee": 30.00,
            "min_balance_waiver": 5000.00,
            "min_direct_deposit_waiver": 0.00,  # Balance waiver only
            "overdraft_fee_amount": 35.00,
            "max_daily_overdraft_fees": 3,
            "overdraft_threshold_cents": 500,
            "wire_incoming_domestic_fee": 10.00,
            "wire_outgoing_domestic_fee": 25.00,
            "wire_outgoing_international_fee": 45.00,
            "paper_statement_fee": 5.00,
            "foreign_transaction_fee_rate": 0.025,
        }
    ]


def get_default_tariff_rules_data(tier_codes_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """Return published tariff rules mapped to account tier UUIDs."""
    rules = []

    # Everyday Checking rules
    everyday_id = tier_codes_map.get("TIER_EVERYDAY")
    if everyday_id:
        rules.extend([
            {
                "tier_id": everyday_id,
                "fee_category": "MONTHLY_MAINTENANCE",
                "fee_name": "Everyday Monthly Service Charge",
                "standard_amount": 12.00,
                "condition_logic": {
                    "min_balance_waiver": 1500.00,
                    "min_direct_deposit_waiver": 500.00,
                    "grace_period_days": 30
                },
                "effective_from": date(2024, 1, 1),
                "source_document_ref": "Apex Schedule of Fees 2024 v1.0 Section 2.1"
            },
            {
                "tier_id": everyday_id,
                "fee_category": "OVERDRAFT",
                "fee_name": "Standard Overdraft Paid Item Fee",
                "standard_amount": 35.00,
                "condition_logic": {
                    "max_daily_overdraft_fees": 3,
                    "de_minimis_threshold": 5.00,
                    "curfew_cutoff_hour": 20
                },
                "effective_from": date(2024, 1, 1),
                "source_document_ref": "Apex Consumer Deposit Agreement Sec 8.4"
            },
            {
                "tier_id": everyday_id,
                "fee_category": "PAPER_STATEMENT",
                "fee_name": "Paper Account Statement Delivery Fee",
                "standard_amount": 3.00,
                "condition_logic": {
                    "waived_for_estatement": True
                },
                "effective_from": date(2024, 1, 1),
                "source_document_ref": "Apex E-Sign Disclosure Section 3"
            }
        ])

    # Premier tier rules
    premier_id = tier_codes_map.get("TIER_PREMIER")
    if premier_id:
        rules.extend([
            {
                "tier_id": premier_id,
                "fee_category": "WIRE_TRANSFER",
                "fee_name": "Premier Domestic Inbound Wire Benefit",
                "standard_amount": 0.00,
                "condition_logic": {
                    "wire_incoming_domestic_fee": 0.00,
                    "wire_outgoing_domestic_fee": 20.00
                },
                "effective_from": date(2024, 1, 1),
                "source_document_ref": "Apex Premier Client Guide 2024 Sec 4.2"
            },
            {
                "tier_id": premier_id,
                "fee_category": "MONTHLY_MAINTENANCE",
                "fee_name": "Premier Relationship Monthly Fee",
                "standard_amount": 25.00,
                "condition_logic": {
                    "min_balance_waiver": 10000.00,
                    "min_direct_deposit_waiver": 2500.00
                },
                "effective_from": date(2024, 1, 1),
                "source_document_ref": "Apex Premier Fee Schedule Sec 1"
            }
        ])

    # SMB rules
    smb_id = tier_codes_map.get("TIER_SMB")
    if smb_id:
        rules.extend([
            {
                "tier_id": smb_id,
                "fee_category": "WIRE_TRANSFER",
                "fee_name": "Commercial Outgoing Wire Fee",
                "standard_amount": 25.00,
                "condition_logic": {
                    "wire_outgoing_domestic_fee": 25.00,
                    "wire_incoming_domestic_fee": 10.00
                },
                "effective_from": date(2024, 1, 1),
                "source_document_ref": "Commercial Banking Tariff 2024 Sec 5"
            }
        ])

    return rules


def generate_synthetic_statement_bundle(account_id: str, tier_code: str) -> Dict[str, Any]:
    """Generates synthetic audit statement + subsequent verification statement."""
    base_date = date(2024, 3, 1)
    end_date = date(2024, 3, 31)

    if tier_code == "TIER_EVERYDAY":
        # Scenario: Everyday checking account with balance of $1,840 (exceeding $1500 waiver)
        # BUG: Charged $12.00 monthly service fee!
        # BUG 2: Charged 4 overdraft fees on March 15 (exceeding daily cap of 3)!
        # BUG 3: Charged $3.00 paper statement fee while electronic statement enrolled!
        opening = 2450.00
        txs = [
            {"date": date(2024, 3, 2), "desc": "Payroll Direct Deposit - ACME Corp", "type": "CREDIT", "amount": 1250.00, "bal": 3700.00, "cat": "PAYROLL"},
            {"date": date(2024, 3, 5), "desc": "Whole Foods Market Grocery", "type": "DEBIT", "amount": 134.50, "bal": 3565.50, "cat": "GROCERY"},
            {"date": date(2024, 3, 8), "desc": "Electric Utility Bill Autopay", "type": "DEBIT", "amount": 142.10, "bal": 3423.40, "cat": "UTILITIES"},
            {"date": date(2024, 3, 12), "desc": "Amazon Online Marketplace", "type": "DEBIT", "amount": 89.20, "bal": 3334.20, "cat": "SHOPPING"},
            # March 15: Overdraft event cascade
            {"date": date(2024, 3, 15), "desc": "Emergency Auto Repair Shop", "type": "DEBIT", "amount": 3400.00, "bal": -65.80, "cat": "SERVICES"},
            {"date": date(2024, 3, 15), "desc": "Overdraft Fee - Item 1", "type": "FEE", "amount": 35.00, "bal": -100.80, "cat": "BANK_FEE"},
            {"date": date(2024, 3, 15), "desc": "Pharmacy Rx Co-Pay", "type": "DEBIT", "amount": 25.00, "bal": -125.80, "cat": "HEALTH"},
            {"date": date(2024, 3, 15), "desc": "Overdraft Fee - Item 2", "type": "FEE", "amount": 35.00, "bal": -160.80, "cat": "BANK_FEE"},
            {"date": date(2024, 3, 15), "desc": "Local Bakery Coffee Shop", "type": "DEBIT", "amount": 18.00, "bal": -178.80, "cat": "DINING"},
            {"date": date(2024, 3, 15), "desc": "Overdraft Fee - Item 3", "type": "FEE", "amount": 35.00, "bal": -213.80, "cat": "BANK_FEE"},
            # Fourth OD fee on same day! Contractual cap is 3!
            {"date": date(2024, 3, 15), "desc": "Overdraft Fee - Item 4 (Excess Daily Cap)", "type": "FEE", "amount": 35.00, "bal": -248.80, "cat": "BANK_FEE"},
            # Deposit to cure negative balance
            {"date": date(2024, 3, 16), "desc": "Mobile Check Deposit", "type": "CREDIT", "amount": 2200.00, "bal": 1951.20, "cat": "DEPOSIT"},
            # Paper statement fee charged on e-statement enrolled account
            {"date": date(2024, 3, 28), "desc": "Paper Statement Fee", "type": "FEE", "amount": 3.00, "bal": 1948.20, "cat": "BANK_FEE"},
            # Monthly maintenance fee charged despite ADB being $1,840.50
            {"date": date(2024, 3, 31), "desc": "Monthly Maintenance Fee", "type": "FEE", "amount": 12.00, "bal": 1936.20, "cat": "BANK_FEE"},
        ]

        subsequent_base = date(2024, 4, 1)
        subsequent_end = date(2024, 4, 30)
        # Subsequent statement contains the refund credit matching the reversal!
        subsequent_txs = [
            {"date": date(2024, 4, 3), "desc": "Payroll Direct Deposit - ACME Corp", "type": "CREDIT", "amount": 1250.00, "bal": 3186.20, "cat": "PAYROLL"},
            {"date": date(2024, 4, 10), "desc": "FEE REFUND - OVERDRAFT EXCESS CAP REVERSAL", "type": "REFUND", "amount": 35.00, "bal": 3221.20, "cat": "REFUND"},
            {"date": date(2024, 4, 10), "desc": "FEE REFUND - MONTHLY MAINTENANCE WAIVER REVERSAL", "type": "REFUND", "amount": 12.00, "bal": 3233.20, "cat": "REFUND"},
            {"date": date(2024, 4, 10), "desc": "FEE REFUND - PAPER STATEMENT ENROLLMENT REVERSAL", "type": "REFUND", "amount": 3.00, "bal": 3236.20, "cat": "REFUND"},
            {"date": date(2024, 4, 15), "desc": "Target Superstore", "type": "DEBIT", "amount": 86.40, "bal": 3149.80, "cat": "SHOPPING"},
        ]

        return {
            "initial_statement": {
                "account_id": account_id,
                "statement_period_start": base_date,
                "statement_period_end": end_date,
                "opening_balance": opening,
                "closing_balance": 1936.20,
                "average_daily_balance": 1840.50,
                "total_qualifying_direct_deposits": 1250.00,
                "is_subsequent_statement": False,
                "source_id": "SYNTH-STMT-2024-03-EVERYDAY",
                "source_filename": "Apex_March2024_Stmt_8821.pdf",
                "raw_statement_hash": sha256_hash("SYNTH-STMT-2024-03-EVERYDAY-DATA"),
                "transactions": txs
            },
            "subsequent_statement": {
                "account_id": account_id,
                "statement_period_start": subsequent_base,
                "statement_period_end": subsequent_end,
                "opening_balance": 1936.20,
                "closing_balance": 3149.80,
                "average_daily_balance": 2850.00,
                "total_qualifying_direct_deposits": 1250.00,
                "is_subsequent_statement": True,
                "source_id": "SYNTH-STMT-2024-04-EVERYDAY-SUBSEQUENT",
                "source_filename": "Apex_April2024_Stmt_8821.pdf",
                "raw_statement_hash": sha256_hash("SYNTH-STMT-2024-04-EVERYDAY-DATA"),
                "transactions": subsequent_txs
            }
        }

    elif tier_code == "TIER_PREMIER":
        # Premier tier: Free incoming domestic wires!
        # BUG: Charged $15.00 incoming wire fee!
        opening = 45000.00
        txs = [
            {"date": date(2024, 3, 3), "desc": "Investment Dividend Distribution", "type": "CREDIT", "amount": 4200.00, "bal": 49200.00, "cat": "INVESTMENT"},
            {"date": date(2024, 3, 10), "desc": "Wire Transfer In - Domestic Escrow Settlement", "type": "CREDIT", "amount": 15000.00, "bal": 64200.00, "cat": "WIRE"},
            # BUG: Premier Tier grants free incoming domestic wires!
            {"date": date(2024, 3, 10), "desc": "Incoming Wire Fee - Domestic", "type": "FEE", "amount": 15.00, "bal": 64185.00, "cat": "BANK_FEE"},
            {"date": date(2024, 3, 20), "desc": "US Merchant Software Subscription", "type": "DEBIT", "amount": 500.00, "bal": 63685.00, "cat": "SOFTWARE"},
            # BUG: Foreign transaction fee charged on domestic US purchase!
            {"date": date(2024, 3, 20), "desc": "Foreign Transaction Fee - Domestic US Merchant", "type": "FEE", "amount": 15.00, "bal": 63670.00, "cat": "BANK_FEE"},
        ]
        subsequent_txs = [
            {"date": date(2024, 4, 8), "desc": "FEE REFUND - PREMIER INCOMING WIRE CHARGE REVERSAL", "type": "REFUND", "amount": 15.00, "bal": 63685.00, "cat": "REFUND"},
            {"date": date(2024, 4, 8), "desc": "FEE REFUND - DOMESTIC MERCHANT FX SURCHARGE REVERSAL", "type": "REFUND", "amount": 15.00, "bal": 63700.00, "cat": "REFUND"}
        ]
        return {
            "initial_statement": {
                "account_id": account_id,
                "statement_period_start": base_date,
                "statement_period_end": end_date,
                "opening_balance": opening,
                "closing_balance": 63670.00,
                "average_daily_balance": 54200.00,
                "total_qualifying_direct_deposits": 4200.00,
                "is_subsequent_statement": False,
                "source_id": "SYNTH-STMT-2024-03-PREMIER",
                "source_filename": "Apex_Premier_March2024_Stmt_9011.pdf",
                "raw_statement_hash": sha256_hash("SYNTH-STMT-2024-03-PREMIER-DATA"),
                "transactions": txs
            },
            "subsequent_statement": {
                "account_id": account_id,
                "statement_period_start": date(2024, 4, 1),
                "statement_period_end": date(2024, 4, 30),
                "opening_balance": 63670.00,
                "closing_balance": 63700.00,
                "average_daily_balance": 63680.00,
                "total_qualifying_direct_deposits": 0.0,
                "is_subsequent_statement": True,
                "source_id": "SYNTH-STMT-2024-04-PREMIER-SUBSEQUENT",
                "source_filename": "Apex_Premier_April2024_Stmt_9011.pdf",
                "raw_statement_hash": sha256_hash("SYNTH-STMT-2024-04-PREMIER-DATA"),
                "transactions": subsequent_txs
            }
        }

    else:
        # Small business
        opening = 12000.00
        txs = [
            {"date": date(2024, 3, 4), "desc": "Client Invoice Payment Received", "type": "CREDIT", "amount": 6500.00, "bal": 18500.00, "cat": "REVENUE"},
            {"date": date(2024, 3, 14), "desc": "Outgoing Domestic Wire Transfer to Supplier", "type": "TRANSFER", "amount": 8000.00, "bal": 10500.00, "cat": "SUPPLIER"},
            # BUG: Standard outgoing domestic wire tariff is $25.00, but $35.00 was charged!
            {"date": date(2024, 3, 14), "desc": "Outgoing Domestic Wire Fee", "type": "FEE", "amount": 35.00, "bal": 10465.00, "cat": "BANK_FEE"},
        ]
        subsequent_txs = [
            {"date": date(2024, 4, 12), "desc": "FEE REFUND - WIRE OVERCHARGE REVERSAL", "type": "REFUND", "amount": 10.00, "bal": 10475.00, "cat": "REFUND"}
        ]
        return {
            "initial_statement": {
                "account_id": account_id,
                "statement_period_start": base_date,
                "statement_period_end": end_date,
                "opening_balance": opening,
                "closing_balance": 10465.00,
                "average_daily_balance": 12800.00,
                "total_qualifying_direct_deposits": 0.0,
                "is_subsequent_statement": False,
                "source_id": "SYNTH-STMT-2024-03-SMB",
                "source_filename": "Apex_SMB_March2024_Stmt_4412.pdf",
                "raw_statement_hash": sha256_hash("SYNTH-STMT-2024-03-SMB-DATA"),
                "transactions": txs
            },
            "subsequent_statement": {
                "account_id": account_id,
                "statement_period_start": date(2024, 4, 1),
                "statement_period_end": date(2024, 4, 30),
                "opening_balance": 10465.00,
                "closing_balance": 10475.00,
                "average_daily_balance": 10470.00,
                "total_qualifying_direct_deposits": 0.0,
                "is_subsequent_statement": True,
                "source_id": "SYNTH-STMT-2024-04-SMB-SUBSEQUENT",
                "source_filename": "Apex_SMB_April2024_Stmt_4412.pdf",
                "raw_statement_hash": sha256_hash("SYNTH-STMT-2024-04-SMB-DATA"),
                "transactions": subsequent_txs
            }
        }
