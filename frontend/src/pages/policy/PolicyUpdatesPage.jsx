import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../../api/client';
import ChunkSelectionPanel from '../../components/chunk-editor/ChunkSelectionPanel';
import './PolicyUpdatesPage.css';

const PolicyUpdatesPage = ({ isSidebarOpen, onToggleSidebar, showToast, user }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [view, setView] = useState('dashboard'); // 'dashboard' or 'all-tickets'
  const [tickets, setTickets] = useState([]);
  const [allTickets, setAllTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showRejectionModal, setShowRejectionModal] = useState(false);
  const [showTicketDetail, setShowTicketDetail] = useState(false);
  const [approvalForm, setApprovalForm] = useState({ notes: '', policyText: '' });
  const [rejectionReason, setRejectionReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAudit, setShowAudit] = useState(false);
  
  // Proof viewer state
  const [showProofViewer, setShowProofViewer] = useState(false);
  const [currentProofs, setCurrentProofs] = useState([]);
  const [currentProofIndex, setCurrentProofIndex] = useState(0);

  // Deprecation workflow state
  const [deprecationMode, setDeprecationMode] = useState(true);
  const [affectedChunksData, setAffectedChunksData] = useState(null);
  const [selectedChunkIds, setSelectedChunkIds] = useState([]);
  const [editedChunks, setEditedChunks] = useState({}); // Track individual chunk edits {chunkId: newText}
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [deprecationStep, setDeprecationStep] = useState('review'); // 'review' | 'chunks' | 'confirm'

  useEffect(() => {
    // Check if user is authenticated
    if (!user) {
      showToast('Please sign in to access this page', 'error');
      navigate('/');
      return;
    }

    fetchInitialData();
  }, [user, navigate]);

  useEffect(() => {
    if (view === 'all-tickets') {
      fetchAllTickets(filterStatus || null);
    }
  }, [view, filterStatus]);

  const fetchInitialData = async () => {
    setLoading(true);
    await Promise.all([
      fetchTickets('pending'),
      fetchStats()
    ]);
    setLoading(false);
    
    // Reset scroll position after content is loaded
    setTimeout(() => {
      const dashboardContent = document.querySelector('.dashboard-content');
      if (dashboardContent) {
        dashboardContent.scrollTop = 0;
      }
    }, 0);
  };

  const fetchTickets = async (status = null) => {
    try {
      const data = await api.getPolicyUpdateTickets(status);
      setTickets(data.tickets || []);
    } catch (error) {
      showToast('Failed to load tickets: ' + error.message, 'error');
    }
  };

  const fetchAllTickets = async (status = null) => {
    try {
      const data = await api.getPolicyUpdateTickets(status);
      setAllTickets(data.tickets || []);
    } catch (error) {
      showToast('Failed to load all tickets: ' + error.message, 'error');
    }
  };

  const fetchStats = async () => {
    try {
      const data = await api.getPolicyUpdateStats();
      setStats(data);
    } catch (error) {
      showToast('Failed to load statistics: ' + error.message, 'error');
    }
  };

  const fetchAuditLog = async () => {
    try {
      const data = await api.getPolicyAuditLog();
      setAuditLog(data.audit_records || []);
    } catch (error) {
      showToast('Failed to load audit log: ' + error.message, 'error');
    }
  };

  const openTicketDetail = (ticket) => {
    setSelectedTicket(ticket);
    setShowTicketDetail(true);
  };

  const openApprovalModal = async (ticket) => {
    // First approve the ticket, then navigate to deprecation workflow
    setIsSubmitting(true);
    try {
      await api.approvePolicyUpdate(ticket.ticket_id, {
        reviewer_notes: 'Approved for policy deprecation workflow'
      });
      
      showToast('Ticket approved successfully', 'success');
      
      // Refresh tickets list
      fetchTickets('pending');
      fetchStats();
      
      // Move directly into the in-app deprecation workflow after approval succeeds
      navigate(`/policy-updates/${ticket.ticket_id}/deprecate`);
    } catch (error) {
      showToast('Failed to approve ticket: ' + error.message, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openRejectionModal = (ticket) => {
    setSelectedTicket(ticket);
    setRejectionReason('');
    setShowRejectionModal(true);
  };

  const openProofViewer = (proofs, startIndex = 0) => {
    setCurrentProofs(proofs);
    setCurrentProofIndex(startIndex);
    setShowProofViewer(true);
  };

  const nextProof = () => {
    if (currentProofIndex < currentProofs.length - 1) {
      setCurrentProofIndex(currentProofIndex + 1);
    }
  };

  const previousProof = () => {
    if (currentProofIndex > 0) {
      setCurrentProofIndex(currentProofIndex - 1);
    }
  };

  const getFileType = (url) => {
    if (url.match(/\.(png|jpg|jpeg|gif|webp|svg)$/i)) return 'image';
    if (url.match(/\.pdf$/i)) return 'pdf';
    if (url.match(/\.(txt|md)$/i)) return 'text';
    return 'other';
  };

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      showToast('Please provide a rejection reason', 'error');
      return;
    }

    if (rejectionReason.trim().length < 10) {
      showToast('Rejection reason must be at least 10 characters', 'error');
      return;
    }

    if (rejectionReason.trim().length > 500) {
      showToast('Rejection reason must be less than 500 characters', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.rejectPolicyUpdate(selectedTicket.ticket_id, {
        reason: rejectionReason.trim(),
        reviewer_notes: rejectionReason.trim()
      });

      showToast('Policy update rejected', 'success');
      setShowRejectionModal(false);
      setSelectedTicket(null);
      fetchTickets('pending');
      fetchStats();
    } catch (error) {
      showToast('Failed to reject: ' + error.message, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Deprecation workflow handlers
  const handleFindAffectedChunks = async () => {
    if (!selectedTicket) return;

    setLoadingChunks(true);
    try {
      const result = await api.findAffectedChunks(selectedTicket.ticket_id);
      setAffectedChunksData(result);
      
      // Pre-select high confidence chunks
      const highConfIds = result.high_confidence_chunks?.map(c => c.id) || [];
      setSelectedChunkIds(highConfIds);
      
      setDeprecationStep('chunks');
      showToast(`Found ${result.total_found} related chunks`, 'success');
    } catch (error) {
      showToast('Failed to find affected chunks: ' + error.message, 'error');
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleProceedToEdit = () => {
    if (selectedChunkIds.length === 0) {
      showToast('Please select at least one chunk to edit', 'warning');
      return;
    }

    // Get the full chunk objects for selected IDs
    const selectedChunkObjects = getSelectedChunks();
    
    // Navigate to the chunk editor page
    navigate('/policy-updates/edit-chunks', {
      state: {
        ticket: selectedTicket,
        selectedChunks: selectedChunkObjects,
        allChunks: {
          highConfidence: affectedChunksData?.high_confidence_chunks || [],
          possiblyRelated: affectedChunksData?.possibly_related_chunks || []
        }
      }
    });
  };

  const handleApplyDeprecationWithData = async (ticket, chunks, chunkIds) => {
    if (!ticket || chunkIds.length === 0) {
      showToast('Invalid data for deprecation', 'error');
      return;
    }

    // Check if any chunks were edited
    const hasEdits = Object.keys(chunks).length > 0;
    if (!hasEdits) {
      showToast('No chunks were edited', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      // Prepare individual chunk updates
      const chunkUpdates = chunkIds.map(chunkId => ({
        chunk_id: chunkId,
        new_text: chunks[chunkId]
      })).filter(update => update.new_text); // Only include edited chunks

      const result = await api.applyPolicyDeprecation(ticket.ticket_id, {
        chunk_updates: chunkUpdates,
        policy_area: 'Policy Update',
        deprecation_reason: approvalForm.notes.trim() || 'Policy updated via chunk editor'
      });

      showToast(
        `Success! Deprecated ${result.deprecated_count} chunks, created ${result.created_count} new chunks`,
        'success'
      );
      
      // Reset state
      setSelectedTicket(null);
      setAffectedChunksData(null);
      setSelectedChunkIds([]);
      setEditedChunks({});
      setDeprecationStep('review');
      setShowApprovalModal(false);
      
      fetchTickets('pending');
      fetchStats();
    } catch (error) {
      showToast('Failed to apply deprecation: ' + error.message, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApplyDeprecation = async () => {
    if (!selectedTicket || selectedChunkIds.length === 0) {
      showToast('Please select at least one chunk to deprecate', 'error');
      return;
    }

    // Check if any chunks were edited
    const hasEdits = Object.keys(editedChunks).length > 0;
    if (!hasEdits) {
      showToast('Please edit at least one chunk before applying', 'error');
      return;
    }

    // Validate edited chunks
    for (const [chunkId, text] of Object.entries(editedChunks)) {
      if (!text.trim() || text.trim().length < 20) {
        showToast(`Chunk ${chunkId} must have at least 20 characters`, 'error');
        return;
      }
    }

    setIsSubmitting(true);
    try {
      // Prepare individual chunk updates
      const chunkUpdates = selectedChunkIds.map(chunkId => ({
        chunk_id: chunkId,
        new_text: editedChunks[chunkId] || getOriginalChunkText(chunkId)
      }));

      const result = await api.applyPolicyDeprecation(selectedTicket.ticket_id, {
        chunk_updates: chunkUpdates,
        policy_area: affectedChunksData?.policy_area || 'Policy Update',
        deprecation_reason: approvalForm.notes.trim() || 'Policy updated by admin'
      });

      showToast(
        `Success! Deprecated ${result.deprecated_count} chunks, created ${result.created_count} new chunks`,
        'success'
      );
      
      setShowApprovalModal(false);
      setSelectedTicket(null);
      setAffectedChunksData(null);
      setSelectedChunkIds([]);
      setEditedChunks({});
      setDeprecationStep('review');
      setApprovalForm({ notes: '', policyText: '' });
      
      fetchTickets('pending');
      fetchStats();
    } catch (error) {
      showToast('Failed to apply deprecation: ' + error.message, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelDeprecation = () => {
    setShowApprovalModal(false);
    setSelectedTicket(null);
    setAffectedChunksData(null);
    setSelectedChunkIds([]);
    setEditedChunks({});
    setDeprecationStep('review');
  };

  // Helper to get original chunk text from affectedChunksData
  const getOriginalChunkText = (chunkId) => {
    const allChunks = [
      ...(affectedChunksData?.high_confidence_chunks || []),
      ...(affectedChunksData?.possibly_related_chunks || [])
    ];
    const chunk = allChunks.find(c => c.id === chunkId);
    return chunk?.text || '';
  };

  // Get selected chunks with full data
  const getSelectedChunks = () => {
    if (!affectedChunksData) return [];
    const allChunks = [
      ...(affectedChunksData.high_confidence_chunks || []),
      ...(affectedChunksData.possibly_related_chunks || [])
    ];
    return allChunks.filter(chunk => selectedChunkIds.includes(chunk.id));
  };

  const handleChunkEdit = (chunkId, newText) => {
    setEditedChunks(prev => ({
      ...prev,
      [chunkId]: newText
    }));
  };


  const getConfidenceBadgeClass = (level) => {
    const classes = {
      low: 'confidence-badge-low',
      medium: 'confidence-badge-medium',
      high: 'confidence-badge-high'
    };
    return classes[level] || classes.medium;
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      pending: 'status-badge-pending',
      approved: 'status-badge-approved',
      rejected: 'status-badge-rejected',
      implemented: 'status-badge-implemented'
    };
    return classes[status] || 'status-badge-pending';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatStatus = (status) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="policy-updates-page dashboard-layout">
     {/* Header with Search */}
      <div className="dashboard-header">
        <div className="header-left">
          <button className="toggle-sidebar-btn" onClick={onToggleSidebar}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          <div>
            <h1 className="page-title">Policy Updates Dashboard</h1>
          </div>
        </div>
        <div className="header-actions">
          <div className="search-box">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input
              type="text"
              placeholder="Search tickets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        ) : (
          <>
            {/* Quick Stats Overview */}
            {/* {stats && (
              <div className="stats-overview">
                <div className="stat-card compact">
                  <div className="stat-icon-small">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                  </div>
                  <div>
                    <div className="stat-label">Pending</div>
                    <div className="stat-value-large">{stats.by_status?.pending || 0}</div>
                  </div>
                </div>

                <div className="stat-card compact">
                  <div className="stat-icon-small success">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </div>
                  <div>
                    <div className="stat-label">Approved</div>
                    <div className="stat-value-large">{stats.by_status?.approved || 0}</div>
                  </div>
                </div>

                <div className="stat-card compact">
                  <div className="stat-icon-small">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                  </div>
                  <div>
                    <div className="stat-label">Avg Trust Score</div>
                    <div className="stat-value-large">{((stats.avg_trust_score || 0) * 100).toFixed(0)}%</div>
                  </div>
                </div>

                <div className="stat-card compact">
                  <div className="stat-icon-small">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7"></rect>
                      <rect x="14" y="3" width="7" height="7"></rect>
                      <rect x="14" y="14" width="7" height="7"></rect>
                      <rect x="3" y="14" width="7" height="7"></rect>
                    </svg>
                  </div>
                  <div>
                    <div className="stat-label">Chunks Updated</div>
                    <div className="stat-value-large">{stats.total_chunks_deprecated || 0}</div>
                  </div>
                </div>
              </div>
            )} */}

            {/* Pending Reviews Section */}
            <div className="main-section">
              <div className="section-header">
                <h2>Pending Reviews</h2>
                <span className="badge-count">{tickets.length}</span>
              </div>
              
              {tickets.length === 0 ? (
                <div className="empty-state-inline">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  <p>All clear! No pending reviews</p>
                </div>
              ) : (
                <div className="tickets-grid">
                  {tickets.filter(ticket => 
                    !searchQuery || 
                    ticket.claim_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    ticket.ticket_id.toLowerCase().includes(searchQuery.toLowerCase())
                  ).map(ticket => (
                    <div key={ticket.ticket_id} className="ticket-card">
                      <div className="ticket-header">
                        <span className="ticket-id">{ticket.ticket_id}</span>
                        <div className="ticket-badges">
                          <span className={`confidence-badge ${getConfidenceBadgeClass(ticket.confidence_level)}`}>
                            {ticket.confidence_level?.toUpperCase() || 'MEDIUM'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="ticket-body">
                        <h3 className="ticket-claim">{ticket.claim_text}</h3>
                        
                        <div className="ticket-metrics-compact">
                          <div className="metric-inline">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                            </svg>
                            <span>{ticket.trust_score != null ? (ticket.trust_score * 100).toFixed(0) : 'N/A'}%</span>
                          </div>
                          <div className="metric-inline">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <rect x="3" y="3" width="7" height="7"></rect>
                              <rect x="14" y="3" width="7" height="7"></rect>
                              <rect x="14" y="14" width="7" height="7"></rect>
                              <rect x="3" y="14" width="7" height="7"></rect>
                            </svg>
                            <span>{ticket.affected_chunks?.length || 0} chunks</span>
                          </div>
                          {ticket.has_proofs && (
                            <div className="metric-inline proof-indicator">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
                              </svg>
                              <span>{ticket.proof_urls?.length || 0} proofs</span>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="ticket-actions compact">
                        <button className="btn-view" onClick={() => openTicketDetail(ticket)}>
                          View Details
                        </button>
                        <button className="btn-approve" onClick={() => openApprovalModal(ticket)}>
                          Approve
                        </button>
                        <button className="btn-reject" onClick={() => openRejectionModal(ticket)}>
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* All Tickets Section */}
            <div className="section-divider"></div>
            
            <div className="secondary-section">
              <div className={`section-header clickable ${view === 'all-tickets' ? 'expanded' : ''}`} onClick={() => {
                if (view === 'all-tickets') {
                  setView('dashboard');
                } else {
                  setView('all-tickets');
                  if (allTickets.length === 0) {
                    fetchAllTickets(null);
                  }
                }
              }}>
                <h2>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    {view === 'all-tickets' ? (
                      <polyline points="6 9 12 15 18 9"></polyline>
                    ) : (
                      <polyline points="9 18 15 12 9 6"></polyline>
                    )}
                  </svg>
                  All Tickets
                </h2>
                {view !== 'all-tickets' && (
                  <button className="btn-link">View All →</button>
                )}
              </div>

              {view === 'all-tickets' && (
                <div className="section-content expanded">
                  <div className="filter-bar">
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="filter-select-inline"
                    >
                      <option value="">All Status</option>
                      <option value="pending">Pending Review</option>
                      <option value="approved">Approved</option>
                      <option value="rejected">Rejected</option>
                      <option value="implemented">Implemented</option>
                    </select>
                  </div>

                  {allTickets.length === 0 ? (
                    <div className="empty-state-inline">
                      <p>No tickets found</p>
                    </div>
                  ) : (
                    <div className="tickets-table-compact">
                      <table>
                        <thead>
                          <tr>
                            <th>Ticket ID</th>
                            <th>Claim</th>
                            <th>Trust</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>View</th>
                          </tr>
                        </thead>
                        <tbody>
                          {allTickets.map(ticket => (
                            <tr key={ticket.ticket_id}>
                              <td className="ticket-id-cell">{ticket.ticket_id}</td>
                              <td className="claim-cell">{ticket.claim_text}</td>
                              <td>
                                <span className="trust-badge">
                                  {ticket.trust_score != null ? (ticket.trust_score * 100).toFixed(0) : 'N/A'}%
                                </span>
                              </td>
                              <td>
                                <span className={`status-badge ${getStatusBadgeClass(ticket.status)}`}>
                                  {formatStatus(ticket.status)}
                                </span>
                              </td>
                              <td className="date-cell-compact">{formatDate(ticket.created_at)}</td>
                              <td>
                                <button className="btn-icon" onClick={() => openTicketDetail(ticket)}>
                                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                    <circle cx="12" cy="12" r="3"></circle>
                                  </svg>
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Audit Trail Section */}
            {/* <div className="section-divider"></div> */}
            
            {/* <div className="secondary-section">
              <div className={`section-header clickable ${showAudit ? 'expanded' : ''}`} onClick={() => {
                setShowAudit(!showAudit);
                if (!showAudit && auditLog.length === 0) {
                  fetchAuditLog();
                }
              }}>
                <h2>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    {showAudit ? (
                      <polyline points="6 9 12 15 18 9"></polyline>
                    ) : (
                      <polyline points="9 18 15 12 9 6"></polyline>
                    )}
                  </svg>
                  Recent Activity
                </h2>
              </div>

              {showAudit && (
                <div className="section-content expanded">
                  {auditLog.length === 0 ? (
                    <div className="empty-state-inline">
                      <p>No activity recorded</p>
                    </div>
                  ) : (
                    <div className="audit-timeline-compact">
                      {auditLog.slice(0, 5).map((record, index) => (
                        <div key={record.audit_id || index} className="audit-item-compact">
                          <div className="audit-icon">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                          </div>
                          <div className="audit-content-compact">
                            <div className="audit-title">{formatStatus(record.change_type || 'policy_update')}</div>
                            <div className="audit-meta">
                              {record.ticket_id} • {record.performed_by} • {formatDate(record.performed_at)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div> */}
          </>
        )}
      </div>

      {/* Ticket Detail Modal */}
      {showTicketDetail && selectedTicket && (
        <div className="modal-overlay" onClick={() => {
          setShowTicketDetail(false);
          setSelectedTicket(null);
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="ticket-detail-modal">
            <h2>Ticket Details</h2>
            
            <div className="detail-section">
              <h3>Ticket Information</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Ticket ID:</span>
                  <span className="detail-value">{selectedTicket.ticket_id}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Status:</span>
                  <span className={`status-badge ${getStatusBadgeClass(selectedTicket.status)}`}>
                    {formatStatus(selectedTicket.status)}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Reported By:</span>
                  <span className="detail-value">{selectedTicket.user_id || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Reported At:</span>
                  <span className="detail-value">{formatDate(selectedTicket.created_at)}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Trust Score:</span>
                  <span className="detail-value">
                    {selectedTicket.trust_score != null ? `${(selectedTicket.trust_score * 100).toFixed(0)}%` : 'N/A'}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Confidence:</span>
                  <span className={`confidence-badge ${getConfidenceBadgeClass(selectedTicket.confidence_level)}`}>
                    {selectedTicket.confidence_level?.toUpperCase() || 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            <div className="detail-section">
              <h3>User Claim</h3>
              <div className="claim-box">
                {selectedTicket.claim_text}
              </div>
            </div>

            {/* Proof Uploads Display */}
            {selectedTicket.has_proofs && selectedTicket.proof_urls && selectedTicket.proof_urls.length > 0 && (
              <div className="detail-section">
                <h3>📎 Attached Proofs ({selectedTicket.proof_urls.length})</h3>
                <div className="proofs-grid">
                  {selectedTicket.proof_urls.map((url, idx) => {
                    const fileType = getFileType(url);
                    
                    return (
                      <div key={idx} className="proof-item clickable" onClick={() => openProofViewer(selectedTicket.proof_urls, idx)}>
                        {fileType === 'image' ? (
                          <div className="proof-image-wrapper">
                            <img src={url} alt={`Proof ${idx + 1}`} className="proof-image" />
                            <div className="proof-overlay">
                              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                              </svg>
                              <span>View</span>
                            </div>
                          </div>
                        ) : fileType === 'pdf' ? (
                          <div className="proof-pdf">
                            <div className="proof-icon">📄</div>
                            <div className="proof-label">PDF Document {idx + 1}</div>
                            <div className="proof-action">Click to view</div>
                          </div>
                        ) : fileType === 'text' ? (
                          <div className="proof-file">
                            <div className="proof-icon">📝</div>
                            <div className="proof-label">Text Document {idx + 1}</div>
                            <div className="proof-action">Click to view</div>
                          </div>
                        ) : (
                          <div className="proof-file">
                            <div className="proof-icon">📎</div>
                            <div className="proof-label">Document {idx + 1}</div>
                            <div className="proof-action">Click to download</div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {selectedTicket.extracted_fields && Object.keys(selectedTicket.extracted_fields).some(key => 
              selectedTicket.extracted_fields[key] != null && key !== 'specific_claim'
            ) && (
              <div className="detail-section">
                <h3>Evidence Extracted</h3>
                <div className="evidence-grid">
                  {selectedTicket.extracted_fields.circular_number && (
                    <div className="evidence-detail">
                      <span className="evidence-label">Circular Number:</span>
                      <span>{selectedTicket.extracted_fields.circular_number}</span>
                    </div>
                  )}
                  {selectedTicket.extracted_fields.date_mentioned && (
                    <div className="evidence-detail">
                      <span className="evidence-label">Date Mentioned:</span>
                      <span>{selectedTicket.extracted_fields.date_mentioned}</span>
                    </div>
                  )}
                  {selectedTicket.extracted_fields.policy_reference && (
                    <div className="evidence-detail">
                      <span className="evidence-label">Policy Reference:</span>
                      <span>{selectedTicket.extracted_fields.policy_reference}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedTicket.affected_chunks && selectedTicket.affected_chunks.length > 0 && (
              <div className="detail-section">
                <h3>Affected Chunks ({selectedTicket.affected_chunks.length})</h3>
                <div className="chunks-list">
                  {selectedTicket.affected_chunks.slice(0, 5).map((chunk, idx) => (
                    <div key={idx} className="chunk-item">
                      <div className="chunk-header">
                        <span className="chunk-doc">{chunk.doc_id || 'Document'}</span>
                        {chunk.section && <span className="chunk-section">{chunk.section}</span>}
                      </div>
                      <div className="chunk-text">
                        {chunk.current_text?.substring(0, 200) || chunk.text?.substring(0, 200) || 'No text available'}...
                      </div>
                      {chunk.contradiction_score != null && (
                        <div className="chunk-score">
                          Contradiction Score: <span className="score-value">{(chunk.contradiction_score * 100).toFixed(0)}%</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="modal-actions">
              {selectedTicket.status === 'pending' && (
                <>
                  <button
                    className="btn-approve"
                    onClick={() => {
                      setShowTicketDetail(false);
                      openApprovalModal(selectedTicket);
                    }}
                  >
                    Approve
                  </button>
                  <button
                    className="btn-reject"
                    onClick={() => {
                      setShowTicketDetail(false);
                      openRejectionModal(selectedTicket);
                    }}
                  >
                    Reject
                  </button>
                </>
              )}
              {selectedTicket.status === 'approved' && (
                <button
                  className="btn-approve"
                  onClick={() => {
                    setShowTicketDetail(false);
                    setSelectedTicket(null);
                    navigate(`/policy-updates/${selectedTicket.ticket_id}/deprecate`);
                  }}
                >
                  Implement
                </button>
              )}
              <button
                className="btn-secondary"
                onClick={() => {
                  setShowTicketDetail(false);
                  setSelectedTicket(null);
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* Approval Modal */}
      {/* Rejection Modal */}
      {showRejectionModal && selectedTicket && (
        <div className="modal-overlay" onClick={() => {
          setShowRejectionModal(false);
          setSelectedTicket(null);
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="rejection-modal">
            <h2>Reject Policy Update</h2>
            
            <div className="rejection-info">
              <div className="info-item">
                <span className="info-label">Ticket:</span>
                <span>{selectedTicket.ticket_id}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Claim:</span>
                <span>{selectedTicket.claim_text}</span>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="rejection-reason">
                Rejection Reason * 
                <span className="char-count" style={{
                  color: rejectionReason.length < 10 ? '#ef4444' : rejectionReason.length > 500 ? '#ef4444' : '#64748b',
                  fontSize: '0.875rem',
                  marginLeft: '8px'
                }}>
                  ({rejectionReason.length}/500 characters, min 10)
                </span>
              </label>
              <textarea
                id="rejection-reason"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Explain why this policy update is being rejected (minimum 10 characters)"
                rows="5"
                required
                maxLength={500}
              />
              {rejectionReason.length > 0 && rejectionReason.length < 10 && (
                <span style={{ color: '#ef4444', fontSize: '0.875rem', marginTop: '4px', display: 'block' }}>
                  Please enter at least {10 - rejectionReason.length} more character(s)
                </span>
              )}
            </div>

            <div className="modal-actions">
              <button
                className="btn-reject"
                onClick={handleReject}
                disabled={isSubmitting || !rejectionReason.trim() || rejectionReason.trim().length < 10}
              >
                {isSubmitting ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
              <button
                className="btn-secondary"
                onClick={() => {
                  setShowRejectionModal(false);
                  setSelectedTicket(null);
                }}
                disabled={isSubmitting}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* Proof Viewer Modal */}
      {showProofViewer && currentProofs.length > 0 && (
        <div className="modal-overlay proof-viewer-overlay" onClick={() => setShowProofViewer(false)}>
          <div className="modal-content proof-viewer-content" onClick={(e) => e.stopPropagation()}>
            <div className="proof-viewer">
              <div className="proof-viewer-header">
                <h2>Proof {currentProofIndex + 1} of {currentProofs.length}</h2>
                <button
                  className="btn-close"
                  onClick={() => setShowProofViewer(false)}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>

              <div className="proof-viewer-body">
                {(() => {
                  const currentProof = currentProofs[currentProofIndex];
                  const fileType = getFileType(currentProof);

                  if (fileType === 'image') {
                    return (
                      <div className="proof-image-container">
                        <img src={currentProof} alt={`Proof ${currentProofIndex + 1}`} />
                      </div>
                    );
                  } else if (fileType === 'pdf') {
                    return (
                      <div className="proof-pdf-container">
                        <iframe
                          src={currentProof}
                          title={`PDF Proof ${currentProofIndex + 1}`}
                          width="100%"
                          height="100%"
                        />
                      </div>
                    );
                  } else if (fileType === 'text') {
                    return (
                      <div className="proof-text-container">
                        <iframe
                          src={currentProof}
                          title={`Text Proof ${currentProofIndex + 1}`}
                          width="100%"
                          height="100%"
                        />
                      </div>
                    );
                  } else {
                    return (
                      <div className="proof-unsupported">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                          <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                        <p>Preview not available for this file type</p>
                        <a href={currentProof} target="_blank" rel="noopener noreferrer" className="btn-download">
                          Download File
                        </a>
                      </div>
                    );
                  }
                })()}
              </div>

              {currentProofs.length > 1 && (
                <div className="proof-viewer-navigation">
                  <button
                    className="btn-nav"
                    onClick={previousProof}
                    disabled={currentProofIndex === 0}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="15 18 9 12 15 6"></polyline>
                    </svg>
                    Previous
                  </button>
                  <div className="proof-counter">
                    {currentProofIndex + 1} / {currentProofs.length}
                  </div>
                  <button
                    className="btn-nav"
                    onClick={nextProof}
                    disabled={currentProofIndex === currentProofs.length - 1}
                  >
                    Next
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyUpdatesPage;