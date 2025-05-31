# InfluencerFlow Contract System - Postman Testing Guide

## 🚀 Setup Instructions

### 1. Start the FastAPI Server
```bash
cd /Users/vardaanbhatia/Desktop/CodeGit/Influencerflow_backend
python -m uvicorn main:app --reload --port 8000
```

### 2. Import Postman Collection
1. Open Postman
2. Click "Import" button
3. Select the file: `InfluencerFlow_Contract_System.postman_collection.json`
4. The collection will be imported with all endpoints ready to test

### 3. Environment Variables
The collection uses these variables (auto-set):
- `baseUrl`: http://localhost:8000
- `contractId`: 16dbf6a4-6cd0-41af-a2fc-8caeb40e6201

## 📋 Testing Workflow

### Phase 1: Generate a Fresh Contract
Before testing the API, generate a new contract:
```bash
python complete_pdf_demo.py
```
Copy the generated contract ID and update the `contractId` variable in Postman.

### Phase 2: API Testing Sequence

#### Step 1: Basic Health Check
- **Request**: `9. Health Check`
- **Expected**: Server running confirmation
- **Purpose**: Verify server is accessible

#### Step 2: Contract Information
- **Request**: `1. Get Contract Details`
- **Expected**: Full contract JSON with terms, parties, status
- **Purpose**: Verify contract exists and data is complete

#### Step 3: Contract Summary
- **Request**: `2. Get Contract Summary`
- **Expected**: Simplified contract overview
- **Purpose**: Test summary endpoint functionality

#### Step 4: View Contract HTML
- **Request**: `5. View Contract HTML`
- **Expected**: HTML content of the contract
- **Purpose**: Verify HTML generation for web display

#### Step 5: Download PDF (Initial)
- **Request**: `6. Download Contract PDF`
- **Expected**: PDF file download (357KB+)
- **Purpose**: Test initial PDF generation without signatures

### Phase 3: Digital Signature Testing

#### Step 6: Brand Signs Contract
- **Request**: `7. Sign Contract (Brand)`
- **Expected**: Updated contract with brand signature
- **Purpose**: Test brand signing functionality

#### Step 7: Check Status After Brand Signature
- **Request**: `4. Get Contract Status`
- **Expected**: Status = "brand_signed"
- **Purpose**: Verify status update after brand signature

#### Step 8: Download PDF After Brand Signature
- **Request**: `6. Download Contract PDF`
- **Expected**: PDF with brand signature (390KB+)
- **Purpose**: Test PDF generation with brand signature

#### Step 9: Influencer Signs Contract
- **Request**: `8. Sign Contract (Influencer)`
- **Expected**: Updated contract with both signatures
- **Purpose**: Test influencer signing functionality

#### Step 10: Final Status Check
- **Request**: `4. Get Contract Status`
- **Expected**: Status = "fully_executed"
- **Purpose**: Verify final contract status

#### Step 11: Download Final PDF
- **Request**: `6. Download Contract PDF`
- **Expected**: PDF with both signatures (275KB+)
- **Purpose**: Test final PDF generation

### Phase 4: Additional Testing

#### Step 12: List All Contracts
- **Request**: `3. List All Contracts`
- **Expected**: Array including your test contract
- **Purpose**: Verify contract listing functionality

## 🔍 Expected Response Examples

### Contract Details Response
```json
{
  "contract_id": "16dbf6a4-6cd0-41af-a2fc-8caeb40e6201",
  "status": "pending_signatures",
  "brand_name": "PDF Demo Corp",
  "influencer_name": "Demo Influencer",
  "total_amount": 1500.0,
  "currency": "USD",
  "created_at": "2025-06-01T00:35:00",
  "signatures": []
}
```

### Contract Status Response
```json
{
  "contract_id": "16dbf6a4-6cd0-41af-a2fc-8caeb40e6201",
  "status": "fully_executed",
  "brand_signed": true,
  "influencer_signed": true,
  "brand_signature_date": "2025-06-01T00:36:00",
  "influencer_signature_date": "2025-06-01T00:37:00"
}
```

### Sign Contract Response
```json
{
  "message": "Contract signed successfully",
  "contract_id": "16dbf6a4-6cd0-41af-a2fc-8caeb40e6201",
  "signer_type": "brand",
  "signature_timestamp": "2025-06-01T00:36:00",
  "new_status": "brand_signed"
}
```

## 🎯 Success Criteria

### PDF Downloads
- ✅ Initial PDF: ~357KB (unsigned)
- ✅ Brand-signed PDF: ~390KB (with brand signature)
- ✅ Final PDF: ~275KB (fully signed)

### Status Transitions
- ✅ Initial: `pending_signatures`
- ✅ After brand: `brand_signed`
- ✅ After influencer: `fully_executed`

### Response Times
- ✅ Contract details: < 100ms
- ✅ PDF generation: < 2 seconds
- ✅ Signing: < 200ms

## 🚨 Troubleshooting

### Common Issues

#### 1. Contract Not Found (404)
- **Cause**: Invalid or expired contract ID
- **Solution**: Generate new contract with `complete_pdf_demo.py`

#### 2. Server Connection Error
- **Cause**: FastAPI server not running
- **Solution**: Start server with `uvicorn main:app --reload --port 8000`

#### 3. PDF Download Issues
- **Cause**: WeasyPrint dependency issues
- **Solution**: Reinstall with `pip install weasyprint`

#### 4. Signing Fails
- **Cause**: Missing required fields in request body
- **Solution**: Ensure all fields (signer_type, signer_name, signer_email, ip_address, user_agent) are provided

### Server Logs
Monitor server logs for detailed error information:
```bash
tail -f server.log
```

## 📊 Performance Benchmarks

Based on successful testing:
- **Contract retrieval**: ~50ms
- **PDF generation**: ~1.5 seconds
- **Contract signing**: ~100ms
- **Status updates**: ~30ms

## 🎉 Next Steps

After successful Postman testing:
1. **Production deployment** considerations
2. **Authentication integration** (JWT tokens)
3. **Rate limiting** implementation
4. **File storage** for persistent PDF storage
5. **Email notifications** for contract events

## 📁 Files Created
- `InfluencerFlow_Contract_System.postman_collection.json` - Postman collection
- PDF files from testing (demo_contract_*.pdf)
- Test scripts and documentation
