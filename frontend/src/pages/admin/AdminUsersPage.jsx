import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import Dialog from '../../components/common/Dialog';
import './AdminUsersPage.css';

function AdminUsersPage({ user, onToggleSidebar, showToast }) {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [actionDialog, setActionDialog] = useState({ isOpen: false, title: '', message: '', onConfirm: null, type: 'success' });

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/');
      return;
    }
    loadUsers();
  }, [user, navigate]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await api.getAdminUsers();
      setUsers(data.users || []);
    } catch (error) {
      if (showToast) showToast(error.message || 'Failed to load users', 'error');
    } finally {
      setLoading(false);
    }
  };

  const updateRow = (updatedUser) => {
    setUsers((prev) => prev.map((row) => (row.id === updatedUser.id ? updatedUser : row)));
  };

  const askAction = (title, message, actionFn, type = 'success') => {
    setActionDialog({
      isOpen: true,
      title,
      message,
      type,
      onConfirm: async () => {
        try {
          await actionFn();
        } finally {
          setActionDialog({ isOpen: false, title: '', message: '', onConfirm: null, type: 'success' });
        }
      },
    });
  };

  const handleRoleUpdate = (targetUser, role) => {
    const roleRank = { student: 1, faculty: 2, admin: 3 };
    const isDemotion = (roleRank[role] || 0) < (roleRank[targetUser.role] || 0);

    askAction(
      'Confirm Role Change',
      `Change ${targetUser.email} to ${role}?`,
      async () => {
        const res = await api.updateAdminUserRole(targetUser.id, role);
        updateRow(res.user);
        if (showToast) showToast(res.message || 'Role updated', 'success');
      },
      isDemotion ? 'danger' : 'success'
    );
  };

  const handleStatusUpdate = (targetUser, accountStatus) => {
    askAction(
      'Confirm Account Status Change',
      `${accountStatus === 'suspended' ? 'Suspend' : 'Activate'} ${targetUser.email}?`,
      async () => {
        const res = await api.updateAdminUserStatus(targetUser.id, accountStatus);
        updateRow(res.user);
        if (showToast) showToast(res.message || 'Status updated', 'success');
      },
      accountStatus === 'suspended' ? 'danger' : 'success'
    );
  };

  const handleResetVerification = (targetUser) => {
    askAction(
      'Reset Verification?',
      `Reset verification for ${targetUser.email} to pending? User must upload ID again.`,
      async () => {
        const res = await api.resetAdminUserVerification(targetUser.id);
        updateRow(res.user);
        if (showToast) showToast(res.message || 'Verification reset', 'success');
      },
      'danger'
    );
  };

  const filteredUsers = useMemo(() => {
    return users.filter((row) => {
      const q = search.trim().toLowerCase();
      const matchesSearch = !q || row.email.toLowerCase().includes(q) || (row.name || '').toLowerCase().includes(q);
      const matchesRole = roleFilter === 'all' || row.role === roleFilter;
      const matchesStatus = statusFilter === 'all' || row.account_status === statusFilter;
      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, search, roleFilter, statusFilter]);

  const stats = useMemo(() => {
    const total = users.length;
    const adminCount = users.filter((u) => u.role === 'admin').length;
    const facultyCount = users.filter((u) => u.role === 'faculty').length;
    const suspendedCount = users.filter((u) => u.account_status === 'suspended').length;
    const pendingVerification = users.filter((u) => u.verification_status === 'pending').length;
    return { total, adminCount, facultyCount, suspendedCount, pendingVerification };
  }, [users]);

  return (
    <div className="admin-users-page">
      <div className="admin-users-header">
        <button className="mobile-menu-btn" onClick={onToggleSidebar}>
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <div className="header-copy">
          <h1>User Management</h1>
          {/* <p>Promote roles and manage account access.</p> */}
        </div>
        <button className="refresh-users-btn" onClick={loadUsers}>Refresh</button>
      </div>

      <div className="admin-users-content">
        {/* <div className="users-stats-row">
          <div className="users-stat-card">
            <span className="label">Total Users</span>
            <span className="value">{stats.total}</span>
          </div>
          <div className="users-stat-card">
            <span className="label">Admins</span>
            <span className="value">{stats.adminCount}</span>
          </div>
          <div className="users-stat-card">
            <span className="label">Faculty</span>
            <span className="value">{stats.facultyCount}</span>
          </div>
          <div className="users-stat-card warning">
            <span className="label">Suspended</span>
            <span className="value">{stats.suspendedCount}</span>
          </div>
          <div className="users-stat-card pending">
            <span className="label">Pending Verification</span>
            <span className="value">{stats.pendingVerification}</span>
          </div>
        </div> */}

        <div className="users-filter-row">
          <input
            className="users-search"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or email"
          />
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="all">All roles</option>
            <option value="student">student</option>
            <option value="faculty">faculty</option>
            <option value="admin">admin</option>
          </select>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All status</option>
            <option value="active">active</option>
            <option value="suspended">suspended</option>
          </select>
        </div>

        {loading ? (
          <div className="users-loading">Loading users...</div>
        ) : (
          <div className="users-table-wrap">
            <table className="users-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Verification</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((row) => {
                  const isSelf = row.id === user?.id;
                  return (
                    <tr key={row.id}>
                      <td>{row.name || 'N/A'}</td>
                      <td>{row.email}</td>
                      <td>
                        <span className={`chip chip-role chip-${row.role}`}>{row.role}</span>
                      </td>
                      <td>
                        <span className={`chip chip-status chip-${row.account_status}`}>{row.account_status}</span>
                      </td>
                      <td>
                        <span className={`chip chip-verify chip-${row.verification_status}`}>{row.verification_status}</span>
                      </td>
                      <td>
                        <div className="action-buttons">
                          {!isSelf && row.role !== 'faculty' && (
                            <button className="promote" onClick={() => handleRoleUpdate(row, 'faculty')}>Promote Faculty</button>
                          )}
                          {!isSelf && row.role !== 'admin' && (
                            <button className="promote admin-promote" onClick={() => handleRoleUpdate(row, 'admin')}>Promote Admin</button>
                          )}
                          {!isSelf && row.role !== 'student' && (
                            <button className="neutral" onClick={() => handleRoleUpdate(row, 'student')}>Set Student</button>
                          )}
                          {!isSelf && row.account_status === 'active' && (
                            <button className="danger" onClick={() => handleStatusUpdate(row, 'suspended')}>Suspend</button>
                          )}
                          {row.account_status === 'suspended' && (
                            <button className="success" onClick={() => handleStatusUpdate(row, 'active')}>Activate</button>
                          )}
                          {!isSelf && (
                            <button className="secondary" onClick={() => handleResetVerification(row)}>Reset Verification</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td className="users-empty-cell" colSpan={6}>
                      No users match the selected filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Dialog
        isOpen={actionDialog.isOpen}
        onClose={() => setActionDialog({ isOpen: false, title: '', message: '', onConfirm: null, type: 'success' })}
        onConfirm={actionDialog.onConfirm}
        title={actionDialog.title}
        message={actionDialog.message}
        confirmText="Confirm"
        cancelText="Cancel"
        type={actionDialog.type}
      />
    </div>
  );
}

export default AdminUsersPage;
