import { Innertube, UniversalCache, Platform } from "youtubei.js";

// Essential shim for URL deciphering (required by youtubei.js)
Platform.shim.eval = (data, env) => {
  const props = Object.entries(env)
    .map(([k, v]) => `${k}: exportedVars.${k}Function("${v}")`)
    .join(", ");

  return new Function(`${data.output}\nreturn { ${props} }`)();
};

let yt: Innertube;

async function getYoutubeClient() {
  return (yt ??= await Innertube.create({
    cache: new UniversalCache(false),
    generate_session_locally: true,
  }));
}

export async function downloadVideo(
  url: string,
  format: "video+audio" | "audio" = "video+audio"
): Promise<string> {
  const client = await getYoutubeClient();

  // Extract video ID
  const videoId = url.match(
    /(?:youtube\.com\/watch\?v=|youtu\.be\/)([0-9A-Za-z_-]{11})/
  )?.[1];
  if (!videoId) throw new Error("Invalid YouTube URL");

  // Get video info
  const { basic_info } = await client.getBasicInfo(videoId);
  const ext = format === "audio" ? "m4a" : "mp4";
  const filename = `${(basic_info.title || "video")
    .replace(/[^a-z0-9]/gi, "_")
    .toLowerCase()}.${ext}`;

  console.log(`Downloading: ${basic_info.title || videoId}`);

  // Download stream
  const stream = await client.download(videoId, {
    type: format === "audio" ? "audio" : "video+audio",
    quality: "best",
    format: "mp4",
  });

  // Stream to file
  const writer = Bun.file(filename).writer();

  for await (const chunk of stream) {
    writer.write(chunk);
  }

  writer.end();

  console.log(`✓ Saved to ${filename}`);
  return filename;
}

// Run if executed directly
if (import.meta.main) {
  const url = "https://www.youtube.com/watch?v=Qa8IfEeBJqk";
  await downloadVideo(url);
}
