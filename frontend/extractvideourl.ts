import { Innertube, UniversalCache } from "youtubei.js";

(async () => {
  // 1. Create a session (mimicking a real browser/app)
  const yt = await Innertube.create({
    cache: new UniversalCache(false),
    generate_session_locally: true, // Crucial for speed
  });

  // 2. Get Video Info
  const videoId = "dQw4w9WgXcQ";
  const info = await yt.getBasicInfo(videoId);

  // 3. Get the Stream URL (Deciphers the signature automatically)
  // Cobalt usually requests 'ios' or 'android' client to avoid throttling
  const format = info.chooseFormat({ type: "video", quality: "best" });

  console.log("Download URL:", format.decipher(yt.session.player));
})();
