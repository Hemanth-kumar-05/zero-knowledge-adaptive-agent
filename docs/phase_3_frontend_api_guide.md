# Phase 3 Frontend API Reference

Quick reference guide for implementing the Policy Updates admin dashboard.

---

## 🔐 Authentication

All endpoints require JWT authentication:

```javascript
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json'
};
```

---

## 📋 API Endpoints

### 1. List Policy Update Tickets

**Endpoint**: `GET /api/policy-updates/tickets`

**Query Parameters**:
- `status` (optional): `pending_review` | `approved` | `rejected` | `implemented`
- `limit` (optional): Number of tickets to return (default: 50)
- `skip` (optional): Number of tickets to skip (for pagination)

**Request**:
```javascript
const response = await fetch(
  '/api/policy-updates/tickets?status=pending_review&limit=10',
  { headers }
);
const data = await response.json();
```

**Response**:
```json
{
  "tickets": [
    {
      "ticket_id": "PT-20250303-A1B2C3D4",
      "claim_text": "Exam registration deadline changed to 15 days",
      "reported_by": "user_123",
      "reported_at": "2025-03-03T10:30:00",
      "status": "pending_review",
      "trust_score": 0.78,
      "confidence_level": "high",
      "affected_chunks_count": 3,
      "evidence": {
        "circular_number": "NCIE/2025/123",
        "date_mentioned": "2025-02-28",
        "policy_reference": "Exam Registration Policy"
      },
      "metadata": {
        "claim_detected": {
          "claim_type": "policy_change",
          "confidence": 0.82,
          "reasoning": "User mentions deadline change with specific numbers"
        },
        "contradiction_analysis": {
          "has_contradiction": true,
          "avg_contradiction_score": 0.85,
          "affected_chunks": [
            {
              "doc_id": "ncie_exam_registration",
              "section": "Registration Timeline",
              "contradiction_score": 0.92,
              "text": "Students must register 12 days before..."
            }
          ]
        }
      }
    }
  ],
  "total": 15,
  "limit": 10,
  "skip": 0
}
```

---

### 2. Get Single Ticket Details

**Endpoint**: `GET /api/policy-updates/tickets/{ticket_id}`

**Request**:
```javascript
const ticket = await fetch(
  '/api/policy-updates/tickets/PT-20250303-A1B2C3D4',
  { headers }
).then(r => r.json());
```

**Response**: Same as single ticket object from list endpoint

---

### 3. Approve Policy Update

**Endpoint**: `POST /api/policy-updates/tickets/{ticket_id}/approve`

**Request Body**:
```json
{
  "reviewer_notes": "Verified via official circular NCIE/2025/123",
  "new_policy_text": "Students must register for examinations at least 15 days before the exam date. Late registrations may incur additional fees."
}
```

**Request**:
```javascript
const result = await fetch(
  '/api/policy-updates/tickets/PT-20250303-A1B2C3D4/approve',
  {
    method: 'POST',
    headers,
    body: JSON.stringify({
      reviewer_notes: "Verified with department",
      new_policy_text: "Updated policy content..."
    })
  }
).then(r => r.json());
```

**Response**:
```json
{
  "success": true,
  "ticket_id": "PT-20250303-A1B2C3D4",
  "message": "Policy update approved and queued for execution",
  "execution_result": {
    "success": true,
    "audit_id": "audit_123",
    "new_version": 2,
    "deprecated_chunks": 3,
    "new_chunks": 4,
    "execution_time_ms": 1250
  }
}
```

---

### 4. Reject Policy Update

**Endpoint**: `POST /api/policy-updates/tickets/{ticket_id}/reject`

**Request Body**:
```json
{
  "rejection_reason": "Insufficient evidence. Requires official circular for verification."
}
```

**Request**:
```javascript
await fetch(
  '/api/policy-updates/tickets/PT-20250303-A1B2C3D4/reject',
  {
    method: 'POST',
    headers,
    body: JSON.stringify({
      rejection_reason: "Needs more documentation"
    })
  }
);
```

**Response**:
```json
{
  "success": true,
  "ticket_id": "PT-20250303-A1B2C3D4",
  "message": "Policy update rejected"
}
```

---

### 5. Get Audit Trail

**Endpoint**: `GET /api/policy-updates/audit`

**Query Parameters**:
- `limit` (optional): Number of records (default: 50)
- `skip` (optional): Pagination offset

**Request**:
```javascript
const auditLog = await fetch(
  '/api/policy-updates/audit?limit=20',
  { headers }
).then(r => r.json());
```

**Response**:
```json
{
  "audit_records": [
    {
      "audit_id": "audit_123",
      "ticket_id": "PT-20250303-A1B2C3D4",
      "change_type": "policy_update",
      "performed_by": "admin_user",
      "performed_at": "2025-03-03T11:00:00",
      "old_version": 1,
      "new_version": 2,
      "affected_chunks": ["chunk_1", "chunk_2", "chunk_3"],
      "new_chunks": ["chunk_4", "chunk_5", "chunk_6", "chunk_7"],
      "rollback_available": true,
      "verified": true
    }
  ],
  "total": 45,
  "limit": 20,
  "skip": 0
}
```

---

### 6. Get Statistics

**Endpoint**: `GET /api/policy-updates/stats`

**Request**:
```javascript
const stats = await fetch(
  '/api/policy-updates/stats',
  { headers }
).then(r => r.json());
```

**Response**:
```json
{
  "total_tickets": 45,
  "by_status": {
    "pending_review": 8,
    "approved": 12,
    "rejected": 5,
    "implemented": 20
  },
  "avg_trust_score": 0.72,
  "trust_score_distribution": {
    "low": 10,
    "medium": 20,
    "high": 15
  },
  "approval_rate": 0.71,
  "avg_processing_time_hours": 2.5,
  "total_chunks_deprecated": 156,
  "total_chunks_created": 189
}
```

---

## 🎨 UI Component Examples

### Ticket Card Component

```jsx
function TicketCard({ ticket }) {
  const getConfidenceBadge = (level) => {
    const colors = {
      low: 'bg-yellow-100 text-yellow-800',
      medium: 'bg-blue-100 text-blue-800',
      high: 'bg-green-100 text-green-800'
    };
    return colors[level] || colors.medium;
  };

  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-lg">{ticket.ticket_id}</h3>
          <p className="text-gray-600 mt-1">{ticket.claim_text}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm ${getConfidenceBadge(ticket.confidence_level)}`}>
          {ticket.confidence_level.toUpperCase()}
        </span>
      </div>
      
      <div className="mt-3 flex gap-4 text-sm text-gray-500">
        <span>Trust: {(ticket.trust_score * 100).toFixed(0)}%</span>
        <span>Affected: {ticket.affected_chunks_count} chunks</span>
        <span>{new Date(ticket.reported_at).toLocaleDateString()}</span>
      </div>
      
      {ticket.evidence.circular_number && (
        <div className="mt-2 text-sm">
          <span className="font-medium">Evidence:</span> {ticket.evidence.circular_number}
        </div>
      )}
    </div>
  );
}
```

### Approval Modal Component

```jsx
function ApprovalModal({ ticket, onClose, onApprove }) {
  const [notes, setNotes] = useState('');
  const [policyText, setPolicyText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    setLoading(true);
    try {
      await onApprove(ticket.ticket_id, {
        reviewer_notes: notes,
        new_policy_text: policyText
      });
      onClose();
    } catch (error) {
      alert('Error approving ticket: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4">Approve Policy Update</h2>
        
        <div className="mb-4">
          <h3 className="font-semibold mb-2">User Claim</h3>
          <p className="bg-gray-50 p-3 rounded">{ticket.claim_text}</p>
        </div>
        
        <div className="mb-4">
          <h3 className="font-semibold mb-2">Affected Chunks ({ticket.affected_chunks_count})</h3>
          <div className="space-y-2">
            {ticket.metadata.contradiction_analysis.affected_chunks.map((chunk, i) => (
              <div key={i} className="bg-gray-50 p-3 rounded text-sm">
                <div className="font-medium">{chunk.doc_id} - {chunk.section}</div>
                <div className="text-gray-600 mt-1">{chunk.text.substring(0, 100)}...</div>
                <div className="text-red-600 mt-1">
                  Contradiction Score: {(chunk.contradiction_score * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="mb-4">
          <label className="block font-semibold mb-2">Reviewer Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full border rounded p-2"
            rows="3"
            placeholder="Verification details, source references..."
          />
        </div>
        
        <div className="mb-4">
          <label className="block font-semibold mb-2">New Policy Text *</label>
          <textarea
            value={policyText}
            onChange={(e) => setPolicyText(e.target.value)}
            className="w-full border rounded p-2"
            rows="6"
            placeholder="Enter the updated policy text that will replace the deprecated chunks..."
            required
          />
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={handleApprove}
            disabled={loading || !policyText}
            className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700 disabled:bg-gray-300"
          >
            {loading ? 'Approving...' : 'Approve & Execute'}
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-300 text-gray-700 py-2 rounded hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Statistics Dashboard

```jsx
function StatsDashboard({ stats }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-gray-500 text-sm">Total Tickets</h3>
        <p className="text-3xl font-bold mt-2">{stats.total_tickets}</p>
        <div className="mt-3 text-sm">
          <div className="flex justify-between">
            <span>Pending</span>
            <span className="font-medium">{stats.by_status.pending_review}</span>
          </div>
          <div className="flex justify-between">
            <span>Implemented</span>
            <span className="font-medium">{stats.by_status.implemented}</span>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-gray-500 text-sm">Average Trust Score</h3>
        <p className="text-3xl font-bold mt-2">
          {(stats.avg_trust_score * 100).toFixed(0)}%
        </p>
        <div className="mt-3 text-sm text-gray-600">
          Approval Rate: {(stats.approval_rate * 100).toFixed(0)}%
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-gray-500 text-sm">Chunks Updated</h3>
        <p className="text-3xl font-bold mt-2">{stats.total_chunks_deprecated}</p>
        <div className="mt-3 text-sm text-gray-600">
          {stats.total_chunks_created} new chunks created
        </div>
      </div>
    </div>
  );
}
```

---

## 🔄 State Management Example (React Context)

```jsx
import { createContext, useContext, useState } from 'react';

const PolicyUpdatesContext = createContext();

export function PolicyUpdatesProvider({ children }) {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchTickets = async (status = null) => {
    setLoading(true);
    try {
      const url = status 
        ? `/api/policy-updates/tickets?status=${status}`
        : '/api/policy-updates/tickets';
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setTickets(data.tickets);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const approveTicket = async (ticketId, approvalData) => {
    const response = await fetch(
      `/api/policy-updates/tickets/${ticketId}/approve`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(approvalData)
      }
    );
    
    if (!response.ok) throw new Error('Approval failed');
    
    // Refresh tickets after approval
    await fetchTickets();
    return await response.json();
  };

  const rejectTicket = async (ticketId, reason) => {
    const response = await fetch(
      `/api/policy-updates/tickets/${ticketId}/reject`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rejection_reason: reason })
      }
    );
    
    if (!response.ok) throw new Error('Rejection failed');
    
    await fetchTickets();
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/policy-updates/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <PolicyUpdatesContext.Provider value={{
      tickets,
      stats,
      loading,
      fetchTickets,
      approveTicket,
      rejectTicket,
      fetchStats
    }}>
      {children}
    </PolicyUpdatesContext.Provider>
  );
}

export const usePolicyUpdates = () => useContext(PolicyUpdatesContext);
```

---

## 🎯 Recommended Page Structure

```
/admin
  /policy-updates
    - Dashboard (stats overview)
    - Pending Reviews (tickets with status=pending_review)
    - All Tickets (full list with filters)
    - Audit Trail (history of all changes)
```

### Route Configuration (React Router)

```jsx
import { Routes, Route } from 'react-router-dom';

function AdminRoutes() {
  return (
    <Routes>
      <Route path="/admin/policy-updates" element={<PolicyUpdatesDashboard />} />
      <Route path="/admin/policy-updates/pending" element={<PendingReviews />} />
      <Route path="/admin/policy-updates/tickets" element={<AllTickets />} />
      <Route path="/admin/policy-updates/audit" element={<AuditTrail />} />
    </Routes>
  );
}
```

---

## ⚠️ Error Handling

```javascript
async function safeApiCall(apiFunction) {
  try {
    return await apiFunction();
  } catch (error) {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      alert('You do not have permission to perform this action');
    } else {
      console.error('API Error:', error);
      alert('An error occurred. Please try again.');
    }
    throw error;
  }
}
```

---

## 🔔 Real-time Updates (Optional)

If you want live updates when new tickets are created:

```javascript
// Using polling (simple approach)
useEffect(() => {
  const interval = setInterval(() => {
    fetchTickets('pending_review');
  }, 30000); // Poll every 30 seconds
  
  return () => clearInterval(interval);
}, []);

// Or use WebSockets (advanced)
const ws = new WebSocket('ws://localhost:8000/ws/policy-updates');
ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  if (notification.type === 'new_ticket') {
    fetchTickets();
    showToast('New policy update ticket created!');
  }
};
```

---

## 📱 Responsive Design Notes

- Use Tailwind CSS or similar for responsive layouts
- Mobile: Stack cards vertically, show abbreviated info
- Tablet: 2-column grid for ticket cards
- Desktop: 3-column grid with expandable details
- Use modals for approve/reject actions (better UX than inline forms)

---

**Quick Start Checklist**:
- [ ] Set up authentication headers
- [ ] Create API client functions
- [ ] Build ticket list component
- [ ] Build ticket detail/approval modal
- [ ] Add stats dashboard
- [ ] Implement audit trail viewer
- [ ] Test approve/reject workflows
- [ ] Add error handling and loading states

---

**Next**: See [Implementation Summary](./phase_3_implementation_summary.md) for complete backend details.
