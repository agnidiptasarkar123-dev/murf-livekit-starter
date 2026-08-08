'use client';

import React, { useState, useMemo } from 'react';
import { X, Search, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { featureData, type FeatureCategory } from './feature-data';
import { useLanguage } from './language-context';

interface FeatureDetailsModalProps {
  category: FeatureCategory;
  onClose: () => void;
  title: string;
}

export function FeatureDetailsModal({ category, onClose, title }: FeatureDetailsModalProps) {
  const { t } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSubCategory, setSelectedSubCategory] = useState('All');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Filter data based on category, search, and sub-category
  const filteredData = useMemo(() => {
    return featureData.filter((item) => {
      const matchesCategory = item.category === category;
      const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                            item.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesSubCategory = selectedSubCategory === 'All' || item.subCategory === selectedSubCategory;
      return matchesCategory && matchesSearch && matchesSubCategory;
    });
  }, [category, searchQuery, selectedSubCategory]);

  // Extract unique sub-categories for the dropdown
  const subCategories = useMemo(() => {
    const subs = featureData.filter(item => item.category === category).map(item => item.subCategory);
    return ['All', ...Array.from(new Set(subs))];
  }, [category]);

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(10, 63, 66, 0.4)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px',
    }}>
      <div style={{
        background: '#ffffff', borderRadius: 24, width: '100%', maxWidth: 600,
        maxHeight: '90vh', display: 'flex', flexDirection: 'column',
        boxShadow: '0 20px 60px rgba(13,110,115,0.15)',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px', borderBottom: '1px solid #e8f7f8',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: '#f9fafb'
        }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: '#0a3f42' }}>{title}</h2>
          <button onClick={onClose} style={{
            background: '#e8f7f8', border: 'none', borderRadius: '50%', width: 36, height: 36,
            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
            color: '#0d6e73'
          }}>
            <X size={20} />
          </button>
        </div>

        {/* Search & Filter Bar */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #e8f7f8', display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 200px', position: 'relative' }}>
            <Search size={18} color="#6b7280" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
            <input 
              type="text" 
              placeholder={t('searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%', padding: '12px 14px 12px 40px', borderRadius: 12,
                border: '1px solid #d1eff0', background: '#f4f8f8',
                fontSize: 14, color: '#374151', outline: 'none'
              }}
            />
          </div>
          <div style={{ flex: '0 0 auto', position: 'relative' }}>
            <Filter size={16} color="#6b7280" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
            <select
              value={selectedSubCategory}
              onChange={(e) => setSelectedSubCategory(e.target.value)}
              style={{
                padding: '12px 14px 12px 36px', borderRadius: 12,
                border: '1px solid #d1eff0', background: '#ffffff',
                fontSize: 14, color: '#374151', outline: 'none', cursor: 'pointer',
                appearance: 'none', minWidth: 140
              }}
            >
              {subCategories.map(sub => (
                <option key={sub} value={sub}>{sub === 'All' ? t('filterAll') : sub}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Scrollable List */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1, background: '#ffffff' }}>
          {filteredData.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: '#6b7280' }}>
              <p>{t('noResults')}</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {filteredData.map(item => {
                const isExpanded = expandedId === item.id;
                return (
                  <div 
                    key={item.id} 
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    style={{
                      padding: '16px', borderRadius: 16, border: `1px solid ${isExpanded ? '#0d6e73' : '#e8f7f8'}`,
                      background: isExpanded ? '#f4f8f8' : '#fcfdfd', cursor: 'pointer',
                      transition: 'all 0.2s',
                      boxShadow: isExpanded ? '0 4px 12px rgba(13,110,115,0.05)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                          <span style={{ fontSize: 11, fontWeight: 700, color: '#0d6e73', background: isExpanded ? '#ffffff' : '#e8f7f8', padding: '2px 8px', borderRadius: 999 }}>
                            {item.subCategory}
                          </span>
                        </div>
                        <h3 style={{ margin: '0 0 6px', fontSize: 16, fontWeight: 700, color: '#0a3f42' }}>{item.title}</h3>
                        {!isExpanded && (
                          <p style={{ margin: 0, fontSize: 13, color: '#6b7280', lineHeight: 1.5 }}>{item.description}</p>
                        )}
                      </div>
                      <div style={{ color: '#0d6e73', padding: '4px' }}>
                        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                      </div>
                    </div>
                    {isExpanded && (
                      <div style={{ 
                        marginTop: 12, paddingTop: 12, borderTop: '1px solid #d1eff0',
                        fontSize: 14, color: '#374151', lineHeight: 1.6, whiteSpace: 'pre-wrap'
                      }}>
                        {item.fullDetails}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
