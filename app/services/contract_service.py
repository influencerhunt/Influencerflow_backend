import os
import uuid
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from jinja2 import Template
from weasyprint import HTML
from io import BytesIO
from enum import Enum

from app.models.negotiation_models import (
    ContractTerms, ContractStatus, DigitalSignature, 
    NegotiationState, ContentDeliverable,
    BrandDetails, InfluencerProfile, NegotiationOffer,
    PlatformType, ContentType, LocationType
)

logger = logging.getLogger(__name__)

@dataclass
class ContractDeliverable:
    content_type: str
    quantity: int
    rate_per_piece: float
    total_amount: float
    description: str
    deadline: datetime

@dataclass 
class Contract:
    contract_id: str
    brand_name: str
    influencer_name: str
    total_amount: float
    currency: str
    deliverables: List[ContractDeliverable]
    terms_and_conditions: str
    timeline_start: datetime
    timeline_end: datetime
    payment_schedule: str
    created_at: datetime
    status: str = "draft"

class ContractGenerationService:
    """Service for generating and managing digital contracts"""
    
    def __init__(self):
        self.contracts: Dict[str, ContractTerms] = {}  # In-memory storage for MVP
        
        # Legal templates
        self.contract_template = self._get_contract_template()
        
    def generate_contract(
        self, 
        session_id: str, 
        negotiation_state: NegotiationState,
        brand_contact_email: str = "",
        brand_contact_name: str = "",
        influencer_email: str = "",
        influencer_contact: str = ""
    ) -> ContractTerms:
        """Generate a digital contract from agreed negotiation terms"""
        
        if not negotiation_state.agreed_terms:
            raise ValueError("No agreed terms found in negotiation state")
            
        contract_id = str(uuid.uuid4())
        agreed_terms = negotiation_state.agreed_terms
        brand = negotiation_state.brand_details
        influencer = negotiation_state.influencer_profile
        
        # Get currency information
        location_context = self._get_location_context(brand.brand_location)
        currency = location_context["currency"]
        
        # Calculate campaign dates
        campaign_start = datetime.now() + timedelta(days=7)  # Start in 1 week
        campaign_end = campaign_start + timedelta(days=agreed_terms.campaign_duration_days)
        
        # Determine governing law based on brand location
        governing_law = self._get_governing_law(brand.brand_location)
        
        contract_terms = ContractTerms(
            contract_id=contract_id,
            session_id=session_id,
            brand_name=brand.name,
            brand_contact_email=brand_contact_email or f"legal@{brand.name.lower().replace(' ', '')}.com",
            brand_contact_name=brand_contact_name or f"{brand.name} Legal Team",
            influencer_name=influencer.name,
            influencer_email=influencer_email or f"{influencer.name.lower().replace(' ', '.')}@email.com",
            influencer_contact=influencer_contact or "+1-XXX-XXX-XXXX",
            
            # Campaign Details
            campaign_title=f"{brand.name} x {influencer.name} Collaboration",
            campaign_description=f"Influencer marketing campaign for {brand.name} across {', '.join([p.value for p in brand.target_platforms])}",
            deliverables=agreed_terms.deliverables,
            total_amount=agreed_terms.total_price,
            currency=currency,
            payment_terms=agreed_terms.payment_terms,
            campaign_start_date=campaign_start,
            campaign_end_date=campaign_end,
            
            # Legal Terms
            usage_rights=agreed_terms.usage_rights,
            exclusivity_period_days=getattr(agreed_terms, 'exclusivity_period_days', None),
            revisions_included=agreed_terms.revisions_included,
            cancellation_policy=self._get_cancellation_policy(),
            dispute_resolution=self._get_dispute_resolution(),
            governing_law=governing_law,
            
            # Contract Metadata
            contract_date=datetime.now(),
            status=ContractStatus.PENDING_SIGNATURES
        )
        
        # Store contract
        self.contracts[contract_id] = contract_terms
        
        logger.info(f"Generated contract {contract_id} for session {session_id}")
        return contract_terms
    
    def get_contract(self, contract_id: str) -> Optional[ContractTerms]:
        """Retrieve contract by ID"""
        return self.contracts.get(contract_id)
    
    def get_contract_by_session(self, session_id: str) -> Optional[ContractTerms]:
        """Retrieve contract by session ID"""
        for contract in self.contracts.values():
            if contract.session_id == session_id:
                return contract
        return None
    
    def sign_contract(
        self, 
        contract_id: str, 
        signer_type: str,  # "brand" or "influencer"
        signer_name: str,
        signer_email: str,
        ip_address: str,
        user_agent: str
    ) -> ContractTerms:
        """Add digital signature to contract"""
        
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        signature = DigitalSignature(
            signer_name=signer_name,
            signer_email=signer_email,
            signature_timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if signer_type == "brand":
            if contract.brand_signature:
                raise ValueError("Brand has already signed this contract")
            contract.brand_signature = signature
            
            # Update status
            if contract.influencer_signature:
                contract.status = ContractStatus.FULLY_EXECUTED
            else:
                contract.status = ContractStatus.BRAND_SIGNED
                
        elif signer_type == "influencer":
            if contract.influencer_signature:
                raise ValueError("Influencer has already signed this contract")
            contract.influencer_signature = signature
            
            # Update status
            if contract.brand_signature:
                contract.status = ContractStatus.FULLY_EXECUTED
            else:
                contract.status = ContractStatus.INFLUENCER_SIGNED
        else:
            raise ValueError("signer_type must be 'brand' or 'influencer'")
        
        logger.info(f"Contract {contract_id} signed by {signer_type}: {signer_name}")
        return contract
    
    def generate_contract_pdf_content(self, contract_id: str) -> str:
        """Generate HTML content for contract that can be converted to PDF"""
        
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        # Prepare deliverables breakdown
        deliverables_html = ""
        for i, deliverable in enumerate(contract.deliverables, 1):
            # Convert price to local currency for display
            price_local = self._convert_from_usd(deliverable.proposed_price, contract.currency)
            price_formatted = self._format_currency(price_local, contract.currency)
            
            deliverables_html += f"""
            <tr>
                <td>{i}</td>
                <td>{deliverable.platform.value.title()}</td>
                <td>{deliverable.content_type.value.replace('_', ' ').title()}</td>
                <td>{deliverable.quantity}</td>
                <td>{price_formatted}</td>
            </tr>
            """
        
        # Convert total amount to local currency
        total_local = self._convert_from_usd(contract.total_amount, contract.currency)
        total_formatted = self._format_currency(total_local, contract.currency)
        
        # Signature sections
        brand_signature_html = ""
        influencer_signature_html = ""
        
        if contract.brand_signature:
            brand_signature_html = f"""
            <p><strong>✓ Signed digitally by:</strong> {contract.brand_signature.signer_name}</p>
            <p><strong>Date:</strong> {contract.brand_signature.signature_timestamp.strftime('%B %d, %Y at %I:%M %p UTC')}</p>
            """
        else:
            brand_signature_html = """
            <p>⏳ <em>Pending signature</em></p>
            <div class="signature-line">Brand Representative Signature</div>
            """
        
        if contract.influencer_signature:
            influencer_signature_html = f"""
            <p><strong>✓ Signed digitally by:</strong> {contract.influencer_signature.signer_name}</p>
            <p><strong>Date:</strong> {contract.influencer_signature.signature_timestamp.strftime('%B %d, %Y at %I:%M %p UTC')}</p>
            """
        else:
            influencer_signature_html = """
            <p>⏳ <em>Pending signature</em></p>
            <div class="signature-line">Influencer Signature</div>
            """
        
        template_data = {
            'contract': contract,
            'deliverables_html': deliverables_html,
            'total_formatted': total_formatted,
            'brand_signature_html': brand_signature_html,
            'influencer_signature_html': influencer_signature_html,
            'campaign_start_formatted': contract.campaign_start_date.strftime('%B %d, %Y'),
            'campaign_end_formatted': contract.campaign_end_date.strftime('%B %d, %Y'),
            'contract_date_formatted': contract.contract_date.strftime('%B %d, %Y')
        }
        
        return self.contract_template.render(**template_data)

    def generate_contract_pdf(self, contract_id: str) -> bytes:
        """Generate PDF from contract HTML"""
        try:
            # Get HTML content
            html_content = self.generate_contract_pdf_content(contract_id)
            
            # Convert to PDF
            html_doc = HTML(string=html_content)
            pdf_buffer = BytesIO()
            html_doc.write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            logger.info(f"Successfully generated PDF for contract {contract_id}")
            return pdf_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating PDF for contract {contract_id}: {e}")
            raise ValueError(f"Failed to generate PDF: {str(e)}")
    
    def get_contract_summary(self, contract_id: str) -> Dict[str, Any]:
        """Get contract summary for API responses"""
        
        contract = self.contracts.get(contract_id)
        if not contract:
            return {"error": f"Contract {contract_id} not found"}
        
        # Convert amount to local currency
        total_local = self._convert_from_usd(contract.total_amount, contract.currency)
        total_formatted = self._format_currency(total_local, contract.currency)
        
        return {
            "contract_id": contract.contract_id,
            "status": contract.status.value,
            "brand_name": contract.brand_name,
            "influencer_name": contract.influencer_name,
            "campaign_title": contract.campaign_title,
            "total_amount": total_formatted,
            "deliverables_count": len(contract.deliverables),
            "campaign_start": contract.campaign_start_date.isoformat(),
            "campaign_end": contract.campaign_end_date.isoformat(),
            "signatures": {
                "brand_signed": contract.brand_signature is not None,
                "influencer_signed": contract.influencer_signature is not None,
                "fully_executed": contract.status == ContractStatus.FULLY_EXECUTED
            },
            "created_date": contract.contract_date.isoformat()
        }
    
    def list_contracts(self) -> List[Dict[str, Any]]:
        """List all contracts with summaries"""
        return [self.get_contract_summary(contract_id) for contract_id in self.contracts.keys()]
    
    def _get_governing_law(self, brand_location) -> str:
        """Determine governing law based on brand location"""
        law_mapping = {
            "US": "State of Delaware, United States",
            "UK": "England and Wales",
            "Canada": "Province of Ontario, Canada", 
            "Australia": "State of New South Wales, Australia",
            "India": "Laws of India",
            "Germany": "Laws of Germany",
            "France": "Laws of France",
            "Brazil": "Laws of Brazil",
            "Japan": "Laws of Japan"
        }
        
        if brand_location and brand_location.value in law_mapping:
            return law_mapping[brand_location.value]
        return "Laws of Delaware, United States"  # Default
    
    def _get_cancellation_policy(self) -> str:
        """Standard cancellation policy"""
        return """Either party may terminate this agreement with 7 days written notice. In case of termination:
        • If terminated by Brand: Full payment for completed deliverables + 50% for work in progress
        • If terminated by Influencer without cause: Refund of advance payment minus completed work
        • Completed content may be used by Brand as per usage rights terms"""
    
    def _get_dispute_resolution(self) -> str:
        """Standard dispute resolution clause"""
        return """Any disputes arising from this agreement shall be resolved through:
        1. Good faith negotiation (30 days)
        2. Mediation with mutually agreed mediator (60 days)
        3. Binding arbitration as final resort
        Both parties waive right to jury trial for disputes under this agreement."""
    
    def _get_contract_template(self) -> Template:
        """HTML template for contract generation"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Influencer Marketing Agreement - {{contract.contract_id}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .section { margin: 20px 0; }
        .section-title { font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        .deliverables-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .deliverables-table th, .deliverables-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .deliverables-table th { background-color: #f2f2f2; font-weight: bold; }
        .signature-section { margin-top: 40px; }
        .signature-line { border-bottom: 1px solid #333; width: 300px; height: 30px; margin: 10px 0; }
        .contract-meta { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .status-badge { display: inline-block; padding: 5px 10px; border-radius: 15px; color: white; font-size: 12px; }
        .status-pending { background-color: #ffc107; }
        .status-signed { background-color: #28a745; }
        .status-executed { background-color: #007bff; }
        .highlight { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>INFLUENCER MARKETING AGREEMENT</h1>
        <p><strong>Contract ID:</strong> {{contract.contract_id}}</p>
        <p><strong>Date:</strong> {{contract_date_formatted}}</p>
        <span class="status-badge 
            {% if contract.status == 'fully_executed' %}status-executed
            {% elif contract.brand_signature and contract.influencer_signature %}status-signed
            {% else %}status-pending{% endif %}">
            {{contract.status.value.replace('_', ' ').title()}}
        </span>
    </div>

    <div class="contract-meta">
        <h3>📋 Agreement Overview</h3>
        <p><strong>Campaign:</strong> {{contract.campaign_title}}</p>
        <p><strong>Total Investment:</strong> {{total_formatted}}</p>
        <p><strong>Campaign Period:</strong> {{campaign_start_formatted}} to {{campaign_end_formatted}}</p>
    </div>

    <div class="section">
        <div class="section-title">1. PARTIES</div>
        <p><strong>Brand ("Client"):</strong><br>
        {{contract.brand_name}}<br>
        Contact: {{contract.brand_contact_name}}<br>
        Email: {{contract.brand_contact_email}}</p>
        
        <p><strong>Influencer ("Creator"):</strong><br>
        {{contract.influencer_name}}<br>
        Email: {{contract.influencer_email}}<br>
        Contact: {{contract.influencer_contact}}</p>
    </div>

    <div class="section">
        <div class="section-title">2. CAMPAIGN DETAILS</div>
        <p><strong>Campaign Description:</strong> {{contract.campaign_description}}</p>
        <p><strong>Campaign Duration:</strong> {{campaign_start_formatted}} to {{campaign_end_formatted}}</p>
    </div>

    <div class="section">
        <div class="section-title">3. DELIVERABLES & COMPENSATION</div>
        <table class="deliverables-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Platform</th>
                    <th>Content Type</th>
                    <th>Quantity</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
                {{deliverables_html|safe}}
            </tbody>
            <tfoot>
                <tr style="font-weight: bold; background-color: #f8f9fa;">
                    <td colspan="4">TOTAL COMPENSATION</td>
                    <td>{{total_formatted}}</td>
                </tr>
            </tfoot>
        </table>
    </div>

    <div class="section">
        <div class="section-title">4. PAYMENT TERMS</div>
        <p>{{contract.payment_terms}}</p>
        <p><strong>Currency:</strong> {{contract.currency}}</p>
    </div>

    <div class="section">
        <div class="section-title">5. CONTENT REQUIREMENTS</div>
        <p><strong>Revisions Included:</strong> {{contract.revisions_included}} rounds of revisions</p>
        <p><strong>Usage Rights:</strong> {{contract.usage_rights}}</p>
        {% if contract.exclusivity_period_days %}
        <p><strong>Exclusivity Period:</strong> {{contract.exclusivity_period_days}} days</p>
        {% endif %}
    </div>

    <div class="section">
        <div class="section-title">6. LEGAL TERMS</div>
        <p><strong>Cancellation Policy:</strong></p>
        <div class="highlight">{{contract.cancellation_policy}}</div>
        
        <p><strong>Dispute Resolution:</strong></p>
        <div class="highlight">{{contract.dispute_resolution}}</div>
        
        <p><strong>Governing Law:</strong> {{contract.governing_law}}</p>
    </div>

    <div class="signature-section">
        <div class="section-title">7. SIGNATURES</div>
        
        <div style="display: flex; justify-content: space-between; margin-top: 30px;">
            <div style="width: 45%;">
                <h4>BRAND REPRESENTATIVE</h4>
                {{brand_signature_html|safe}}
                <p><strong>Name:</strong> {{contract.brand_contact_name}}</p>
                <p><strong>Company:</strong> {{contract.brand_name}}</p>
            </div>
            
            <div style="width: 45%;">
                <h4>INFLUENCER</h4>
                {{influencer_signature_html|safe}}
                <p><strong>Name:</strong> {{contract.influencer_name}}</p>
                <p><strong>Email:</strong> {{contract.influencer_email}}</p>
            </div>
        </div>
    </div>

    <div class="contract-meta" style="margin-top: 40px;">
        <p><strong>⚖️ Legal Notice:</strong> This is a legally binding agreement. Both parties acknowledge they have read, understood, and agree to be bound by these terms.</p>
        <p><strong>📄 Document Version:</strong> {{contract.contract_version}} | <strong>Generated:</strong> {{contract_date_formatted}}</p>
    </div>
</body>
</html>
        """
        return Template(template_str)

    def _format_currency(self, amount: float, currency: str) -> str:
        """Simple currency formatting."""
        currency_symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CAD': 'C$', 'AUD': 'A$', 'CHF': 'CHF ', 'CNY': '¥',
            'INR': '₹', 'BRL': 'R$', 'MXN': 'MX$', 'KRW': '₩'
        }
        
        symbol = currency_symbols.get(currency, f'{currency} ')
        
        if currency in ['JPY', 'KRW']:
            return f"{symbol}{amount:,.0f}"
        else:
            return f"{symbol}{amount:,.2f}"

    def _convert_from_usd(self, amount: float, to_currency: str) -> float:
        """Simple fallback currency conversion from USD."""
        if to_currency == 'USD':
            return amount
        
        # Approximate exchange rates
        rates_from_usd = {
            'EUR': 0.85, 'GBP': 0.79, 'CAD': 1.35, 'AUD': 1.52,
            'JPY': 150.0, 'INR': 83.0, 'BRL': 5.0, 'MXN': 18.0,
            'CHF': 0.91, 'CNY': 7.2, 'KRW': 1320.0
        }
        
        rate = rates_from_usd.get(to_currency, 1.0)
        return amount * rate

    def _get_location_context(self, location: LocationType) -> Dict[str, str]:
        """Get basic location context."""
        location_contexts = {
            LocationType.INDIA: {
                "payment_methods": "Bank transfer, UPI, or digital wallet",
                "tax_info": "GST applicable as per Indian tax laws",
                "currency": "INR"
            },
            LocationType.US: {
                "payment_methods": "ACH transfer or wire transfer", 
                "tax_info": "1099-NEC will be issued for payments over $600",
                "currency": "USD"
            },
            LocationType.UK: {
                "payment_methods": "BACS or faster payments",
                "tax_info": "Subject to UK tax regulations",
                "currency": "GBP"
            }
        }
        
        return location_contexts.get(location, {
            "payment_methods": "International wire transfer",
            "tax_info": "Subject to local tax regulations", 
            "currency": "USD"
        })

# Global instance
contract_service = ContractGenerationService()
