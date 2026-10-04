import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { Video, Clip, ApiResponse } from '@/lib/types';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const requestedVideoId = searchParams.get('videoId');

    // 1. Fetch videos
    const { data: videosData, error: videosError } = await supabaseAdmin
      .from('videos')
      .select('*')
      .order('created_at', { ascending: false });

    if (videosError) {
      console.error('Error fetching videos from Supabase:', videosError);
      return NextResponse.json(
        { success: false, error: videosError.message },
        { status: 500 }
      );
    }

    const videos: Video[] = videosData || [];
    const activeVideo: Video | null = requestedVideoId
      ? videos.find((v) => v.id === requestedVideoId) || videos[0] || null
      : videos[0] || null;

    if (!activeVideo) {
      return NextResponse.json<ApiResponse>({
        success: true,
        videos: [],
        activeVideo: null,
        clips: [],
        stats: {
          totalClips: 0,
          avgScore: 0,
          approvedCount: 0,
          readyCount: 0,
          rejectedCount: 0,
        },
      });
    }

    // 2. Fetch clips for active video
    const { data: clipsData, error: clipsError } = await supabaseAdmin
      .from('clips')
      .select('*')
      .eq('video_id', activeVideo.id)
      .order('score', { ascending: false });

    if (clipsError) {
      console.error('Error fetching clips:', clipsError);
      return NextResponse.json(
        { success: false, error: clipsError.message },
        { status: 500 }
      );
    }

    // 3. Generate signed URLs for private 'clips' bucket
    const clipsWithUrls: Clip[] = await Promise.all(
      (clipsData || []).map(async (clip: Clip) => {
        let signedUrl: string | undefined = undefined;
        let downloadUrl: string | undefined = undefined;

        if (clip.storage_path) {
          try {
            // Streaming / Playback signed URL (expires in 2 hours = 7200s)
            const { data: playData, error: playError } = await supabaseAdmin.storage
              .from('clips')
              .createSignedUrl(clip.storage_path, 7200);

            if (!playError && playData?.signedUrl) {
              signedUrl = playData.signedUrl;
            }

            // Download signed URL with custom download attachment filename
            const downloadFilename = `${clip.clip_id}.mp4`;
            const { data: dlData, error: dlError } = await supabaseAdmin.storage
              .from('clips')
              .createSignedUrl(clip.storage_path, 7200, {
                download: downloadFilename,
              });

            if (!dlError && dlData?.signedUrl) {
              downloadUrl = dlData.signedUrl;
            }
          } catch (storageErr) {
            console.warn(`Failed to sign URL for ${clip.storage_path}:`, storageErr);
          }
        }

        return {
          ...clip,
          signed_url: signedUrl,
          download_url: downloadUrl || signedUrl,
        };
      })
    );

    // 4. Calculate Aggregate Stats
    const totalClips = clipsWithUrls.length;
    const avgScore = totalClips > 0
      ? Math.round(clipsWithUrls.reduce((sum, c) => sum + (c.score || 0), 0) / totalClips)
      : 0;
    const approvedCount = clipsWithUrls.filter((c) => c.status === 'approved').length;
    const readyCount = clipsWithUrls.filter((c) => c.status === 'ready').length;
    const rejectedCount = clipsWithUrls.filter((c) => c.status === 'rejected').length;

    return NextResponse.json<ApiResponse>({
      success: true,
      videos,
      activeVideo,
      clips: clipsWithUrls,
      stats: {
        totalClips,
        avgScore,
        approvedCount,
        readyCount,
        rejectedCount,
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal Server Error';
    console.error('API Error in GET /api/clips:', err);
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}
