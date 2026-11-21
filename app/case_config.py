"""Configurable seed data so TRIPE can be retargeted per case/jurisdiction.

Set environment variables to override mock/seed values.
"""
import os

CASE_JURISDICTION = os.getenv("TRIPE_CASE_JURISDICTION", "Illinois")
CASE_TENANT_NAME = os.getenv("TRIPE_CASE_TENANT_NAME", "Tenant")

SEED_CASES = [
    {
        "title": os.getenv("TRIPE_CASE_1_TITLE", "Mold & Heat Failure — 142 Elm St"),
        "landlord_name": os.getenv("TRIPE_CASE_1_LANDLORD", "Landlord 1 LLC"),
        "property_address": os.getenv("TRIPE_CASE_1_ADDRESS", "142 Elm St, Apt 3B"),
    },
    {
        "title": os.getenv("TRIPE_CASE_2_TITLE", "Withheld Security Deposit — 88 Oak Ave"),
        "landlord_name": os.getenv("TRIPE_CASE_2_LANDLORD", "Landlord 2 Management"),
        "property_address": os.getenv("TRIPE_CASE_2_ADDRESS", "88 Oak Ave, Unit 12"),
    },
    {
        "title": os.getenv("TRIPE_CASE_3_TITLE", "Retaliatory Entry & Harassment — 9 Maple Ct"),
        "landlord_name": os.getenv("TRIPE_CASE_3_LANDLORD", "Landlord 3 Realty"),
        "property_address": os.getenv("TRIPE_CASE_3_ADDRESS", "9 Maple Ct"),
    },
]
