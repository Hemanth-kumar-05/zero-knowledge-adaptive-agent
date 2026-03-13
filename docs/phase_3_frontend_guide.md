# Policy Updates Admin Frontend - Quick Start Guide

## ✅ What Was Created

### New Components
1. **PolicyUpdatesPage.jsx** - Main admin dashboard component
2. **PolicyUpdatesPage.css** - Styling matching existing design
3. **Updated Files:**
   - `App.jsx` - Added route for `/policy-updates`
   - `Sidebar.jsx` - Added "Policy Updates" menu item
   - `api/client.js` - Added 6 new API endpoints

---

## 🚀 How to Access

### For Admin/Faculty Users:
1. **Sign in to the application**
2. **Click your user profile** in the sidebar footer
3. **Select "Policy Updates"** from the dropdown menu

Or directly navigate to: `http://localhost:5173/policy-updates`

---

## 📱 Features Overview

### 4 Main Tabs:

#### 1. **Pending Reviews** (Default)
- Shows all policy update tickets awaiting review
- **Key Information Displayed:**
  - Ticket ID (e.g., PT-20250303-A1B2C3D4)
  - User's policy change claim
  - Trust score (0-100%)
  - Confidence level (Low/Medium/High)
  - Number of affected chunks
  - Evidence (circular numbers, dates, references)
  - Report date/time

- **Actions Available:**
  - **View Details** - See full ticket information
  - **Approve** - Accept and implement policy update
  - **Reject** - Deny the policy change request

#### 2. **All Tickets**
- Complete list of all tickets with filtering
- **Filter Options:**
  - All Status
  - Pending Review
  - Approved
  - Rejected
  - Implemented

- Table view showing:
  - Ticket ID
  - Claim text (truncated)
  - Trust score with color coding
  - Status badge
  - Report date
  - Quick view button

#### 3. **Statistics**
- Real-time system metrics
- **4 Main Stat Cards:**
  1. **Total Tickets**
     - Breakdown by status
     - Pending vs Implemented count
  
  2. **Average Trust Score**
     - Overall trust percentage
     - Approval rate
  
  3. **Chunks Updated**
     - Deprecated chunks count
     - New chunks created
  
  4. **Average Processing Time**
     - Time from submission to implementation

- **Trust Score Distribution Chart**
  - Visual breakdown: Low, Medium, High
  - Color-coded bars with counts

#### 4. **Audit Trail**
- Complete history of all policy changes
- Timeline view with:
  - Change type
  - Ticket ID
  - Performed by (user)
  - Version change (e.g., 1 → 2)
  - Chunks affected
  - Rollback availability indicator
  - Date/time

---

## 🔍 Detailed Workflows

### Reviewing a Policy Update Ticket

#### Step 1: View Ticket Details
1. Click **"View Details"** on any ticket
2. **Modal shows:**
   - Complete ticket information
   - User's full claim text
   - Evidence details (circular, dates, references)
   - Affected chunks with:
     - Document ID and section
     - Current chunk text (150 chars preview)
     - Contradiction score

#### Step 2: Approve Policy Update
1. Click **"Approve"** button
2. **Approval Modal Opens:**
   - Shows ticket summary
   - Affected chunks count
   
3. **Fill Required Fields:**
   - **Reviewer Notes** (optional)
     - Add verification details
     - Add source references
     - Add approval reasoning
   
   - **New Policy Text** (required)
     - Enter complete updated policy text
     - This will be:
       - Chunked (800 chars, 100 overlap)
       - Embedded
       - Added to ChromaDB
       - Replaces deprecated chunks

4. Click **"Approve & Execute"**
   - System automatically:
     - Deprecates old chunks
     - Re-embeds new policy text
     - Updates policy version
     - Writes audit record
     - Marks ticket as implemented
   
5. **Success notification shows:**
   - "Policy update approved! X chunks added"

#### Step 3: Reject Policy Update
1. Click **"Reject"** button
2. **Rejection Modal Opens:**
   - Shows ticket summary
   
3. **Enter Rejection Reason:** (required)
   - Explain why (insufficient evidence, incorrect info, etc.)

4. Click **"Confirm Rejection"**
5. Ticket status updates to "Rejected"

---

## 🎨 Design Features

### Color-Coded Elements

#### Trust Scores / Confidence Levels:
- 🟢 **High (85%+)** - Green badge
- 🔵 **Medium (60-84%)** - Blue badge
- 🟡 **Low (<60%)** - Yellow badge

#### Status Badges:
- 🟠 **Pending Review** - Orange
- 🟢 **Approved** - Green
- 🔴 **Rejected** - Red
- 🟣 **Implemented** - Purple

### Interactive Elements:
- **Hover Effects:** Cards lift on hover
- **Loading States:** Spinner animations
- **Empty States:** Friendly messages with icons
- **Toast Notifications:** Success/error feedback
- **Responsive Design:** Works on mobile, tablet, desktop

---

## 💻 Technical Details

### API Endpoints Used:
```javascript
// Get tickets (with optional status filter)
GET /api/v1/policy-updates/tickets?status=pending_review

// Get single ticket
GET /api/v1/policy-updates/tickets/{ticket_id}

// Approve ticket
POST /api/v1/policy-updates/tickets/{ticket_id}/approve
Body: { reviewer_notes, new_policy_text }

// Reject ticket
POST /api/v1/policy-updates/tickets/{ticket_id}/reject
Body: { rejection_reason }

// Get audit log
GET /api/v1/policy-updates/audit?limit=50

// Get statistics
GET /api/v1/policy-updates/stats
```

### State Management:
- React hooks (`useState`, `useEffect`)
- Local state for tabs, modals, forms
- Async data fetching with error handling
- Toast notifications for user feedback

### Authentication:
- JWT token from `localStorage`
- Automatic header injection via axios interceptor
- Redirects to login on 401 errors
- User context from `auth.getUser()`

---

## 🔧 Customization

### Adding More Filters:
Edit `PolicyUpdatesPage.jsx`:
```jsx
<select className="filter-select">
  <option value="">All Status</option>
  <option value="pending_review">Pending Review</option>
  // Add more options here
</select>
```

### Changing Colors:
Edit `PolicyUpdatesPage.css`:
```css
.confidence-badge-high {
  background-color: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}
```

### Adjusting Card Layout:
```css
.tickets-grid {
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  /* Change 400px to adjust card minimum width */
}
```

---

## 📊 Example Use Cases

### Use Case 1: Regular Review Session
1. Admin logs in daily
2. Navigates to "Pending Reviews"
3. Sees 5 new tickets
4. Reviews each ticket:
   - Views details
   - Checks evidence
   - Verifies with official sources
   - Approves or rejects
5. System automatically updates knowledge base

### Use Case 2: Monitoring System Health
1. Admin navigates to "Statistics" tab
2. Reviews metrics:
   - Trust score trending up (good)
   - Approval rate at 75% (healthy)
   - Processing time under 3 hours (efficient)
3. Identifies patterns:
   - Most claims are medium confidence
   - Few rejections (users providing good evidence)

### Use Case 3: Auditing Changes
1. Admin navigates to "Audit Trail"
2. Views timeline of all changes
3. Identifies specific policy update
4. Sees who approved it and when
5. Notes "Rollback Available" badge
6. Can revert if needed (via API)

### Use Case 4: Quality Control
1. Admin filters "All Tickets" by "Implemented"
2. Reviews recently approved changes
3. Spot-checks policy accuracy
4. Verifies chunks updated correctly

---

## 🚨 Troubleshooting

### Problem: "Failed to load tickets"
**Solution:**
- Check backend is running (port 8000)
- Verify Feature flag: `ENABLE_POLICY_UNLEARNING=True`
- Check browser console for errors
- Verify JWT token in localStorage

### Problem: Empty "Pending Reviews"
**Possible Causes:**
- No new tickets submitted
- All tickets already processed
- Detection system not triggering
**Check:**
- Go to "All Tickets" tab
- Select "All Status" filter
- See if any tickets exist

### Problem: Approval/Rejection not working
**Solution:**
- Check required fields filled
- Verify user has admin permissions
- Check backend logs for errors
- Ensure ticket status is "pending_review"

### Problem: Statistics not loading
**Solution:**
- Backend may need data aggregation
- Check if any tickets exist
- Verify stats endpoint returns data
- Check browser network tab for errors

---

## 🎯 Best Practices

### For Reviewers:
1. **Always verify evidence** before approving
2. **Check affected chunks** to understand impact
3. **Write clear rejection reasons** to help users improve
4. **Use reviewer notes** to document verification sources
5. **Test new policy text** for completeness before approving

### For System Admins:
1. **Monitor statistics regularly** (daily/weekly)
2. **Review audit trail** for compliance
3. **Set up alerts** for high-priority tickets (high trust score)
4. **Train reviewers** on approval criteria
5. **Maintain documentation** of approval guidelines

---

## 📝 Keyboard Shortcuts

While on Policy Updates page:
- **Tab Navigation:** Use Tab key to move between buttons
- **Enter:** Confirm modal actions
- **Escape:** Close modals
- **Arrow Keys:** Scroll through lists

---

## 🔐 Security Notes

- All endpoints require **authentication**
- JWT tokens auto-refresh on valid requests
- 401 errors automatically redirect to login
- No sensitive data stored in browser localStorage (only token)
- All actions logged in audit trail for accountability

---

## 📱 Mobile Responsiveness

The interface is fully responsive:
- **Mobile (< 768px):**
  - Single column card layout
  - Stacked metrics
  - Touch-friendly buttons
  - Scrollable tabs

- **Tablet (768-1024px):**
  - Two columns for cards
  - Compact stats grid
  - Side-scrolling tables

- **Desktop (> 1024px):**
  - Three columns for cards
  - Full tables visible
  - Optimal spacing

---

## 🎓 Training Resources

### For New Admins:
1. Start with **"Pending Reviews"** tab
2. Click **"View Details"** on sample tickets
3. Review **Statistics** to understand system health
4. Check **Audit Trail** to see past changes
5. Practice approvals on low-risk tickets first

### Key Metrics to Understand:
- **Trust Score:** AI's confidence in the claim (0-100%)
- **Confidence Level:** Overall classification (Low/Medium/High)
- **Contradiction Score:** How much claim differs from current policy
- **Affected Chunks:** Number of knowledge base pieces to update

---

## 🔄 Integration with Main App

The Policy Updates page integrates seamlessly:
1. **Same authentication system** (JWT)
2. **Consistent design** (colors, fonts, spacing)
3. **Unified navigation** (same sidebar)
4. **Shared components** (Modal, Toast)
5. **Same API client** (axios with interceptors)

Users can switch between:
- Chat interface
- Preferences
- Memory dashboard
- **Policy Updates** (new)

---

## 📞 Support

If you encounter issues:
1. Check browser console for errors
2. Verify backend logs
3. Test API endpoints directly (curl/Postman)
4. Review Phase 3 documentation
5. Check feature flag is enabled

---

**Created:** March 3, 2026  
**Version:** 1.0  
**Component Files:**
- `frontend/src/components/PolicyUpdatesPage.jsx`
- `frontend/src/components/PolicyUpdatesPage.css`
- `frontend/src/App.jsx` (modified)
- `frontend/src/components/Sidebar.jsx` (modified)
- `frontend/src/api/client.js` (modified)

**Ready to use!** 🚀
