"""
Finance Sector Taxonomy Seed Script
====================================
Seeds the database with:
  1. "Finance & Banking" sector with keyword aliases
  2. 25 curated finance roles with aliases
  3. 60+ finance-specific skills with aliases
  4. Role-skill mappings
  5. Migrates existing IT skills to have sector_id = IT
  6. Adds the sector_id column if missing (schema migration)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.taxonomy import (
    SectorTaxonomy, SectorAlias,
    RoleTaxonomy, RoleAlias,
    SkillTaxonomy, SkillAlias,
    RoleSkill,
)
from sqlalchemy import text, inspect

app = create_app()

# ─────────────────────────────────────────────────────────────
# CURATED FINANCE DATA
# ─────────────────────────────────────────────────────────────

SECTOR_NAME = "Finance & Banking"
SECTOR_ALIASES = [
    "finance", "banking", "fintech", "investment", "accounting",
    "audit", "actuarial", "wealth management", "insurance",
    "financial services", "asset management", "private equity",
    "venture capital", "treasury", "risk management",
    "capital markets", "hedge fund", "portfolio management",
    "credit", "underwriting", "mortgage",
]

ROLES = {
    # role_title: [aliases]
    "Financial Analyst": ["finance analyst", "financial planning analyst", "FP&A analyst"],
    "Investment Banker": ["investment banking analyst", "IB analyst", "IBD analyst"],
    "Risk Manager": ["risk analyst", "risk management analyst", "enterprise risk manager"],
    "Compliance Officer": ["compliance analyst", "regulatory compliance officer", "compliance manager"],
    "Accountant": ["staff accountant", "senior accountant", "accounting specialist"],
    "Auditor": ["internal auditor", "external auditor", "audit associate", "audit manager"],
    "Actuarial Analyst": ["actuary", "actuarial associate", "actuarial consultant"],
    "Portfolio Manager": ["asset manager", "fund manager", "investment portfolio manager"],
    "Quantitative Analyst": ["quant analyst", "quant developer", "quantitative researcher", "quant"],
    "Credit Analyst": ["credit risk analyst", "credit officer", "credit underwriter"],
    "Financial Controller": ["controller", "corporate controller", "finance controller"],
    "Treasury Analyst": ["treasury manager", "cash management analyst", "treasury associate"],
    "Tax Specialist": ["tax analyst", "tax consultant", "tax advisor", "tax accountant"],
    "Wealth Manager": ["wealth advisor", "financial advisor", "private banker", "relationship manager"],
    "Underwriter": ["insurance underwriter", "commercial underwriter", "underwriting analyst"],
    "Financial Planner": ["certified financial planner", "CFP", "financial planning specialist"],
    "Mergers & Acquisitions Analyst": ["M&A analyst", "M&A associate", "corporate development analyst"],
    "Equity Research Analyst": ["research analyst", "equity analyst", "securities analyst"],
    "Derivatives Trader": ["options trader", "derivatives analyst", "trading analyst", "trader"],
    "Anti-Money Laundering Analyst": ["AML analyst", "AML compliance analyst", "KYC analyst"],
    "Blockchain Developer (Finance)": ["crypto developer", "DeFi developer", "blockchain engineer"],
    "Financial Data Scientist": ["finance data analyst", "quantitative data scientist"],
    "Loan Officer": ["mortgage officer", "loan originator", "lending specialist"],
    "Claims Analyst": ["claims adjuster", "claims examiner", "insurance claims analyst"],
    "FinTech Product Manager": ["fintech PM", "payments product manager", "banking product manager"],
}

SKILLS = {
    # skill_name: { category, aliases }
    "Financial Modeling": {"category": "Finance", "aliases": ["financial modelling", "fin model", "3-statement model"]},
    "Bloomberg Terminal": {"category": "Finance Tool", "aliases": ["bloomberg", "BBG terminal"]},
    "Risk Assessment": {"category": "Finance", "aliases": ["risk analysis", "risk evaluation", "risk scoring"]},
    "GAAP": {"category": "Accounting", "aliases": ["US GAAP", "generally accepted accounting principles"]},
    "IFRS": {"category": "Accounting", "aliases": ["international financial reporting standards"]},
    "SOX Compliance": {"category": "Compliance", "aliases": ["sarbanes-oxley", "SOX", "sox audit"]},
    "Anti-Money Laundering": {"category": "Compliance", "aliases": ["AML", "AML compliance", "anti money laundering"]},
    "KYC": {"category": "Compliance", "aliases": ["know your customer", "KYC compliance", "customer due diligence"]},
    "Basel III": {"category": "Regulation", "aliases": ["basel framework", "basel regulatory"]},
    "Dodd-Frank": {"category": "Regulation", "aliases": ["dodd frank act", "dodd-frank compliance"]},
    "Derivatives": {"category": "Finance", "aliases": ["options", "futures", "swaps", "financial derivatives"]},
    "Fixed Income": {"category": "Finance", "aliases": ["bonds", "fixed income securities", "debt instruments"]},
    "Equity Analysis": {"category": "Finance", "aliases": ["equity research", "stock analysis", "equity valuation"]},
    "DCF Analysis": {"category": "Finance", "aliases": ["discounted cash flow", "DCF model", "DCF valuation"]},
    "Monte Carlo Simulation": {"category": "Quantitative", "aliases": ["monte carlo", "MC simulation"]},
    "Value at Risk": {"category": "Quantitative", "aliases": ["VaR", "value-at-risk", "portfolio risk"]},
    "Credit Risk Modeling": {"category": "Finance", "aliases": ["credit scoring model", "PD/LGD models"]},
    "Financial Reporting": {"category": "Accounting", "aliases": ["financial statements", "quarterly reporting", "10-K filing"]},
    "Budgeting & Forecasting": {"category": "Finance", "aliases": ["budget planning", "financial forecasting", "FP&A"]},
    "Taxation": {"category": "Accounting", "aliases": ["tax planning", "corporate tax", "tax law", "income tax"]},
    "Audit": {"category": "Accounting", "aliases": ["internal audit", "external audit", "audit procedures"]},
    "Accounts Payable": {"category": "Accounting", "aliases": ["AP", "accounts payable processing"]},
    "Accounts Receivable": {"category": "Accounting", "aliases": ["AR", "collections", "receivables"]},
    "General Ledger": {"category": "Accounting", "aliases": ["GL", "ledger management", "GL reconciliation"]},
    "SAP FICO": {"category": "Finance Tool", "aliases": ["SAP finance", "SAP FI/CO", "SAP financial accounting"]},
    "Oracle Financials": {"category": "Finance Tool", "aliases": ["oracle EBS finance", "oracle financial cloud"]},
    "QuickBooks": {"category": "Finance Tool", "aliases": ["quickbooks online", "QBO", "intuit quickbooks"]},
    "Xero": {"category": "Finance Tool", "aliases": ["xero accounting"]},
    "Tally": {"category": "Finance Tool", "aliases": ["tally ERP", "tally prime", "tally software"]},
    "Advanced Excel": {"category": "Finance Tool", "aliases": ["excel modeling", "financial excel", "pivot tables", "VLOOKUP", "macros"]},
    "VBA": {"category": "Programming", "aliases": ["visual basic for applications", "excel VBA", "VBA macros"]},
    "Tableau (Finance)": {"category": "Analytics", "aliases": ["tableau dashboard", "financial visualization"]},
    "Power BI (Finance)": {"category": "Analytics", "aliases": ["power bi reporting", "financial dashboard"]},
    "SAS": {"category": "Analytics", "aliases": ["SAS programming", "SAS analytics"]},
    "R (Finance)": {"category": "Programming", "aliases": ["R programming", "R statistical"]},
    "Python (Finance)": {"category": "Programming", "aliases": ["python quant", "python finance", "pandas", "numpy"]},
    "SQL (Finance)": {"category": "Programming", "aliases": ["SQL queries", "database querying", "financial SQL"]},
    "Stripe API": {"category": "FinTech", "aliases": ["stripe payments", "stripe integration"]},
    "Payment Processing": {"category": "FinTech", "aliases": ["payment gateway", "payment systems", "PCI DSS"]},
    "Blockchain": {"category": "FinTech", "aliases": ["distributed ledger", "DLT", "blockchain technology"]},
    "Cryptocurrency": {"category": "FinTech", "aliases": ["crypto", "digital assets", "bitcoin", "ethereum"]},
    "Smart Contracts": {"category": "FinTech", "aliases": ["solidity", "smart contract development"]},
    "RegTech": {"category": "FinTech", "aliases": ["regulatory technology", "compliance automation"]},
    "Actuarial Science": {"category": "Insurance", "aliases": ["actuarial modeling", "life tables", "mortality tables"]},
    "Insurance Underwriting": {"category": "Insurance", "aliases": ["risk underwriting", "policy underwriting"]},
    "Claims Management": {"category": "Insurance", "aliases": ["claims processing", "claims handling"]},
    "Loan Origination": {"category": "Banking", "aliases": ["mortgage origination", "lending process", "loan processing"]},
    "Trade Finance": {"category": "Banking", "aliases": ["letter of credit", "LC", "trade documentation"]},
    "Wealth Management": {"category": "Banking", "aliases": ["private wealth", "HNI management", "UHNW"]},
    "Portfolio Optimization": {"category": "Quantitative", "aliases": ["mean-variance optimization", "efficient frontier"]},
    "Algorithmic Trading": {"category": "Quantitative", "aliases": ["algo trading", "automated trading", "HFT"]},
    "Market Microstructure": {"category": "Quantitative", "aliases": ["order book", "market making"]},
    "Stress Testing": {"category": "Risk", "aliases": ["financial stress testing", "scenario analysis", "CCAR"]},
    "Operational Risk": {"category": "Risk", "aliases": ["operational risk management", "ORM"]},
    "Market Risk": {"category": "Risk", "aliases": ["market risk management", "trading risk"]},
    "Liquidity Risk": {"category": "Risk", "aliases": ["liquidity management", "cash flow risk"]},
    "ESG": {"category": "Finance", "aliases": ["environmental social governance", "sustainable finance", "ESG investing"]},
    "CFA": {"category": "Certification", "aliases": ["chartered financial analyst", "CFA charter"]},
    "CPA": {"category": "Certification", "aliases": ["certified public accountant"]},
    "FRM": {"category": "Certification", "aliases": ["financial risk manager", "GARP FRM"]},
    "ACCA": {"category": "Certification", "aliases": ["association of chartered certified accountants"]},
}

# Role → Skills mapping (which skills each role typically requires)
ROLE_SKILL_MAP = {
    "Financial Analyst": ["Financial Modeling", "Advanced Excel", "Budgeting & Forecasting", "Financial Reporting", "SQL (Finance)", "Power BI (Finance)"],
    "Investment Banker": ["Financial Modeling", "DCF Analysis", "Equity Analysis", "Advanced Excel", "Bloomberg Terminal", "Mergers & Acquisitions Analyst"],
    "Risk Manager": ["Risk Assessment", "Value at Risk", "Stress Testing", "Basel III", "Credit Risk Modeling", "Market Risk", "Operational Risk"],
    "Compliance Officer": ["SOX Compliance", "Anti-Money Laundering", "KYC", "Dodd-Frank", "RegTech"],
    "Accountant": ["GAAP", "IFRS", "Financial Reporting", "General Ledger", "Taxation", "Accounts Payable", "Accounts Receivable", "SAP FICO"],
    "Auditor": ["Audit", "GAAP", "SOX Compliance", "Financial Reporting", "General Ledger"],
    "Actuarial Analyst": ["Actuarial Science", "R (Finance)", "SAS", "Monte Carlo Simulation", "Advanced Excel"],
    "Portfolio Manager": ["Portfolio Optimization", "Equity Analysis", "Fixed Income", "Bloomberg Terminal", "ESG"],
    "Quantitative Analyst": ["Python (Finance)", "R (Finance)", "Monte Carlo Simulation", "Algorithmic Trading", "Derivatives", "Value at Risk"],
    "Credit Analyst": ["Credit Risk Modeling", "Financial Modeling", "Financial Reporting", "Risk Assessment", "Advanced Excel"],
    "Financial Controller": ["GAAP", "IFRS", "Financial Reporting", "Budgeting & Forecasting", "General Ledger", "SAP FICO"],
    "Treasury Analyst": ["Liquidity Risk", "Budgeting & Forecasting", "Advanced Excel", "Trade Finance"],
    "Tax Specialist": ["Taxation", "GAAP", "Advanced Excel", "SAP FICO"],
    "Wealth Manager": ["Wealth Management", "Portfolio Optimization", "ESG", "Bloomberg Terminal", "CFA"],
    "Underwriter": ["Insurance Underwriting", "Risk Assessment", "Actuarial Science", "Claims Management"],
    "Derivatives Trader": ["Derivatives", "Algorithmic Trading", "Bloomberg Terminal", "Market Microstructure", "Python (Finance)"],
    "Anti-Money Laundering Analyst": ["Anti-Money Laundering", "KYC", "RegTech", "SQL (Finance)"],
    "Blockchain Developer (Finance)": ["Blockchain", "Cryptocurrency", "Smart Contracts", "Python (Finance)"],
    "Financial Data Scientist": ["Python (Finance)", "SQL (Finance)", "R (Finance)", "SAS", "Tableau (Finance)", "Financial Modeling"],
    "FinTech Product Manager": ["Payment Processing", "Stripe API", "Blockchain", "RegTech"],
    "Loan Officer": ["Loan Origination", "Credit Risk Modeling", "Risk Assessment"],
    "Claims Analyst": ["Claims Management", "Insurance Underwriting", "Advanced Excel"],
}


def run_seed():
    with app.app_context():
        # ── 0. Schema Migration: add sector_id column if missing ──
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('skill_taxonomy')]
        if 'sector_id' not in columns:
            print("[Migration] Adding sector_id column to skill_taxonomy...")
            db.session.execute(text("ALTER TABLE skill_taxonomy ADD COLUMN sector_id INTEGER REFERENCES sector_taxonomy(id)"))
            db.session.commit()
            print("[Migration] Done.")
        else:
            print("[Migration] sector_id column already exists.")

        # ── 1. Get or create the IT sector reference ──
        it_sector = SectorTaxonomy.query.filter_by(name='IT').first()
        if it_sector:
            # Set all existing IT skills to point to the IT sector
            updated = db.session.execute(
                text("UPDATE skill_taxonomy SET sector_id = :sid WHERE sector_id IS NULL AND category = 'IT'"),
                {'sid': it_sector.id}
            )
            db.session.commit()
            print(f"[IT] Updated {updated.rowcount} existing IT skills with sector_id={it_sector.id}")

        # ── 2. Create the Finance sector ──
        finance_sector = SectorTaxonomy.query.filter_by(name=SECTOR_NAME).first()
        if not finance_sector:
            finance_sector = SectorTaxonomy(name=SECTOR_NAME)
            db.session.add(finance_sector)
            db.session.flush()
            print(f"[Sector] Created '{SECTOR_NAME}' with id={finance_sector.id}")
        else:
            print(f"[Sector] '{SECTOR_NAME}' already exists (id={finance_sector.id})")

        # Add sector aliases
        existing_aliases = {a.name.lower() for a in (finance_sector.aliases or [])}
        added_aliases = 0
        for alias in SECTOR_ALIASES:
            if alias.lower() not in existing_aliases:
                try:
                    db.session.add(SectorAlias(name=alias.lower(), sector_id=finance_sector.id))
                    added_aliases += 1
                except Exception:
                    db.session.rollback()
        db.session.commit()
        print(f"[Sector] Added {added_aliases} aliases to '{SECTOR_NAME}'")

        # ── 3. Seed Finance Roles ──
        roles_created = 0
        role_map = {}  # title -> RoleTaxonomy object
        for title, aliases in ROLES.items():
            role = RoleTaxonomy.query.filter_by(title=title, sector_id=finance_sector.id).first()
            if not role:
                role = RoleTaxonomy(title=title, sector_id=finance_sector.id)
                db.session.add(role)
                db.session.flush()
                roles_created += 1
            role_map[title] = role

            # Add role aliases
            existing_ra = {a.name.lower() for a in (role.aliases or [])}
            for alias in aliases:
                if alias.lower() not in existing_ra:
                    try:
                        db.session.add(RoleAlias(name=alias.lower(), role_id=role.id))
                    except Exception:
                        db.session.rollback()
        db.session.commit()
        print(f"[Roles] Created {roles_created} finance roles (total: {len(ROLES)})")

        # ── 4. Seed Finance Skills ──
        skills_created = 0
        skill_map = {}  # name -> SkillTaxonomy object
        for name, meta in SKILLS.items():
            skill = SkillTaxonomy.query.filter_by(canonical_name=name).first()
            if not skill:
                skill = SkillTaxonomy(
                    canonical_name=name,
                    category=meta['category'],
                    sector_id=finance_sector.id,
                    is_approved=True,
                )
                db.session.add(skill)
                db.session.flush()
                skills_created += 1
            elif not skill.sector_id:
                skill.sector_id = finance_sector.id
            skill_map[name] = skill

            # Add skill aliases
            existing_sa = {a.name.lower() for a in (skill.aliases or [])}
            for alias in meta['aliases']:
                if alias.lower() not in existing_sa:
                    try:
                        db.session.add(SkillAlias(name=alias.lower(), skill_id=skill.id))
                    except Exception:
                        db.session.rollback()
        db.session.commit()
        print(f"[Skills] Created {skills_created} finance skills (total: {len(SKILLS)})")

        # ── 5. Create Role-Skill Links ──
        links_created = 0
        for role_title, skill_names in ROLE_SKILL_MAP.items():
            role = role_map.get(role_title)
            if not role:
                continue
            for skill_name in skill_names:
                skill = skill_map.get(skill_name)
                if not skill:
                    continue
                existing_link = RoleSkill.query.filter_by(role_id=role.id, skill_id=skill.id).first()
                if not existing_link:
                    db.session.add(RoleSkill(role_id=role.id, skill_id=skill.id))
                    links_created += 1
        db.session.commit()
        print(f"[Links] Created {links_created} role-skill mappings")

        # ── 6. Summary ──
        total_sectors = SectorTaxonomy.query.count()
        total_roles = RoleTaxonomy.query.count()
        total_skills = SkillTaxonomy.query.count()
        total_links = RoleSkill.query.count()
        print(f"\n{'='*50}")
        print(f"TAXONOMY SUMMARY")
        print(f"{'='*50}")
        print(f"  Sectors:          {total_sectors}")
        print(f"  Roles:            {total_roles}")
        print(f"  Skills:           {total_skills}")
        print(f"  Role-Skill Links: {total_links}")
        print(f"{'='*50}")


if __name__ == '__main__':
    run_seed()
