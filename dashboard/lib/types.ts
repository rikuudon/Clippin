export interface Video {
  id: string;
  youtube_id: string | null;
  source_url: string;
  title: string;
  creator: string;
  credit_line: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Clip {
  id: string;
  video_id: string;
  clip_id: string;
  title: string;
  hook: string;
  reason: string;
  score: number;
  duration: number;
  start_time: number;
  end_time: number;
  post_caption: string;
  hashtags: string[];
  storage_path: string;
  status: 'ready' | 'approved' | 'rejected' | 'posted';
  created_at: string;
  signed_url?: string;
  download_url?: string;
}

export interface ApiResponse {
  success: boolean;
  videos: Video[];
  activeVideo: Video | null;
  clips: Clip[];
  stats: {
    totalClips: number;
    avgScore: number;
    approvedCount: number;
    readyCount: number;
    rejectedCount: number;
  };
}
