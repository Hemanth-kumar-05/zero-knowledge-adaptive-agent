# Policy Updates Frontend - Visual Design Preview

## 🎨 UI Screenshots (Text Description)

Since actual screenshots aren't available yet, here's a detailed visual description of what users will see:

---

## 📱 Main Layout

```
┌────────────────────────────────────────────────────────────────────────┐
│ ☰ Policy Updates Management                                           │
│ Review and manage policy change requests                              │
├────────────────────────────────────────────────────────────────────────┤
│ [🕐 Pending Reviews] [📄 All Tickets] [📊 Statistics] [📜 Audit Trail]│
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [Content Area - Changes based on active tab]                         │
│                                                                        │
│                                                                        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🟠 Tab 1: Pending Reviews

### Layout:
- **3-column grid** of ticket cards
- Each card has rounded corners, subtle border
- Hover effect: Border turns green, slight shadow

### Card Example:
```
┌─────────────────────────────────────────────────────────────┐
│ PT-20250303-A1B2C3D4              [HIGH] [PENDING REVIEW]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ "I heard the exam registration deadline changed            │
│  to 15 days before exams instead of 12 days"               │
│                                                             │
│ Trust Score: 82%    Affected: 3 chunks    Mar 3, 10:30 AM  │
│                                                             │
│ Evidence: 📋 NCIE/2025/123  📅 2025-02-28                  │
│                                                             │
│ [View Details]  [Approve]  [Reject]                        │
└─────────────────────────────────────────────────────────────┘
```

**Color Key:**
- `[HIGH]` badge: Green background, white text
- `[PENDING REVIEW]` badge: Orange background, white text
- Trust Score: Green color if >80%, blue if 60-80%, yellow if <60%
- Actions: Green "Approve", Red "Reject", Gray "View Details"

---

## 📋 Tab 2: All Tickets

### Layout:
- **Filter dropdown** at top: "All Status" selector
- **Full-width table** with 6 columns
- Alternating row hover effects

### Table View:
```
Filter: [All Status ▼]

┌───────────────────┬─────────────────────────┬───────┬──────────────┬──────────────┬─────────┐
│ Ticket ID         │ Claim                   │ Trust │ Status       │ Date         │ Actions │
├───────────────────┼─────────────────────────┼───────┼──────────────┼──────────────┼─────────┤
│ PT-20250303-...   │ Exam deadline change... │ 82%   │ PENDING      │ Mar 3, 10:30 │ [View]  │
│ PT-20250302-...   │ Lab evaluation update...│ 91%   │ IMPLEMENTED  │ Mar 2, 14:20 │ [View]  │
│ PT-20250301-...   │ Grade weightage change..│ 67%   │ APPROVED     │ Mar 1, 09:15 │ [View]  │
│ PT-20250228-...   │ Project deadline...     │ 45%   │ REJECTED     │ Feb 28, 16:45│ [View]  │
└───────────────────┴─────────────────────────┴───────┴──────────────┴──────────────┴─────────┘
```

**Features:**
- Ticket IDs in monospace green font
- Claim text truncated with "..."
- Trust scores color-coded
- Status badges color-coded
- Hover effect on rows (darker background)

---

## 📊 Tab 3: Statistics

### Layout:
- **4 metric cards** in a grid (2x2 on desktop, stacked on mobile)
- **1 distribution chart** below cards

### Metric Cards:
```
┌─────────────────────────┐  ┌─────────────────────────┐
│ 📄 Total Tickets        │  │ ⭐ Avg Trust Score      │
│                         │  │                         │
│       45                │  │       78%               │
│                         │  │                         │
│ Pending: 8              │  │ Approval Rate: 71%      │
│ Implemented: 20         │  │                         │
└─────────────────────────┘  └─────────────────────────┘

┌─────────────────────────┐  ┌─────────────────────────┐
│ 🔲 Chunks Updated       │  │ ⏱️ Avg Processing Time  │
│                         │  │                         │
│       156               │  │       2.5h              │
│                         │  │                         │
│ New: 189                │  │                         │
│                         │  │                         │
└─────────────────────────┘  └─────────────────────────┘
```

### Distribution Chart:
```
Trust Score Distribution
──────────────────────────────────────────────────
Low     ████████████░░░░░░░░░░░░░░░░░░░░░░░░  10
Medium  ████████████████████████████░░░░░░░░  20
High    ████████████████████░░░░░░░░░░░░░░░░  15
```

**Colors:**
- Low bar: Yellow gradient
- Medium bar: Blue gradient
- High bar: Green gradient

---

## 📜 Tab 4: Audit Trail

### Layout:
- **Vertical timeline** with connecting line
- Each item has a dot marker on the timeline
- Cards expand to show details

### Timeline View:
```
    ●───────────────────────────────────────────────────
    │   Policy Update                   Mar 3, 11:00 AM
    │   ───────────────────────────────────────────────
    │   Ticket: PT-20250303-A1B2C3D4
    │   Performed by: admin_user
    │   Version: 1 → 2
    │   Chunks affected: 3 deprecated, 4 created
    │   [Rollback Available]
    │
    ●───────────────────────────────────────────────────
    │   Policy Update                   Mar 2, 14:20 PM
    │   ───────────────────────────────────────────────
    │   Ticket: PT-20250302-B2C3D4E5
    │   Performed by: faculty_user
    │   Version: 2 → 3
    │   Chunks affected: 2 deprecated, 3 created
    │   [Rollback Available]
    │
    ●
```

**Visual Elements:**
- Timeline line: Gray vertical line on left
- Markers: Green circles
- Cards: Dark background, rounded corners
- Rollback badge: Orange with border

---

## 🔍 Modal 1: View Details

### Layout:
- **Centered modal** with overlay
- **Multiple sections** with headers
- **Scrollable content** area

```
┌──────────────────────────────────────────────────────────┐
│ × Ticket Details                                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Ticket Information                                       │
│ ┌────────────────────┬────────────────────────────────┐ │
│ │ Ticket ID:         │ Status:                        │ │
│ │ PT-20250303-...    │ [PENDING REVIEW]               │ │
│ │ Trust Score: 82%   │ Confidence: [HIGH]             │ │
│ └────────────────────┴────────────────────────────────┘ │
│                                                          │
│ User Claim                                               │
│ ┌──────────────────────────────────────────────────────┐│
│ │ "I heard the exam registration deadline changed      ││
│ │  to 15 days before exams instead of 12 days"         ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│ Evidence                                                 │
│ • Circular Number: NCIE/2025/123                        │
│ • Date Mentioned: 2025-02-28                            │
│ • Policy Reference: Exam Registration Policy            │
│                                                          │
│ Affected Chunks (3)                                      │
│ ┌──────────────────────────────────────────────────────┐│
│ │ ncie_exam_registration - Registration Timeline       ││
│ │ "Students must register 12 days before..."           ││
│ │ Contradiction Score: 92%                             ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│              [Approve]  [Reject]  [Close]                │
└──────────────────────────────────────────────────────────┘
```

---

## ✅ Modal 2: Approval Form

### Layout:
- **Form-style modal**
- **Two text areas** (notes and policy text)
- **Character guidance** below policy text

```
┌──────────────────────────────────────────────────────────┐
│ × Approve Policy Update                                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Ticket: PT-20250303-A1B2C3D4                            │
│ Claim: "Exam registration deadline changed to 15 days"  │
│ Affected Chunks: 3                                       │
│                                                          │
│ Reviewer Notes                                           │
│ ┌──────────────────────────────────────────────────────┐│
│ │                                                      ││
│ │                                                      ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│ New Policy Text *                                        │
│ ┌──────────────────────────────────────────────────────┐│
│ │                                                      ││
│ │                                                      ││
│ │                                                      ││
│ │                                                      ││
│ └──────────────────────────────────────────────────────┘│
│ This text will be re-chunked and embedded into system   │
│                                                          │
│              [Approve & Execute]  [Cancel]               │
└──────────────────────────────────────────────────────────┘
```

---

## ❌ Modal 3: Rejection Form

```
┌──────────────────────────────────────────────────────────┐
│ × Reject Policy Update                                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Ticket: PT-20250303-A1B2C3D4                            │
│ Claim: "Exam registration deadline changed to 15 days"  │
│                                                          │
│ Rejection Reason *                                       │
│ ┌──────────────────────────────────────────────────────┐│
│ │                                                      ││
│ │                                                      ││
│ │                                                      ││
│ │                                                      ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│              [Confirm Rejection]  [Cancel]               │
└──────────────────────────────────────────────────────────┘
```

---

## 🌈 Color Palette

### Background Colors:
- **Page Background:** `#212121` (Very dark gray)
- **Card Background:** `#2a2a2a` (Dark gray)
- **Highlighted Background:** `#1a1a1a` (Darker gray)
- **Border Color:** `#3e3e3e` (Medium gray)

### Text Colors:
- **Primary Text:** `#ececec` (Off-white)
- **Secondary Text:** `#b4b4b4` (Light gray)
- **Accent Color:** `#10a37f` (Brand green)

### Badge Colors:
- **High Confidence:** `#4caf50` (Green)
- **Medium Confidence:** `#2196f3` (Blue)
- **Low Confidence:** `#ffc107` (Yellow)
- **Pending Status:** `#ff9800` (Orange)
- **Approved Status:** `#4caf50` (Green)
- **Rejected Status:** `#f44336` (Red)
- **Implemented Status:** `#9c27b0` (Purple)

### Button Colors:
- **Approve:** `#10a37f` (Green)
- **Reject:** `#f44336` (Red)
- **View/Cancel:** `#3e3e3e` (Gray)

---

## 📐 Layout Specifications

### Desktop (> 1024px):
- **Sidebar:** 260px fixed width
- **Content Area:** Remaining width
- **Card Grid:** 3 columns with 20px gap
- **Max Content Width:** 1400px (centered)
- **Padding:** 30px all sides

### Tablet (768px - 1024px):
- **Card Grid:** 2 columns
- **Table:** Horizontal scroll
- **Padding:** 25px

### Mobile (< 768px):
- **Card Grid:** 1 column (stacked)
- **Sidebar:** Overlay on open
- **Padding:** 20px
- **Font Size:** Slightly reduced

---

## 🎭 Interactive States

### Hover Effects:
- **Cards:** Border color changes to green, subtle shadow appears
- **Buttons:** Background darkens by 10%
- **Table Rows:** Background lightens to `#2f2f2f`
- **Tabs:** Background lightens, text color changes

### Active States:
- **Active Tab:** Green bottom border, green text
- **Focused Input:** Green border
- **Selected Dropdown:** Green border

### Loading States:
- **Spinner:** Rotating circle animation (green)
- **Disabled Buttons:** 50% opacity, cursor not-allowed

### Empty States:
- **Large Icon:** 64px, gray, centered
- **Heading:** "No [X] Found"
- **Description:** Helpful message
- **All Centered**

---

## 📱 Mobile View Adjustments

### Changes on Mobile:
1. **Tabs:** Horizontal scroll instead of wrapping
2. **Cards:** Full width, stacked vertically
3. **Table:** Switches to card view or horizontal scroll
4. **Modals:** Full screen on small devices
5. **Sidebar:** Overlay with close button
6. **Stats:** Single column

### Example Mobile Card:
```
┌─────────────────────────────────┐
│ PT-20250303-A1B2C3D4            │
│ [HIGH] [PENDING]                │
├─────────────────────────────────┤
│ Exam deadline changed to 15 days│
│                                 │
│ Trust: 82%                      │
│ Chunks: 3                       │
│ Date: Mar 3                     │
│                                 │
│ Evidence: NCIE/2025/123         │
│                                 │
│ [View] [Approve] [Reject]       │
└─────────────────────────────────┘
```

---

## 🎨 Typography

### Fonts:
- **Headings:** System font stack (Segoe UI, Roboto, Helvetica Neue)
- **Body:** Same as headings
- **Monospace:** Courier New (for ticket IDs)

### Sizes:
- **Page Title:** 24px, bold
- **Section Heading:** 18px, semi-bold
- **Card Title:** 15px, regular
- **Body Text:** 14px, regular
- **Small Text:** 12px, regular
- **Tiny Text:** 11px, regular

### Weights:
- **Headings:** 600 (semi-bold)
- **Body:** 400 (regular)
- **Emphasized:** 500 (medium)
- **Badges:** 600 (semi-bold)

---

## 🔔 Notification System

### Toast Notifications:
```
┌────────────────────────────────────────┐
│ ✅ Policy update approved! 4 chunks    │
│    added                               │
└────────────────────────────────────────┘
```

**Positions:**
- Top-right corner
- 5-second auto-dismiss
- Green for success, red for error
- Slide-in animation

---

## 🎯 Visual Hierarchy

### Primary Elements:
1. Page title (largest, most prominent)
2. Tab navigation (clear separation)
3. Content cards/table (main focus)
4. Action buttons (high contrast)

### Secondary Elements:
- Filters and dropdowns
- Metric labels
- Timestamps
- Help text

### Tertiary Elements:
- Borders and dividers
- Icons
- Badges
- Empty state illustrations

---

## ✨ Animations

### Smooth Transitions:
- **Tab Switch:** Fade in/out (200ms)
- **Hover Effects:** All transitions (200ms ease)
- **Modal Open:** Scale + fade (300ms)
- **Loading Spinner:** Continuous rotation
- **Progress Bars:** Width transition (500ms ease)

### Performance:
- All animations use GPU-accelerated properties
- No layout shifts during animations
- Disabled animations for users with motion preferences

---

## 🖼️ Visual Consistency Checklist

✅ **Colors match main app** (ChatView, Sidebar, etc.)  
✅ **Fonts match main app** (system fonts)  
✅ **Spacing matches main app** (20px, 30px units)  
✅ **Border radius matches** (8px, 12px)  
✅ **Button styles match**  
✅ **Form inputs match**  
✅ **Badges match** (similar to existing tags)  
✅ **Modal overlay matches**  
✅ **Toast notifications match**  
✅ **Icons match** (24-stroke SVGs)  
✅ **Shadows match** (subtle, dark)  

---

**This design perfectly integrates with your existing ChatGPT-style interface!** 🎨

All elements use the same dark theme, green accents, and smooth animations as the rest of your application. Users will feel right at home.
