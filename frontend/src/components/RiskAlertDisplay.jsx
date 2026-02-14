import React, { useState } from 'react';
import './RiskAlertDisplay.css';
import { MdWarning, MdCalendarToday, MdSchedule, MdHelp } from 'react-icons/md';

/**
 * RiskAlertDisplay Component
 * Displays AI-detected risk alerts in a popover on hover
 */
function RiskAlertDisplay({ riskAlerts }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!riskAlerts || riskAlerts.length === 0) {
    return null;
  }

  const getAlertIcon = (riskType) => {
    switch (riskType) {
      case 'attendance':
        return <MdCalendarToday />;
      case 'deadline':
        return <MdSchedule />;
      case 'policy_confusion':
        return <MdHelp />;
      default:
        return <MdWarning />;
    }
  };

  const getSeverityClass = (severity) => {
    return `risk-alert-${severity}`;
  };

  const getSeverityLabel = (severity) => {
    return severity.charAt(0).toUpperCase() + severity.slice(1);
  };

  const getHighestSeverity = () => {
    const severityOrder = { high: 3, medium: 2, low: 1 };
    return riskAlerts.reduce((highest, alert) => {
      return severityOrder[alert.severity] > severityOrder[highest] 
        ? alert.severity 
        : highest;
    }, 'low');
  };

  return (
    <div 
      className="risk-alert-trigger-container"
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <button
        className={`risk-alert-trigger risk-alert-${getHighestSeverity()}`}
        title={`${riskAlerts.length} risk${riskAlerts.length > 1 ? 's' : ''} detected`}
      >
        <MdWarning className="risk-icon" />
        <span className="risk-count">{riskAlerts.length}</span>
      </button>

      {isOpen && (
        <div className="risk-alert-popover">
          {/* <div className="risk-popover-header">
            <MdWarning />
            <span>Risk Alerts Detected</span>
          </div> */}
          
          <div className="risk-popover-content">
            {riskAlerts.map((alert, index) => (
              <div
                key={index}
                className={`risk-alert-item ${getSeverityClass(alert.severity)}`}
              >
                <div className="risk-item-header">
                  <div className="risk-item-icon">
                    {getAlertIcon(alert.risk_type)}
                  </div>
                  <div className="risk-item-title">
                    <span className="risk-type-label">
                      {alert.risk_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span className={`risk-severity-badge ${getSeverityClass(alert.severity)}`}>
                      {getSeverityLabel(alert.severity)}
                    </span>
                  </div>
                </div>
                
                <div className="risk-item-message">
                  {alert.message}
                </div>
                
                {alert.indicators && alert.indicators.length > 0 && (
                  <div className="risk-item-indicators">
                    <span className="indicators-label">Detected patterns:</span>
                    <div className="indicator-tags">
                      {alert.indicators.map((indicator, idx) => (
                        <span key={idx} className="indicator-tag">
                          {indicator}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="risk-item-footer">
                  <span className="confidence-score">
                    {(alert.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default RiskAlertDisplay;
