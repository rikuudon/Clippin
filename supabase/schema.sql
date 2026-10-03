-- ==============================================================================
-- Clippin: Supabase Database Schema & Storage Setup
-- ==============================================================================

-- 1. Create Videos Table
CREATE TABLE IF NOT EXISTS public.videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    youtube_id TEXT,
    source_url TEXT NOT NULL,
    title TEXT,
    creator TEXT,
    credit_line TEXT,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Create Clips Table
CREATE TABLE IF NOT EXISTS public.clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES public.videos(id) ON DELETE CASCADE,
    clip_id TEXT NOT NULL,
    title TEXT NOT NULL,
    hook TEXT,
    reason TEXT,
    score INTEGER NOT NULL DEFAULT 0,
    duration NUMERIC NOT NULL DEFAULT 0,
    start_time NUMERIC NOT NULL,
    end_time NUMERIC NOT NULL,
    post_caption TEXT,
    hashtags TEXT[] DEFAULT '{}',
    storage_path TEXT,
    status TEXT NOT NULL DEFAULT 'ready' CHECK (status IN ('ready', 'approved', 'rejected', 'posted')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Indexes for fast dashboard loading
CREATE INDEX IF NOT EXISTS idx_clips_video_id ON public.clips(video_id);
CREATE INDEX IF NOT EXISTS idx_clips_score ON public.clips(score DESC);
CREATE INDEX IF NOT EXISTS idx_videos_status ON public.videos(status);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clips ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies
-- Allow authenticated users (dashboard) to read all videos and clips
CREATE POLICY "Allow authenticated read videos" ON public.videos
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated update videos" ON public.videos
    FOR UPDATE TO authenticated USING (true);

CREATE POLICY "Allow authenticated read clips" ON public.clips
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated update clips" ON public.clips
    FOR UPDATE TO authenticated USING (true);

-- Allow service role (GitHub Actions worker) full access to insert/update
CREATE POLICY "Allow service role full access videos" ON public.videos
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role full access clips" ON public.clips
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 6. Storage Buckets Setup
-- Note: 'clips' and 'uploads' buckets should be created as private buckets
INSERT INTO storage.buckets (id, name, public)
VALUES ('clips', 'clips', false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('uploads', 'uploads', false)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS: Allow authenticated users to view objects
CREATE POLICY "Allow authenticated read storage clips" ON storage.objects
    FOR SELECT TO authenticated USING (bucket_id = 'clips');

-- Storage RLS: Allow service role to upload/manage storage objects
CREATE POLICY "Allow service role full access storage clips" ON storage.objects
    FOR ALL TO service_role USING (bucket_id IN ('clips', 'uploads')) WITH CHECK (bucket_id IN ('clips', 'uploads'));
