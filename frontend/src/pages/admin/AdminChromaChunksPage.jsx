import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import './AdminChromaChunksPage.css';

const PAGE_SIZE = 25;

function formatConnection(connection) {
  if (!connection) return 'Unavailable';
  if (connection.mode === 'http') {
    return connection.url || `${connection.host}:${connection.port}`;
  }
  return connection.persist_directory || 'Local persistent store';
}

function formatMetadata(metadata) {
  if (!metadata || Object.keys(metadata).length === 0) {
    return 'No metadata';
  }
  return JSON.stringify(metadata, null, 2);
}

function AdminChromaChunksPage({ user, onToggleSidebar, showToast }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [chunks, setChunks] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [collectionName, setCollectionName] = useState('');
  const [connectionInfo, setConnectionInfo] = useState(null);
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [ticketInput, setTicketInput] = useState('');
  const [ticketFilter, setTicketFilter] = useState('');
  const [policyUpdatesOnly, setPolicyUpdatesOnly] = useState(false);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/');
      return;
    }
    loadChunks(0, {
      search: '',
      status: 'all',
      type: 'all',
      ticketId: '',
      policyUpdatesOnly: false,
    });
  }, [user, navigate]);

  const loadChunks = async (
    nextOffset = offset,
    nextFilters = {
      search: searchQuery,
      status: statusFilter,
      type: typeFilter,
      ticketId: ticketFilter,
      policyUpdatesOnly,
    }
  ) => {
    try {
      setLoading(true);
      const data = await api.getAdminChromaChunks({
        limit: PAGE_SIZE,
        offset: nextOffset,
        ...(nextFilters.search ? { search: nextFilters.search } : {}),
        ...(nextFilters.status && nextFilters.status !== 'all' ? { status: nextFilters.status } : {}),
        ...(nextFilters.type && nextFilters.type !== 'all' ? { chunk_type: nextFilters.type } : {}),
        ...(nextFilters.ticketId ? { ticket_id: nextFilters.ticketId } : {}),
        ...(nextFilters.policyUpdatesOnly ? { policy_updates_only: true } : {}),
      });
      setChunks(data.chunks || []);
      setTotalChunks(data.total_chunks || 0);
      setCollectionName(data.collection_name || '');
      setConnectionInfo(data.connection || null);
      setOffset(data.offset || 0);
    } catch (error) {
      if (showToast) showToast(error.message || 'Failed to load Chroma chunks', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadChunks(offset);
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    const nextQuery = searchInput.trim();
    const nextTicket = ticketInput.trim();
    setSearchQuery(nextQuery);
    setTicketFilter(nextTicket);
    setOffset(0);
    loadChunks(0, {
      search: nextQuery,
      status: statusFilter,
      type: typeFilter,
      ticketId: nextTicket,
      policyUpdatesOnly,
    });
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setSearchQuery('');
    setStatusFilter('all');
    setTypeFilter('all');
    setTicketInput('');
    setTicketFilter('');
    setPolicyUpdatesOnly(false);
    setOffset(0);
    loadChunks(0, {
      search: '',
      status: 'all',
      type: 'all',
      ticketId: '',
      policyUpdatesOnly: false,
    });
  };

  const hasPrev = offset > 0;
  const hasNext = offset + chunks.length < totalChunks;
  const visibleRange = useMemo(() => {
    if (totalChunks === 0) {
      return '0 of 0';
    }
    const start = offset + 1;
    const end = offset + chunks.length;
    return `${start}-${end} of ${totalChunks}`;
  }, [offset, chunks.length, totalChunks]);

  return (
    <div className="admin-chroma-page">
      <div className="admin-chroma-header">
        <button className="mobile-menu-btn" onClick={onToggleSidebar}>
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <div className="admin-chroma-copy">
          <h1>Chroma Vault</h1>
          <p>Private admin view of the currently active knowledge chunks.</p>
        </div>
        <button className="refresh-chroma-btn" onClick={handleRefresh}>
          Refresh
        </button>
      </div>

      <div className="admin-chroma-content">
        <div className="chroma-overview">
          <div className="overview-card">
            <span className="label">Collection</span>
            <span className="value">{collectionName || 'academic_docs'}</span>
          </div>
          <div className="overview-card">
            <span className="label">Connection</span>
            <span className="value compact">{formatConnection(connectionInfo)}</span>
          </div>
          <div className="overview-card">
            <span className="label">Visible Range</span>
            <span className="value">{visibleRange}</span>
          </div>
        </div>

        <form className="chroma-toolbar" onSubmit={handleSearchSubmit}>
          <input
            type="text"
            className="chroma-search"
            placeholder="Search chunk text or metadata"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
          <select
            className="chroma-select"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="deprecated">Deprecated</option>
          </select>
          <select
            className="chroma-select"
            value={typeFilter}
            onChange={(event) => setTypeFilter(event.target.value)}
          >
            <option value="all">All types</option>
            <option value="policy_update">Policy updates</option>
            <option value="canonical_knowledge">Canonical knowledge</option>
          </select>
          <input
            type="text"
            className="chroma-ticket"
            placeholder="Ticket ID"
            value={ticketInput}
            onChange={(event) => setTicketInput(event.target.value)}
          />
          <label className="policy-toggle">
            <input
              type="checkbox"
              checked={policyUpdatesOnly}
              onChange={(event) => setPolicyUpdatesOnly(event.target.checked)}
            />
            <span>Only updated policy chunks</span>
          </label>
          <button type="submit" className="toolbar-btn primary">Search</button>
          <button type="button" className="toolbar-btn" onClick={handleClearSearch}>Clear</button>
        </form>

        <div className="chroma-pagination">
          <span className="pagination-text">
            {searchQuery ? `Filtered by "${searchQuery}"` : 'Showing current Chroma collection'}
          </span>
          <div className="pagination-actions">
            <button
              className="toolbar-btn"
              type="button"
              disabled={!hasPrev || loading}
              onClick={() => loadChunks(Math.max(offset - PAGE_SIZE, 0))}
            >
              Previous
            </button>
            <button
              className="toolbar-btn"
              type="button"
              disabled={!hasNext || loading}
              onClick={() => loadChunks(offset + PAGE_SIZE)}
            >
              Next
            </button>
          </div>
        </div>

        {loading ? (
          <div className="chroma-loading">Loading chunks...</div>
        ) : chunks.length === 0 ? (
          <div className="chroma-empty">
            <h3>No chunks found</h3>
            <p>Try a different search term or refresh the collection.</p>
          </div>
        ) : (
          <div className="chunk-list">
            {chunks.map((chunk) => (
              <article className="chunk-card" key={chunk.id}>
                <div className="chunk-card-top">
                  <div>
                    <span className="chunk-chip">{chunk.status || 'active'}</span>
                    {chunk.metadata?.type && <span className="chunk-type">{chunk.metadata.type}</span>}
                    {chunk.source && <span className="chunk-source">{chunk.source}</span>}
                    {chunk.metadata?.ticket_id && <span className="chunk-ticket">{chunk.metadata.ticket_id}</span>}
                  </div>
                  <code className="chunk-id">{chunk.id}</code>
                </div>

                <div className="chunk-grid">
                  <div className="chunk-main">
                    <p className="chunk-preview">{chunk.document}</p>
                  </div>
                  <div className="chunk-side">
                    <div className="chunk-side-item">
                      <span className="side-label">Policy Area</span>
                      <span className="side-value">{chunk.metadata?.policy_area || chunk.metadata?.section || 'N/A'}</span>
                    </div>
                    <div className="chunk-side-item">
                      <span className="side-label">Version</span>
                      <span className="side-value">{chunk.metadata?.version ?? 'N/A'}</span>
                    </div>
                    <div className="chunk-side-item">
                      <span className="side-label">Updated</span>
                      <span className="side-value">{chunk.metadata?.updated_at || chunk.metadata?.created_at || chunk.metadata?.deprecated_at || 'N/A'}</span>
                    </div>
                    <div className="chunk-side-item">
                      <span className="side-label">Replaces</span>
                      <span className="side-value">{chunk.metadata?.replaces || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                <details className="chunk-metadata">
                  <summary>Metadata</summary>
                  <pre>{formatMetadata(chunk.metadata)}</pre>
                </details>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminChromaChunksPage;
