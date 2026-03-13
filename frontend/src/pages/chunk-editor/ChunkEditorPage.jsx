import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import api from '../../api/client';
import ChunkSelectionPanel from '../../components/chunk-editor/ChunkSelectionPanel';
import IndividualChunkEditor from '../../components/chunk-editor/IndividualChunkEditor';
import Dialog from '../../components/common/Dialog';
import './ChunkEditorPage.css';
import { FaArrowLeft, FaCheckCircle, FaSpinner, FaSearch } from 'react-icons/fa';

/**
 * ChunkEditorPage - Full page for editing policy chunks
 * Receives ticket data and selected chunks through navigation state
 */
const ChunkEditorPage = ({ user, showToast }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { ticketId } = useParams();
    
    // Workflow state
    const [currentStep, setCurrentStep] = useState('search'); // 'search' | 'select' | 'edit'
    const [ticket, setTicket] = useState(location.state?.ticket || null);
    const [affectedChunksData, setAffectedChunksData] = useState(null);
    const [selectedChunkIds, setSelectedChunkIds] = useState([]);
    const [editedChunks, setEditedChunks] = useState({});
    const [deprecationReason, setDeprecationReason] = useState('');
    
    // Loading states
    const [loadingTicket, setLoadingTicket] = useState(!ticket);
    const [loadingChunks, setLoadingChunks] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);

    // Load ticket if not in state (for direct URL access or refresh)
    useEffect(() => {
        if (!ticket && ticketId) {
            loadTicket();
        }
    }, [ticketId]);

    // Try to restore cached progress from sessionStorage
    useEffect(() => {
        if (ticketId) {
            const cached = sessionStorage.getItem(`deprecation_progress_${ticketId}`);
            if (cached) {
                try {
                    const progress = JSON.parse(cached);
                    if (progress.step) setCurrentStep(progress.step);
                    if (progress.affectedChunksData) setAffectedChunksData(progress.affectedChunksData);
                    if (progress.selectedChunkIds) setSelectedChunkIds(progress.selectedChunkIds);
                    if (progress.editedChunks) setEditedChunks(progress.editedChunks);
                    if (progress.deprecationReason) setDeprecationReason(progress.deprecationReason);
                } catch (e) {
                    console.error('Failed to restore progress:', e);
                }
            }
        }
    }, [ticketId]);

    // Cache progress whenever it changes
    useEffect(() => {
        if (ticketId && ticket) {
            const progress = {
                step: currentStep,
                affectedChunksData,
                selectedChunkIds,
                editedChunks,
                deprecationReason
            };
            sessionStorage.setItem(`deprecation_progress_${ticketId}`, JSON.stringify(progress));
        }
    }, [currentStep, affectedChunksData, selectedChunkIds, editedChunks, deprecationReason, ticketId]);

    const loadTicket = async () => {
        setLoadingTicket(true);
        try {
            const data = await api.getPolicyUpdateTickets();
            const foundTicket = data.tickets?.find(t => t.ticket_id === ticketId);
            if (foundTicket) {
                setTicket(foundTicket);
            } else {
                showToast('Ticket not found', 'error');
                navigate('/policy-updates');
            }
        } catch (error) {
            showToast('Failed to load ticket: ' + error.message, 'error');
            navigate('/policy-updates');
        } finally {
            setLoadingTicket(false);
        }
    };

    // Redirect if no user
    if (!user) {
        showToast('Please sign in to access this page', 'error');
        navigate('/policy-updates');
        return null;
    }

    // Show loading state
    if (loadingTicket || !ticket) {
        return (
            <div className="chunk-editor-page">
                <div className="ce-header">
                    <div className="header-left">
                        <button className="ce-btn-back" onClick={() => navigate('/policy-updates')}>
                            <FaArrowLeft /> Back
                        </button>
                    </div>
                </div>
                <div className="editor-page-content loading-state">
                    <FaSpinner className="ce-spinner" />
                    <p>Loading ticket...</p>
                </div>
            </div>
        );
    }

    const handleChunkEdit = (chunkId, newText) => {
        setEditedChunks(prev => ({
            ...prev,
            [chunkId]: newText
        }));
    };

    const handleFindAffectedChunks = async () => {
        setLoadingChunks(true);
        try {
            const result = await api.findAffectedChunks(ticket.ticket_id);
            setAffectedChunksData(result);
            
            // Pre-select high confidence chunks
            const highConfIds = result.high_confidence_chunks?.map(c => c.id) || [];
            setSelectedChunkIds(highConfIds);
            
            setCurrentStep('select');
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
        setCurrentStep('edit');
    };

    const getSelectedChunks = () => {
        if (!affectedChunksData) return [];
        const allChunks = [
            ...(affectedChunksData.high_confidence_chunks || []),
            ...(affectedChunksData.possibly_related_chunks || [])
        ];
        return allChunks.filter(chunk => selectedChunkIds.includes(chunk.id));
    };

    const handleApplyDeprecation = async () => {
        if (Object.keys(editedChunks).length === 0) {
            showToast('Please edit at least one chunk before applying', 'warning');
            return;
        }

        setIsSubmitting(true);
        try {
            // Prepare individual chunk updates
            const chunkUpdates = selectedChunkIds.map(chunkId => ({
                chunk_id: chunkId,
                new_text: editedChunks[chunkId]
            })).filter(update => update.new_text); // Only include edited chunks

            const result = await api.applyPolicyDeprecation(ticket.ticket_id, {
                chunk_updates: chunkUpdates,
                policy_area: affectedChunksData?.policy_area || 'Policy Update',
                deprecation_reason: deprecationReason.trim() || 'Policy updated via deprecation workflow'
            });

            showToast(
                `Success! Deprecated ${result.deprecated_count} chunks, created ${result.created_count} new chunks`,
                'success'
            );
            
            // Clear cache
            sessionStorage.removeItem(`deprecation_progress_${ticketId}`);
            
            // Navigate back
            navigate('/policy-updates');
        } catch (error) {
            showToast('Failed to apply deprecation: ' + error.message, 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleCancel = () => {
        if (Object.keys(editedChunks).length > 0 || selectedChunkIds.length > 0) {
            setShowLeaveConfirm(true);
            return;
        }
        // Clear cache
        sessionStorage.removeItem(`deprecation_progress_${ticketId}`);
        navigate('/policy-updates');
    };

    const handleConfirmLeave = () => {
        sessionStorage.removeItem(`deprecation_progress_${ticketId}`);
        setShowLeaveConfirm(false);
        navigate('/policy-updates');
    };

    // Render workflow steps
    const renderSearchStep = () => (
        <div className="ce-workflow-step ce-search-step">
            <div className="ce-step-content">
                <h3>Policy Deprecation Workflow</h3>
                <p className="ce-step-description">
                    Let's find all knowledge base chunks related to this policy claim and update them.
                </p>

                <div className="ce-form-group">
                    <label htmlFor="deprecation-reason">Deprecation Reason</label>
                    <textarea
                        id="deprecation-reason"
                        value={deprecationReason}
                        onChange={(e) => setDeprecationReason(e.target.value)}
                        placeholder="Why is this policy being updated? (e.g., 'Updated per Circular 2026/03')..."
                        rows="3"
                    />
                </div>

                <div className="ce-action-banner">
                    <p>Click below to use semantic search to find all chunks related to this policy claim.</p>
                    <button
                        type="button"
                        className="ce-btn-primary ce-btn-large"
                        onClick={handleFindAffectedChunks}
                        disabled={loadingChunks}
                    >
                        {loadingChunks ? (
                            <>
                                <FaSpinner className="ce-spinner" /> Searching...
                            </>
                        ) : (
                            <>
                                <FaSearch /> Find Affected Chunks
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );

    const renderSelectStep = () => (
        <div className="ce-workflow-step ce-select-step">
            <div className="ce-step-header">
                <h3>Select Chunks to Update</h3>
                <p>Review and select the chunks that need to be updated. High-confidence matches are pre-selected.</p>
            </div>

            <ChunkSelectionPanel
                highConfidenceChunks={affectedChunksData?.high_confidence_chunks || []}
                possiblyRelatedChunks={affectedChunksData?.possibly_related_chunks || []}
                selectedChunkIds={selectedChunkIds}
                onSelectionChange={setSelectedChunkIds}
                loading={loadingChunks}
            />

            <div className="ce-step-actions">
                <button
                    className="ce-btn-secondary"
                    onClick={() => setCurrentStep('search')}
                >
                    ← Back to Search
                </button>
                <button
                    className="ce-btn-primary"
                    onClick={handleProceedToEdit}
                    disabled={selectedChunkIds.length === 0}
                >
                    Proceed to Edit ({selectedChunkIds.length} chunks) →
                </button>
            </div>
        </div>
    );

    const renderEditStep = () => (
        <div className="ce-workflow-step ce-edit-step">
            <IndividualChunkEditor
                selectedChunks={getSelectedChunks()}
                userClaim={ticket.claim_text}
                onChange={handleChunkEdit}
                onChangeSelection={() => setCurrentStep('select')}
            />

            <div className="ce-step-actions ce-fixed-bottom">
                <button
                    className="ce-btn-secondary"
                    onClick={() => setCurrentStep('select')}
                    disabled={isSubmitting}
                >
                    ← Back to Selection
                </button>
                <button
                    className="ce-btn-primary"
                    onClick={handleApplyDeprecation}
                    disabled={isSubmitting || Object.keys(editedChunks).length === 0}
                >
                    {isSubmitting ? (
                        <>
                            <FaSpinner className="ce-spinner" /> Applying...
                        </>
                    ) : (
                        <>
                            <FaCheckCircle /> Apply Deprecation ({Object.keys(editedChunks).length} edited)
                        </>
                    )}
                </button>
            </div>
        </div>
    );

    return (
        <div className="chunk-editor-page">
            {/* Top Navigation Bar */}
            <div className="ce-header">
                <div className="ce-header-left">
                    <button className="ce-btn-back" onClick={handleCancel} title="Back to Policy Updates">
                        <FaArrowLeft /> Back
                    </button>
                    
                    <div className="ce-divider"></div>
                    
                    <div className="ce-ticket-info">
                        <span className="ce-ticket-label">Ticket:</span>
                        <span className="ce-ticket-id">{ticket.ticket_id}</span>
                        <span className="ce-ticket-separator">•</span>
                        <span className="ce-ticket-claim">{ticket.claim_text}</span>
                    </div>
                </div>

                <div className="ce-header-right">
                    <div className="ce-workflow-progress">
                        <div className={`ce-step ${currentStep === 'search' ? 'active' : 'completed'}`}>
                            <div className="ce-step-number">1</div>
                            <div className="ce-step-label">Search</div>
                        </div>
                        <div className={`ce-step ${currentStep === 'select' ? 'active' : currentStep === 'edit' ? 'completed' : ''}`}>
                            <div className="ce-step-number">2</div>
                            <div className="ce-step-label">Select</div>
                        </div>
                        <div className={`ce-step ${currentStep === 'edit' ? 'active' : ''}`}>
                            <div className="ce-step-number">3</div>
                            <div className="ce-step-label">Edit</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="ce-content">
                {currentStep === 'search' && renderSearchStep()}
                {currentStep === 'select' && renderSelectStep()}
                {currentStep === 'edit' && renderEditStep()}
            </div>

            <Dialog
                isOpen={showLeaveConfirm}
                onClose={() => setShowLeaveConfirm(false)}
                onConfirm={handleConfirmLeave}
                title="Leave without saving?"
                message="You have unsaved progress. Leaving now will discard selected and edited chunks."
                confirmText="Leave"
                cancelText="Stay"
                type="danger"
            />
        </div>
    );
};

export default ChunkEditorPage;
