'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  Sparkles,
  Flame,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  Download,
  Maximize2,
  X,
  Play,
  Share2,
  RefreshCw,
  Video as VideoIcon,
  Tag,
  Clock,
  User,
  SlidersHorizontal,
} from 'lucide-react';
import { Video, Clip, ApiResponse } from '@/lib/types';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [videos, setVideos] = useState<Video[]>([]);
  const [activeVideo, setActiveVideo] = useState<Video | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [stats, setStats] = useState({
    totalClips: 0,
    avgScore: 0,
    approvedCount: 0,
    readyCount: 0,
    rejectedCount: 0,
  });

  const [statusFilter, setStatusFilter] = useState<'all' | 'approved' | 'ready' | 'rejected'>('all');
  const [sortBy, setSortBy] = useState<'score' | 'duration' | 'start_time'>('score');
  const [selectedClip, setSelectedClip] = useState<Clip | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  // Fetch data
  const fetchData = async (videoId?: string) => {
    try {
      setRefreshing(true);
      const url = videoId ? `/api/clips?videoId=${videoId}` : '/api/clips';
      const res = await fetch(url);
      const data: ApiResponse = await res.json();

      if (data.success) {
        setVideos(data.videos || []);
        setActiveVideo(data.activeVideo || null);
        setClips(data.clips || []);
        setStats(data.stats);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Copy to clipboard helper
  const handleCopy = (key: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => {
      setCopiedKey(null);
    }, 2200);
  };

  // Toggle clip approval status
  const handleUpdateStatus = async (clip: Clip, newStatus: 'approved' | 'rejected' | 'ready') => {
    const updatedStatus = clip.status === newStatus ? 'ready' : newStatus;
    setUpdatingId(clip.id);

    // Optimistic update
    setClips((prev) =>
      prev.map((c) => (c.id === clip.id ? { ...c, status: updatedStatus } : c))
    );

    try {
      const res = await fetch(`/api/clips/${clip.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: updatedStatus }),
      });

      if (!res.ok) {
        throw new Error('Failed to update status on server');
      }

      // Update aggregate counts
      setStats((prev) => {
        const approvedCount = clips.filter((c) =>
          c.id === clip.id ? updatedStatus === 'approved' : c.status === 'approved'
        ).length;
        const readyCount = clips.filter((c) =>
          c.id === clip.id ? updatedStatus === 'ready' : c.status === 'ready'
        ).length;
        const rejectedCount = clips.filter((c) =>
          c.id === clip.id ? updatedStatus === 'rejected' : c.status === 'rejected'
        ).length;
        return { ...prev, approvedCount, readyCount, rejectedCount };
      });
    } catch (err) {
      console.error('Error updating clip status:', err);
      // Rollback optimistic update
      setClips((prev) =>
        prev.map((c) => (c.id === clip.id ? { ...c, status: clip.status } : c))
      );
    } finally {
      setUpdatingId(null);
    }
  };

  // Filter and sort clips
  const filteredClips = useMemo(() => {
    return clips
      .filter((c) => (statusFilter === 'all' ? true : c.status === statusFilter))
      .sort((a, b) => {
        if (sortBy === 'score') return b.score - a.score;
        if (sortBy === 'duration') return b.duration - a.duration;
        if (sortBy === 'start_time') return a.start_time - b.start_time;
        return 0;
      });
  }, [clips, statusFilter, sortBy]);

  // Virality score style helper
  const getScoreBadgeClass = (score: number) => {
    if (score >= 90) return 'ultra';
    if (score >= 80) return 'high';
    return 'mid';
  };

  return (
    <main className="app-container">
      {/* 1. Header & Navigation */}
      <header className="header">
        <div className="brand-section">
          <div className="brand-logo">
            <Sparkles size={24} color="#FFFFFF" />
          </div>
          <div>
            <h1 className="brand-title">Clippin Studio</h1>
            <p className="brand-tagline">AI-Powered 9:16 Virality & Review Engine</p>
          </div>
        </div>

        <div className="header-actions">
          <div className="framing-indicator">
            <span className="indicator-dot" />
            Supabase Cloud Connected
          </div>

          <button
            onClick={() => fetchData(activeVideo?.id)}
            disabled={refreshing}
            className="btn-download"
            title="Refresh Data"
          >
            <RefreshCw size={18} className={refreshing ? 'loading-spinner' : ''} />
          </button>
        </div>
      </header>

      {/* 2. Video Hero & Summary Stats */}
      {activeVideo && (
        <section className="video-hero">
          <div className="hero-main">
            <div className="hero-info">
              <div className="source-badge">
                <VideoIcon size={14} />
                YouTube Source
              </div>
              <h2 className="hero-title">{activeVideo.title}</h2>
              <div className="hero-meta">
                <span className="creator-pill">
                  <User size={14} style={{ display: 'inline', marginRight: 4 }} />
                  {activeVideo.creator || 'MaxTheMeatGuy'}
                </span>
                <span>•</span>
                <span>{activeVideo.credit_line || 'Original Creator'}</span>
              </div>
            </div>

            {/* Video Selector Dropdown if multiple videos */}
            {videos.length > 1 && (
              <div>
                <select
                  value={activeVideo.id}
                  onChange={(e) => fetchData(e.target.value)}
                  className="sort-select"
                >
                  {videos.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.title.slice(0, 40)}...
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Stats Grid */}
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Total Clips</span>
              <span className="stat-value">{stats.totalClips}</span>
            </div>

            <div className="stat-card">
              <span className="stat-label">Avg Virality</span>
              <span className="stat-value score">
                <Flame size={20} color="#34D399" />
                {stats.avgScore}
              </span>
            </div>

            <div className="stat-card">
              <span className="stat-label">Approved</span>
              <span className="stat-value approved">
                <CheckCircle2 size={20} color="#60A5FA" />
                {stats.approvedCount}
              </span>
            </div>

            <div className="stat-card">
              <span className="stat-label">Ready for Review</span>
              <span className="stat-value">{stats.readyCount}</span>
            </div>
          </div>
        </section>
      )}

      {/* 3. Controls & Filter Bar */}
      <section className="controls-bar">
        <div className="filter-tabs">
          <button
            onClick={() => setStatusFilter('all')}
            className={`filter-tab ${statusFilter === 'all' ? 'active' : ''}`}
          >
            All Clips
            <span className="tab-badge">{stats.totalClips}</span>
          </button>

          <button
            onClick={() => setStatusFilter('approved')}
            className={`filter-tab ${statusFilter === 'approved' ? 'active' : ''}`}
          >
            Approved
            <span className="tab-badge">{stats.approvedCount}</span>
          </button>

          <button
            onClick={() => setStatusFilter('ready')}
            className={`filter-tab ${statusFilter === 'ready' ? 'active' : ''}`}
          >
            Ready
            <span className="tab-badge">{stats.readyCount}</span>
          </button>

          <button
            onClick={() => setStatusFilter('rejected')}
            className={`filter-tab ${statusFilter === 'rejected' ? 'active' : ''}`}
          >
            Rejected
            <span className="tab-badge">{stats.rejectedCount}</span>
          </button>
        </div>

        <div className="filter-actions">
          <SlidersHorizontal size={16} color="var(--text-muted)" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'score' | 'duration' | 'start_time')}
            className="sort-select"
          >
            <option value="score">Highest Virality Score</option>
            <option value="duration">Longest Duration</option>
            <option value="start_time">Video Timeline Order</option>
          </select>
        </div>
      </section>

      {/* 4. Clips Grid */}
      {loading ? (
        <div className="empty-state">
          <div className="loading-spinner" />
          <p style={{ color: 'var(--text-secondary)' }}>Loading AI-curated clips from Supabase...</p>
        </div>
      ) : filteredClips.length === 0 ? (
        <div className="empty-state">
          <VideoIcon size={48} color="var(--text-muted)" />
          <h3>No clips found</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            No clips match the selected status filter &ldquo;{statusFilter}&rdquo;.
          </p>
        </div>
      ) : (
        <div className="clips-grid">
          {filteredClips.map((clip) => {
            const isApproved = clip.status === 'approved';
            const isRejected = clip.status === 'rejected';

            return (
              <article
                key={clip.id}
                className={`clip-card ${isApproved ? 'approved-card' : ''} ${
                  isRejected ? 'rejected-card' : ''
                }`}
              >
                {/* 9:16 Video Player Container */}
                <div className="card-media-wrapper">
                  {clip.signed_url ? (
                    <video
                      src={clip.signed_url}
                      controls
                      preload="metadata"
                      playsInline
                      className="card-video"
                    />
                  ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      Video storage unavailable
                    </div>
                  )}

                  {/* Overlays */}
                  <div className="video-overlay-top">
                    <div className={`score-badge ${getScoreBadgeClass(clip.score)}`}>
                      <Flame size={14} />
                      {clip.score} Virality
                    </div>

                    <div className="duration-pill">
                      <Clock size={12} style={{ display: 'inline', marginRight: 4 }} />
                      {clip.duration.toFixed(1)}s
                    </div>
                  </div>

                  <div className="video-overlay-bottom">
                    <div className="framing-indicator">
                      <span className="indicator-dot" />
                      Speaker Centered
                    </div>

                    <button
                      onClick={() => setSelectedClip(clip)}
                      className="btn-download"
                      style={{ width: 32, height: 32 }}
                      title="Open Fullscreen Theater"
                    >
                      <Maximize2 size={14} />
                    </button>
                  </div>
                </div>

                {/* Card Content */}
                <div className="card-content">
                  <div className="clip-header-title">
                    <span className="clip-id-label">{clip.clip_id.toUpperCase()}</span>
                    <h3 className="clip-title-text">{clip.title}</h3>
                  </div>

                  {/* Hook Quote Box */}
                  <div className="hook-box">
                    <span className="hook-label">Hook (First 3 Seconds)</span>
                    <p className="hook-text">&ldquo;{clip.hook}&rdquo;</p>
                  </div>

                  {/* Why Viral */}
                  <p className="reason-box">{clip.reason}</p>

                  {/* Copy Deck (Caption & Hashtags) */}
                  <div className="copy-deck">
                    <div className="copy-row">
                      <p className="copy-text">{clip.post_caption}</p>
                      <button
                        onClick={() => handleCopy(`cap-${clip.id}`, clip.post_caption)}
                        className={`btn-copy ${copiedKey === `cap-${clip.id}` ? 'copied' : ''}`}
                      >
                        {copiedKey === `cap-${clip.id}` ? (
                          <>
                            <Check size={13} />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy size={13} />
                            Copy Caption
                          </>
                        )}
                      </button>
                    </div>

                    {clip.hashtags && clip.hashtags.length > 0 && (
                      <div className="copy-row" style={{ marginTop: 4 }}>
                        <div className="hashtag-container">
                          {clip.hashtags.map((tag, idx) => (
                            <span key={idx} className="hashtag-pill">
                              #{tag.replace(/^#/, '')}
                            </span>
                          ))}
                        </div>
                        <button
                          onClick={() =>
                            handleCopy(
                              `tag-${clip.id}`,
                              clip.hashtags.map((t) => (t.startsWith('#') ? t : `#${t}`)).join(' ')
                            )
                          }
                          className={`btn-copy ${copiedKey === `tag-${clip.id}` ? 'copied' : ''}`}
                        >
                          {copiedKey === `tag-${clip.id}` ? (
                            <>
                              <Check size={13} />
                              Copied
                            </>
                          ) : (
                            <>
                              <Tag size={13} />
                              Tags
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Action Toolbar */}
                  <div className="card-actions">
                    <button
                      onClick={() => handleUpdateStatus(clip, 'approved')}
                      disabled={updatingId === clip.id}
                      className={`btn-action btn-approve ${isApproved ? 'active' : ''}`}
                    >
                      <CheckCircle2 size={16} />
                      {isApproved ? 'Approved' : 'Approve'}
                    </button>

                    <button
                      onClick={() => handleUpdateStatus(clip, 'rejected')}
                      disabled={updatingId === clip.id}
                      className={`btn-action btn-reject ${isRejected ? 'active' : ''}`}
                    >
                      <XCircle size={16} />
                      {isRejected ? 'Rejected' : 'Reject'}
                    </button>

                    {clip.download_url && (
                      <a
                        href={clip.download_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-download"
                        title="Download MP4"
                      >
                        <Download size={16} />
                      </a>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* 5. Theater Mode Modal */}
      {selectedClip && (
        <div className="modal-backdrop" onClick={() => setSelectedClip(null)}>
          <div className="modal-container" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setSelectedClip(null)}
              className="modal-close-btn"
              title="Close Theater"
            >
              <X size={18} />
            </button>

            {/* Vertical Video View */}
            <div className="modal-video-pane">
              {selectedClip.signed_url && (
                <video
                  src={selectedClip.signed_url}
                  controls
                  autoPlay
                  playsInline
                  className="modal-video"
                />
              )}
            </div>

            {/* Metadata Pane */}
            <div className="modal-details-pane">
              <div>
                <div
                  className={`score-badge ${getScoreBadgeClass(selectedClip.score)}`}
                  style={{ marginBottom: 12 }}
                >
                  <Flame size={14} />
                  {selectedClip.score} Virality Match
                </div>
                <h2 style={{ fontSize: '1.25rem', marginBottom: 8 }}>{selectedClip.title}</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Duration: {selectedClip.duration.toFixed(1)}s • Timeline: {selectedClip.start_time.toFixed(1)}s - {selectedClip.end_time.toFixed(1)}s
                </p>
              </div>

              <div className="hook-box">
                <span className="hook-label">Hook</span>
                <p className="hook-text">&ldquo;{selectedClip.hook}&rdquo;</p>
              </div>

              <div>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                  VIRALITY RATIONALE
                </h4>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {selectedClip.reason}
                </p>
              </div>

              <div>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                  POST CAPTION
                </h4>
                <div className="copy-deck">
                  <p style={{ fontSize: '0.85rem', color: '#E2E8F0', lineHeight: 1.4 }}>
                    {selectedClip.post_caption}
                  </p>
                  <button
                    onClick={() => handleCopy(`modal-cap-${selectedClip.id}`, selectedClip.post_caption)}
                    className={`btn-copy ${
                      copiedKey === `modal-cap-${selectedClip.id}` ? 'copied' : ''
                    }`}
                    style={{ alignSelf: 'flex-start', marginTop: 8 }}
                  >
                    {copiedKey === `modal-cap-${selectedClip.id}` ? (
                      <>
                        <Check size={14} /> Copied!
                      </>
                    ) : (
                      <>
                        <Copy size={14} /> Copy Caption
                      </>
                    )}
                  </button>
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                  HASHTAGS
                </h4>
                <div className="hashtag-container" style={{ marginBottom: 10 }}>
                  {selectedClip.hashtags?.map((tag, idx) => (
                    <span key={idx} className="hashtag-pill">
                      #{tag.replace(/^#/, '')}
                    </span>
                  ))}
                </div>
                <button
                  onClick={() =>
                    handleCopy(
                      `modal-tags-${selectedClip.id}`,
                      selectedClip.hashtags?.map((t) => (t.startsWith('#') ? t : `#${t}`)).join(' ') || ''
                    )
                  }
                  className={`btn-copy ${
                    copiedKey === `modal-tags-${selectedClip.id}` ? 'copied' : ''
                  }`}
                >
                  {copiedKey === `modal-tags-${selectedClip.id}` ? (
                    <>
                      <Check size={14} /> Copied!
                    </>
                  ) : (
                    <>
                      <Tag size={14} /> Copy All Hashtags
                    </>
                  )}
                </button>
              </div>

              <div style={{ marginTop: 'auto', display: 'flex', gap: 10 }}>
                <button
                  onClick={() => handleUpdateStatus(selectedClip, 'approved')}
                  className={`btn-action btn-approve ${
                    selectedClip.status === 'approved' ? 'active' : ''
                  }`}
                >
                  <CheckCircle2 size={16} />
                  {selectedClip.status === 'approved' ? 'Approved' : 'Approve'}
                </button>

                {selectedClip.download_url && (
                  <a
                    href={selectedClip.download_url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-download"
                    title="Download Clip"
                  >
                    <Download size={18} />
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
