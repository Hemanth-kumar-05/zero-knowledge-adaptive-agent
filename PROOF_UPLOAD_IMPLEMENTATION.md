# Policy Unlearning with Proof Upload - Implementation Guide

## ✅ Implemented (Backend)

### 1. Requirements & Dependencies
- ✅ Added `cloudinary>=1.36.0` to requirements.txt
- ✅ Added `python-magic>=0.4.27` for file type detection
- ✅ Added Cloudinary config vars to .env

### 2. Cloudinary Service (`backend/app/services/cloudinary_service.py`)
- ✅ `upload_proof()` - Upload files to Cloudinary
- ✅ `delete_proof()` - Delete single proof file
- ✅ `delete_ticket_proofs()` - Delete all proofs for a ticket
- ✅ Singleton instance `cloudinary_service`

### 3. Modified Query Flow (`backend/app/services/query_service.py`)
- ✅ Changed from auto-creating tickets to storing claim data in session
- ✅ Returns `policy_claim_detected` in query response
- ✅ Added `PolicyClaimDetected` schema with `requires_proof` flag
- ✅ Stores pending claim in session metadata

### 4. Proof Upload API (`backend/app/api/routes/policy_proofs.py`)
- ✅ `POST /policy-proofs/upload` - Upload single proof file
- ✅ `POST /policy-proofs/create-ticket` - Create ticket with proofs
- ✅ `DELETE /policy-proofs/{ticket_id}` - Delete ticket proofs

### 5. Updated Policy Updates Routes
- ✅ Approval endpoint deletes proofs after processing
- ✅ Rejection endpoint deletes proofs after processing

### 6. Database Schema Updates
- ✅ Tickets now support `proof_urls` array and `has_proofs` flag

## ✅ Implemented (Frontend)

### 1. API Client Updates (`frontend/src/api/client.js`)
- ✅ `uploadPolicyProof()` - Upload proof file
- ✅ `createTicketWithProofs()` - Create ticket with uploaded proofs

### 2. Proof Upload Modal Component
- ✅ Created `ProofUploadModal.jsx` with:
  - Multi-file selection
  - File type validation (images, PDFs, text files)
  - File size validation (10MB max)
  - Upload progress tracking
  - Error handling

## 🚧 TODO - Complete Implementation

### 1. Frontend Components

#### A. Create ProofUploadModal.css
```css
/* Create: frontend/src/components/ProofUploadModal.css */
- Modal overlay and content styling
- File list and progress bars
- Badge styles for confidence levels
```

#### B. Update ChatArea.jsx
```javascript
// Add proof upload modal handling
import ProofUploadModal from './ProofUploadModal';

// In ChatArea component:
const [showProofModal, setShowProofModal] = useState(false);
const [policyClaimData, setPolicyClaimData] = useState(null);

// After receiving query response:
if (response.policy_claim_detected) {
  setPolicyClaimData(response.policy_claim_detected);
  setShowProofModal(true);
  // Show the message asking for proof
}

// Add modal to render:
<ProofUploadModal
  isOpen={showProofModal}
  onClose={() => setShowProofModal(false)}
  policyClaimData={policyClaimData}
  sessionId={currentSession?.id}
  onSuccess={(ticketId) => {
    // Show success message
    showToast(`Policy update request submitted! Ticket: ${ticketId}`, 'success');
    setShowProofModal(false);
  }}
/>
```

#### C. Update PolicyUpdatesPage.jsx - Show Proofs
```javascript
// Add proof display in ticket detail modal
{ticket.has_proofs && ticket.proof_urls && (
  <div className="ticket-proofs">
    <h4>Attached Proofs:</h4>
    {ticket.proof_urls.map((url, idx) => (
      <div key={idx} className="proof-item">
        {url.includes('.pdf') ? (
          <a href={url} target="_blank" rel="noopener noreferrer">
            📄 View PDF {idx + 1}
          </a>
        ) : (
          <img src={url} alt={`Proof ${idx + 1}`} />
        )}
      </div>
    ))}
  </div>
)}
```

### 2. Environment Setup

#### Update .env file with Cloudinary credentials:
```bash
# Get free account from: https://cloudinary.com/
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

### 3. Install New Dependencies
```bash
cd backend
pip install cloudinary python-magic
```

### 4. Restart Server
```bash
cd backend
uvicorn app.main:app --reload
```

## 📋 Complete User Flow

1. **User mentions policy change in chat**
   ```
   "The exam registration deadline has been extended to 14 days..."
   ```

2. **System detects claim**
   - Claim detection service analyzes message
   - Contradiction analyzer finds conflicts
   - Trust scorer computes confidence

3. **Modal appears asking for proof**
   - Shows detected claim details
   - Requests supporting documents
   - User selects files to upload

4. **User uploads proof**
   - Files validated (type, size)
   - Progress shown for each file
   - Files stored in Cloudinary temporarily

5. **Ticket created**
   - Ticket includes proof URLs
   - User receives confirmation
   - Admin dashboard updated

6. **Admin reviews in Policy Updates dashboard**
   - Sees ticket with claim text
   - Views uploaded proofs (images inline, PDFs as download)
   - Makes decision with full context

7. **After approval/rejection**
   - Proofs automatically deleted from Cloudinary
   - Policy updated (if approved)
   - User notified of decision

## 🎯 Test Scenario

### Test Message:
```
I heard from the department that the exam registration deadline has been extended 
from 7 days to 14 days before the exam date. This was announced in the latest  
circular ACC/2026/03/EXT-001 dated March 1, 2026.
```

### Expected Flow:
1. Send message in chat
2. Receive response + modal appears
3. Upload circular screenshot/PDF
4. Ticket appears in Policy Updates dashboard  5. Admin views proof and approves
6. Policy updated, proofs deleted

## 🔒 Security & Best Practices

- ✅ File type validation (images, PDFs, text only)
- ✅ File size limits (10MB max)
- ✅ Authentication required for all endpoints
- ✅ Temporary storage (deleted after processing)
- ✅ Tagged uploads for easy cleanup
- ✅ Secure URLs from Cloudinary

## 📱 Cloudinary Setup Instructions

1. Go to https://cloudinary.com/
2. Sign up for free account
3. Get credentials from Dashboard:
   - Cloud Name
   - API Key
   - API Secret
4. Update `.env` file with credentials

## 🐛 Troubleshooting

### Uploads failing?
- Check Cloudinary credentials in .env
- Verify `cloudinary` package installed
- Check file size limits

### Modal not showing?
- Check console for errors
- Verify policy claim detection is working
- Check ChatArea component updated

### Proofs not displaying?
- Check ticket.proof_urls array
- Verify Cloudinary URLs are accessible
- Check image/PDF rendering in browser

## 📝 Next Steps

1. Create ProofUploadModal.css
2. Update ChatArea.jsx to show modal
3. Update PolicyUpdatesPage.jsx to display proofs
4. Set up Cloudinary account and update .env
5. Install new dependencies
6. Test the complete flow
