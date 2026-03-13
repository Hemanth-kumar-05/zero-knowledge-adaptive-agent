import React, { useState } from 'react';
import './FontAwesomeIconPicker.css';

// Popular FontAwesome icons categorized
const ICON_CATEGORIES = {
  'Academic': [
    { class: 'fa-solid fa-book', name: 'Book' },
    { class: 'fa-solid fa-graduation-cap', name: 'Graduation Cap' },
    { class: 'fa-solid fa-file-alt', name: 'Document' },
    { class: 'fa-solid fa-clipboard-list', name: 'Clipboard List' },
    { class: 'fa-solid fa-calendar-check', name: 'Calendar Check' },
    { class: 'fa-solid fa-pencil', name: 'Pencil' },
    { class: 'fa-solid fa-chalkboard-teacher', name: 'Teacher' },
    { class: 'fa-solid fa-user-graduate', name: 'Graduate' },
  ],
  'Planning': [
    { class: 'fa-solid fa-calendar', name: 'Calendar' },
    { class: 'fa-solid fa-clock', name: 'Clock' },
    { class: 'fa-solid fa-list-check', name: 'Checklist' },
    { class: 'fa-solid fa-chart-line', name: 'Chart' },
    { class: 'fa-solid fa-clipboard', name: 'Clipboard' },
    { class: 'fa-solid fa-tasks', name: 'Tasks' },
    { class: 'fa-solid fa-sticky-note', name: 'Note' },
    { class: 'fa-solid fa-calendar-days', name: 'Calendar Days' },
  ],
  'Research': [
    { class: 'fa-solid fa-flask', name: 'Flask' },
    { class: 'fa-solid fa-microscope', name: 'Microscope' },
    { class: 'fa-solid fa-book-open', name: 'Book Open' },
    { class: 'fa-solid fa-lightbulb', name: 'Lightbulb' },
    { class: 'fa-solid fa-search', name: 'Search' },
    { class: 'fa-solid fa-atom', name: 'Atom' },
    { class: 'fa-solid fa-dna', name: 'DNA' },
    { class: 'fa-solid fa-brain', name: 'Brain' },
  ],
  'Career': [
    { class: 'fa-solid fa-briefcase', name: 'Briefcase' },
    { class: 'fa-solid fa-building', name: 'Building' },
    { class: 'fa-solid fa-handshake', name: 'Handshake' },
    { class: 'fa-solid fa-user-tie', name: 'User Tie' },
    { class: 'fa-solid fa-chart-bar', name: 'Chart Bar' },
    { class: 'fa-solid fa-trophy', name: 'Trophy' },
    { class: 'fa-solid fa-rocket', name: 'Rocket' },
    { class: 'fa-solid fa-certificate', name: 'Certificate' },
  ],
  'Learning': [
    { class: 'fa-solid fa-book-reader', name: 'Book Reader' },
    { class: 'fa-solid fa-spell-check', name: 'Spell Check' },
    { class: 'fa-solid fa-highlighter', name: 'Highlighter' },
    { class: 'fa-solid fa-glasses', name: 'Glasses' },
    { class: 'fa-solid fa-laptop', name: 'Laptop' },
    { class: 'fa-solid fa-brain', name: 'Brain' },
    { class: 'fa-solid fa-puzzle-piece', name: 'Puzzle' },
    { class: 'fa-solid fa-users', name: 'Users' },
  ],
  'Tools': [
    { class: 'fa-solid fa-wrench', name: 'Wrench' },
    { class: 'fa-solid fa-cog', name: 'Cog' },
    { class: 'fa-solid fa-tools', name: 'Tools' },
    { class: 'fa-solid fa-hammer', name: 'Hammer' },
    { class: 'fa-solid fa-screwdriver', name: 'Screwdriver' },
    { class: 'fa-solid fa-compass', name: 'Compass' },
    { class: 'fa-solid fa-code', name: 'Code' },
    { class: 'fa-solid fa-terminal', name: 'Terminal' },
  ],
  'Communication': [
    { class: 'fa-solid fa-comments', name: 'Comments' },
    { class: 'fa-solid fa-comment', name: 'Comment' },
    { class: 'fa-solid fa-envelope', name: 'Envelope' },
    { class: 'fa-solid fa-phone', name: 'Phone' },
    { class: 'fa-solid fa-bullhorn', name: 'Bullhorn' },
    { class: 'fa-solid fa-bell', name: 'Bell' },
    { class: 'fa-solid fa-message', name: 'Message' },
    { class: 'fa-solid fa-paper-plane', name: 'Paper Plane' },
  ],
  'Other': [
    { class: 'fa-solid fa-star', name: 'Star' },
    { class: 'fa-solid fa-heart', name: 'Heart' },
    { class: 'fa-solid fa-check-circle', name: 'Check Circle' },
    { class: 'fa-solid fa-info-circle', name: 'Info Circle' },
    { class: 'fa-solid fa-exclamation-circle', name: 'Exclamation' },
    { class: 'fa-solid fa-question-circle', name: 'Question' },
    { class: 'fa-solid fa-flag', name: 'Flag' },
    { class: 'fa-solid fa-bookmark', name: 'Bookmark' },
  ]
};

function FontAwesomeIconPicker({ selectedIcon, onSelectIcon, category }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(category || 'Academic');
  const [isOpen, setIsOpen] = useState(false);

  // Filter icons based on search and category
  const getFilteredIcons = () => {
    const categoryIcons = ICON_CATEGORIES[selectedCategory] || [];
    
    if (!searchQuery) {
      return categoryIcons;
    }

    return categoryIcons.filter(icon =>
      icon.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      icon.class.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const handleSelectIcon = (iconClass) => {
    onSelectIcon(iconClass);
    setIsOpen(false);
  };

  const filteredIcons = getFilteredIcons();

  return (
    <div className="icon-picker-container">
      <div className="icon-picker-trigger" onClick={() => setIsOpen(!isOpen)}>
        <div className="selected-icon-preview">
          {selectedIcon ? (
            <>
              <i className={selectedIcon}></i>
              <span>{selectedIcon}</span>
            </>
          ) : (
            <span className="placeholder">Click to select an icon</span>
          )}
        </div>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>

      {isOpen && (
        <>
          <div className="icon-picker-overlay" onClick={() => setIsOpen(false)} />
          <div className="icon-picker-dropdown">
            <div className="icon-picker-search">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
              <input
                type="text"
                placeholder="Search icons..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              />
            </div>

            <div className="icon-picker-categories">
              {Object.keys(ICON_CATEGORIES).map(cat => (
                <button
                  key={cat}
                  className={`category-tab ${selectedCategory === cat ? 'active' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedCategory(cat);
                    setSearchQuery('');
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div className="icon-picker-grid">
              {filteredIcons.length === 0 ? (
                <div className="no-icons">No icons found</div>
              ) : (
                filteredIcons.map(icon => (
                  <div
                    key={icon.class}
                    className={`icon-option ${selectedIcon === icon.class ? 'selected' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectIcon(icon.class);
                    }}
                    title={icon.name}
                  >
                    <i className={icon.class}></i>
                    <span>{icon.name}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default FontAwesomeIconPicker;
