# Policy Unlearning with Proof Upload - Test Case

## Prerequisites
1. ✅ Backend server running with `ENABLE_POLICY_UNLEARNING=true` in `.env`
2. ✅ Cloudinary credentials configured in `.env`
3. ✅ Frontend running on http://localhost:5173
4. ✅ User authenticated and logged in
5. ✅ MongoDB and ChromaDB running

## Test Scenario 1: Complete Policy Update Workflow with Proof Upload

### Step 1: User Reports Policy Change

**Test Message (send in chat):**
```
I heard from the department that the exam registration deadline has been extended 
from 7 days to 14 days before the exam date. This was announced in the latest 
circular ACC/2026/03/EXT-001 dated March 1, 2026.
```

**What Gets Detected:**
- **Claim Type**: POLICY_UPDATE
- **Confidence**: High (mentions circular, specific dates)
- **Contradiction**: New policy (14 days) conflicts with existing (7 days)
- **Evidence**: Circular reference ACC/2026/03/EXT-001, date March 1, 2026

### Step 2: System Asks for Proof (NEW!)

**Expected Behavior:**
1. ✅ Chat response arrives normally (answers the question)
2. 🎯 **Proof Upload Modal Appears** automatically with message:
   ```
   I noticed you mentioned a policy change. To help verify this information, 
   could you please upload supporting documents (circular, official notice, 
   or screenshot)? This will help our team review and update the policy 
   database if needed.
   ```

3. Modal shows:
   - ✅ Your detected claim text
   - ✅ Confidence level badge (High/Medium/Low)
   - ✅ Claim type badge (POLICY_UPDATE)
   - ✅ File upload area
   - ✅ Accept: Images (PNG, JPG), PDFs, Text files
   - ✅ Max 10MB per file

**Backend Logs to Check:**
```
🎯 Policy claim detected: POLICY_UPDATE (confidence: 0.85)
⚠️  Contradictions detected: 2 chunks affected (confidence: 0.78)
📄 Evidence extracted: strength=strong, fields=['circular_number', 'date_mentioned']
⭐ Trust score computed: 0.75 (level: high, requires_approval: True)
🔔 Policy claim detected - requesting proof from user
```

### Step 3: User Uploads Proof Documents

**Action:**
1. Click "Choose Files" or drag-and-drop
2. Select proof files:
   - ✅ Screenshot of circular (image)
   - ✅ Official PDF notice
   - ✅ Email from department (as text file)

3. Files validate:
   - ✅ Type check: images/PDFs/text only
   - ✅ Size check: under 10MB each
   - ✅ Shows file list with names and sizes

4. Click "Submit X File(s)"

**Expected Behavior:**
- ✅ Upload progress bars shown
- ✅ Files uploaded to Cloudinary
- ✅ Ticket created with proof URLs
- ✅ Success message: "Policy update request submitted! Ticket: PT-20260303-XXXXXXXX"
- ✅ Modal closes

**Backend Logs:**
```
Proof uploaded: policy_proofs/PT-20260303-XXXXXXXX/20260303_143022_circular.png
Proof uploaded: policy_proofs/PT-20260303-XXXXXXXX/20260303_143023_notice.pdf
✅ Policy ticket created with proofs: PT-20260303-XXXXXXXX by user_123 (2 files)
```

### Step 4: Admin Reviews Ticket with Proofs

**Navigate to:** http://localhost:5173/policy-updates

**Pending Reviews Tab Shows:**
- ✅ Ticket ID: PT-20260303-XXXXXXXX
- ✅ Status: Pending Review (orange badge)
- ✅ Confidence: High (green badge)
- ✅ Claim text displayed
- ✅ Trust Score: 0.75
- ✅ 📎 Proofs Attached icon (2 files)

**Click "View Details" to See:**
```
Ticket Details:
├── Claim Text: "I heard from the department..."
├── Claim Type: POLICY_UPDATE
├── Confidence: High (0.85)
├── Trust Score: 0.75
├── Evidence Extracted:
│   ├── Circular: ACC/2026/03/EXT-001
│   ├── Date: March 1, 2026
│   └── Reference: Department announcement
├── Affected Chunks: 2 policy chunks
│   ├── Chunk 1: "Exam registration must be done 7 days before..."
│   └── Chunk 2: "Late registration deadline is..."
└── 📎 Attached Proofs:
    ├── 🖼️ circular.png [View Image]
    ├── 📄 notice.pdf [Download PDF]
    └── 📝 email.txt [View Text]
```

**Admin Can:**
- ✅ View images inline (zoomed)
- ✅ Download PDFs to read
- ✅ See all evidence clearly

### Step 5: Admin Approves with Context

**Action:**
1. Click "Approve" button
2. Fill approval form:
   ```
   Reviewer Notes: "Verified with HOD. Circular ACC/2026/03/EXT-001 confirmed. 
                    Updated deadline to 14 days effective immediately."
   
   New Policy Text: 
   "Exam Registration Timeline: Students must register for examinations at 
    least 14 days before the scheduled exam date. Late registrations will 
    not be accepted unless approved by the Dean's office.
    Reference: Academic Circular ACC/2026/03/EXT-001 dated March 1, 2026"
   ```
3. Click "Submit Approval"

**Expected Result:**
- ✅ Success toast: "Policy update approved! 3 chunks added"
- ✅ Ticket status → "Approved"
- ✅ **Proofs auto-deleted from Cloudinary** (cleanup)
- ✅ New chunks added to ChromaDB with status="active"
- ✅ Old chunks marked status="deprecated"
- ✅ Audit log created

**Backend Logs:**
```
Ticket PT-20260303-XXXXXXXX approved by admin_user
Deleted 2 proofs for approved ticket PT-20260303-XXXXXXXX
Policy chunks updated: 3 new active, 2 deprecated
Audit record created: AUDIT_20260303_001
```

### Step 6: Verify Policy Updated

**Test 1 - Ask Follow-up Question:**
```
What is the deadline for exam registration?
```

**Expected Answer:**
```
According to the latest policy (ACC/2026/03/EXT-001), students must register 
for examinations at least 14 days before the scheduled exam date. Late 
registrations require approval from the Dean's office.
```

**Test 2 - Check Audit Trail:**
Navigate to: Policy Updates → Audit Trail tab

Should show:
```
✅ March 3, 2026 14:35 - APPROVED
   Ticket: PT-20260303-XXXXXXXX
   Reviewer: admin_user
   Action: Policy Updated - Exam Registration Timeline
   Changes: Updated deadline from 7 days to 14 days
   Reference: ACC/2026/03/EXT-001
```

---

## Test Scenario 2: Policy Rejection Without Proof

### Step 1: User Reports Vague Policy Change

**Test Message:**
```
Someone told me that the internship minimum duration has been reduced 
to 4 weeks instead of 8 weeks.
```

**Expected Detection:**
- **Claim Type**: POLICY_UPDATE
- **Confidence**: Low-Medium (no evidence, vague source)
- **Trust Score**: ~0.3-0.5 (no circular, no date)
- **Proof Request**: ✅ Modal appears asking for proof

### Step 2: User Skips Proof Upload

**Action:**
- Click "Cancel" or "Skip" on proof modal

**Expected Behavior:**
- ⚠️ Warning: "Without proof, your claim may not be reviewed immediately"
- ✅ Ticket still created but flagged as "low confidence"
- OR: ❌ Ticket not created (if requires_proof is enforced)

### Step 3: Admin Reviews and Rejects

**Navigate to:** Policy Updates → Pending Reviews

**Click "View Details" on the ticket:**
- ⚠️ No proofs attached (shows "No proofs provided")
- ⚠️ Low trust score (0.35)
- ⚠️ No circular reference
- ⚠️ Vague source ("someone told me")

**Action:**
1. Click "Reject" button
2. Fill rejection form:
   ```
   Rejection Reason: "No supporting evidence provided. Could not verify 
                      with Academic Office. Internship minimum duration 
                      remains 8 weeks as per INTERNSHIP_POLICY_2025."
   ```
3. Click "Submit Rejection"

**Expected Result:**
- ✅ Success toast: "Policy update rejected"
- ✅ Ticket status → "Rejected"
- ✅ No changes to ChromaDB (old policy remains active)
- ✅ Proofs deleted if any were uploaded (cleanup)
- ✅ Audit log created

**Backend Logs:**
```
Ticket PT-20260303-YYYYYYYY rejected by admin_user
Reason: No supporting evidence provided
No policy chunks affected
```

---

## Test Scenario 3: Contradictory Claim with Strong Evidence

### Step 1: User Reports Major Policy Change

**Test Message:**
```
According to the new Academic Senate resolution AS/2026/15 dated March 2, 2026, 
the minimum CGPA requirement for final year project has been lowered from 6.5 
to 5.0 to allow more students to participate in research activities.
```

**Expected Detection:**
- **Claim Type**: POLICY_UPDATE  
- **Confidence**: High (has resolution number, date)
- **Contradiction**: Strong (6.5 → 5.0 is major change)
- **Trust Score**: ~0.75-0.85
- **Evidence**: Senate resolution AS/2026/15, date March 2, 2026

### Step 2: User Uploads Multiple Proofs

**Files to Upload:**
1. 📄 Senate_Resolution_AS_2026_15.pdf (2.3 MB)
2. 🖼️ Meeting_Minutes_Screenshot.png (1.8 MB)
3. 📝 HOD_Email_Confirmation.txt (3 KB)

**Expected Behavior:**
- ✅ All 3 files validated and uploaded
- ✅ Progress bars show 100% for each
- ✅ Ticket created with 3 proof URLs
- ✅ Success message with ticket ID

### Step 3: Admin Reviews with Strong Evidence

**Policy Updates Dashboard:**
- ✅ High confidence badge
- ✅ 📎 3 Proofs Attached
- ✅ Trust Score: 0.82 (very high)

**View Details:**
- ✅ Views PDF inline (Senate resolution)
- ✅ Sees screenshot clearly (meeting minutes)
- ✅ Reads email confirmation from HOD

**Approval Decision:**
```
Reviewer Notes: "Verified all 3 supporting documents. Senate resolution 
                 AS/2026/15 is authentic. Confirmed with Registrar's office. 
                 Updating CGPA requirement policy."

New Policy Text:
"Final Year Project Eligibility: Students with a minimum CGPA of 5.0 are 
 eligible to register for final year projects. This change aims to encourage 
 more students to engage in research activities.
 Effective from: Semester 1, 2026-27
 Reference: Academic Senate Resolution AS/2026/15 dated March 2, 2026"
```

**Expected Result:**
- ✅ Approval successful
- ✅ 4-5 chunks updated in ChromaDB
- ✅ 3 proofs deleted from Cloudinary
- ✅ Old chunks deprecated
- ✅ New chunks active

**Verification Query:**
```
What is the minimum CGPA required for final year project?
```

**Expected Answer:**
```
According to Academic Senate Resolution AS/2026/15, students need a minimum 
CGPA of 5.0 to be eligible for final year projects, effective from Semester 1 
of 2026-27.
```

---

## Test Scenario 4: Proof Upload Validations

### Test Invalid File Types

**Upload Attempts:**
1. ❌ `.exe` file → Error: "Invalid file type. Only images, PDFs, and text files allowed"
2. ❌ `.zip` file → Error: "Invalid file type"
3. ❌ `.docx` file → Error: "Invalid file type"
4. ✅ `.png` file → Success
5. ✅ `.pdf` file → Success
6. ✅ `.txt` file → Success

### Test File Size Limits

**Upload Attempts:**
1. ❌ 15 MB image → Error: "File too large. Maximum size is 10MB"
2. ❌ 12 MB PDF → Error: "File too large"
3. ✅ 9.8 MB PDF → Success
4. ✅ 500 KB image → Success

### Test Multiple Files

**Upload:**
- ✅ Select 5 images at once → All validate
- ✅ Remove 2 files before upload → Only 3 uploaded
- ✅ Add more after removing → Total 6 files uploaded

---

## Test Scenario 5: Cloudinary Cleanup Verification

### Check Cloudinary Dashboard

1. **During Upload:**
   - Go to: https://cloudinary.com/console/media_library
   - Navigate to: `policy_proofs/` folder
   - See subfolders: `PT-20260303-XXXXXXXX/`, `PT-20260303-YYYYYYYY/`
   - Each contains uploaded files

2. **After Approval:**
   - Refresh Cloudinary dashboard
   - ✅ Approved ticket folder DELETED
   - Files no longer exist

3. **After Rejection:**
   - Refresh Cloudinary dashboard
   - ✅ Rejected ticket folder DELETED
   - Files no longer exist

**Backend Logs to Verify:**
```
Deleted proof: policy_proofs/PT-20260303-XXXXXXXX/file1.png (200 OK)
Deleted proof: policy_proofs/PT-20260303-XXXXXXXX/file2.pdf (200 OK)
✅ Successfully deleted 2 proofs for ticket PT-20260303-XXXXXXXX
```

---

## Test Scenario 6: Edge Cases

### No Proof Modal Appears (Policy Claim Not Detected)

**Test Message:**
```
What are the exam registration deadlines?
```

**Expected:**
- ✅ Normal chat response
- ❌ No proof modal (just a question, not a claim)
- ❌ No ticket created

### User Closes Modal Without Uploading

**Action:**
1. Proof modal appears
2. User clicks "Cancel" or X button

**Expected:**
- ⚠️ Optional: Show warning or confirmation
- ✅ Modal closes
- ❌ No ticket created (proof required)
- ✅ User can continue chatting normally

### Network Failure During Upload

**Simulate:**
- Start upload
- Disconnect network mid-upload

**Expected:**
- ❌ Upload fails with error message
- ✅ Shows: "Upload failed: Network error. Please try again."
- ✅ Files remain selected (can retry)
- ✅ Graceful error handling

---

## Quick Test Checklist

- [ ] Message triggers claim detection
- [ ] Proof modal appears automatically
- [ ] File type validation works
- [ ] File size validation works
- [ ] Multiple files can be uploaded
- [ ] Upload progress shown correctly
- [ ] Ticket created with proof URLs
- [ ] Admin sees 📎 Proofs Attached icon
- [ ] Proofs displayed correctly in details modal
- [ ] Images viewable inline
- [ ] PDFs downloadable
- [ ] Approval deletes proofs from Cloudinary
- [ ] Rejection deletes proofs from Cloudinary
- [ ] Policy updated correctly after approval
- [ ] Chat reflects new policy after approval
- [ ] Audit trail shows approval/rejection
- [ ] Backend logs show proof operations

---

## Troubleshooting

### Modal Doesn't Appear
**Check:**
1. `response.policy_claim_detected` in chat response
2. Browser console for errors
3. ChatArea.jsx has ProofUploadModal integrated
4. Backend logs show "Policy claim detected"

### Uploads Fail
**Check:**
1. Cloudinary credentials in `.env` are correct
2. `cloudinary` package installed: `pip list | grep cloudinary`
3. Backend logs for Cloudinary errors
4. Network connectivity

### Proofs Not Visible in Admin Dashboard
**Check:**
1. `ticket.has_proofs` is true in MongoDB
2. `ticket.proof_urls` array has URLs
3. PolicyUpdatesPage.jsx renders proof display
4. Cloudinary URLs are accessible (public)

### Proofs Not Deleted After Approval
**Check:**
1. Backend logs for "Deleted proof" messages
2. Cloudinary dashboard manually
3. Error logs in `cloudinary_service.delete_ticket_proofs()`
4. Retry cleanup endpoint: `DELETE /api/v1/policy-proofs/{ticket_id}`

---

**Test Duration:** ~15-20 minutes for complete workflow
**Success Criteria:** All scenarios pass with expected behavior

---

## Test Scenario 2: Low-Confidence Claim (Should Still Create Ticket)

### Test Message:
```
I think the grading policy might have changed, but I'm not entirely sure.
```

### Expected Behavior:
- **Claim Type**: POLICY_UPDATE
- **Confidence**: Low
- **Trust Score**: Very low (no evidence)
- Still creates a ticket but with low confidence badge
- Likely to be rejected by admin

---

## Test Scenario 3: Policy Removal Claim

### Test Message:
```
The university has discontinued the optional summer semester program 
effective immediately. All references to summer courses should be removed 
from the academic calendar. Official notice: REG/2026/DISC/05.
```

### Expected Behavior:
- **Claim Type**: POLICY_REMOVAL
- Creates ticket with removal action
- After approval, related chunks are marked as deprecated (not deleted)

---

## Test Scenario 4: No Claim (Should NOT Trigger)

### Test Message:
```
What is the current policy on exam registration deadlines?
```

### Expected Behavior:
- No claim detected
- Regular query processing
- No ticket created
- Returns answer from existing policy documents

---

## Troubleshooting

### If No Ticket Appears:

1. **Check Backend Logs**:
   ```
   # Look for errors in the uvicorn terminal
   ERROR: Failed to detect claim
   ERROR: Failed to create policy ticket
   ```

2. **Verify Feature Flag**:
   ```bash
   # Check .env file
   cat .env | grep ENABLE_POLICY_UNLEARNING
   # Should output: ENABLE_POLICY_UNLEARNING=true
   ```

3. **Check MongoDB Connection**:
   ```python
   # In Python shell
   from app.db.mongo import get_database
   db = get_database()
   print(db.list_collection_names())
   # Should include: policy_update_tickets
   ```

4. **Restart Backend**:
   ```bash
   cd backend
   # Kill the server (Ctrl+C)
   uvicorn app.main:app --reload
   ```

### If API Returns 404:

- Backend might not have loaded the fixed query_service.py
- Restart the backend server
- Check that routes are registered in startup logs

---

## Success Criteria

✅ Test passes if:
1. Claim detection creates a ticket in MongoDB
2. Ticket appears in Policy Updates Dashboard
3. Approval process successfully adds chunks to ChromaDB
4. Old chunks are marked as deprecated
5. Subsequent queries return the new policy information
6. Audit trail records all actions

🎯 **Expected Time**: 2-3 minutes per test scenario
