<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import { Skeleton } from "$lib/components/ui/skeleton/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import * as ButtonGroup from "$lib/components/ui/button-group/index.js";
  import Clipboard from "@lucide/svelte/icons/clipboard";
  import SunIcon from "@lucide/svelte/icons/sun";
  import MoonIcon from "@lucide/svelte/icons/moon";
  import { slide, fade } from "svelte/transition";
  import { toggleMode } from "mode-watcher";

  let url = $state("");
  let type = $state<"video" | "audio">("video");
  let progress = $state(0);
  let downloading = $state(false);
  let finished = $state(false);
  let failed = $state(false);
  let error = $state("");

  let interval: ReturnType<typeof setInterval> | null = null;
  let skeletonTimeout: ReturnType<typeof setTimeout> | null = null;
  let showSkeleton = $state(false);
  let hasPreview = $state(false);
  let hasProgress = $state(false);

  const valid = $derived(
    url.trim().length > 0 &&
      (url.includes("youtube.com") || url.includes("youtu.be"))
  );

  const showPreview = $derived(
    progress > 0 || !!error || showSkeleton || hasPreview
  );
  const showProgress = $derived(progress > 0 || showSkeleton || hasProgress);
  const showError = $derived(!!error);

  function download() {
    failed = false;
    error = "";
    progress = 0;

    if (!valid) return;

    downloading = true;
    // Show skeleton immediately for 1s and freeze progress at 0%
    showSkeleton = true;
    hasProgress = true;
    hasPreview = true;
    if (skeletonTimeout) {
      clearTimeout(skeletonTimeout);
      skeletonTimeout = null;
    }
    skeletonTimeout = setTimeout(() => {
      // hide skeleton and show real preview (keep container visible via hasPreview)
      showSkeleton = false;
      skeletonTimeout = null;

      interval = setInterval(() => {
        progress += Math.random() * 15 + 5;

        if (progress >= 100) {
          progress = 100;
          showSkeleton = false;
          clearInterval(interval!);
          interval = null;

          setTimeout(() => {
            downloading = false;
            const success = Math.random() > 1;

            if (!success) {
              failed = true;
              error = "Error downloading content.";
              showSkeleton = false;
              hasProgress = false;
            } else {
              finished = true;
              showSkeleton = false;
              setTimeout(() => {
                progress = 0;
                url = "";
                finished = false;
                // hide preview when reset finishes
                hasPreview = false;
                hasProgress = false;
              }, 2000);
            }
          }, 500);
        }
      }, 300);
    }, 1000);
  }

  function cancel() {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
    if (skeletonTimeout) {
      clearTimeout(skeletonTimeout);
      skeletonTimeout = null;
    }
    downloading = false;
    showSkeleton = false;
    hasPreview = false;
    hasProgress = false;
    failed = true;
    error = "Download cancelled by user";
  }

  function dismiss() {
    error = "";
    progress = 0;
    failed = false;
    showSkeleton = false;
    hasPreview = false;
    hasProgress = false;
  }

  async function paste() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) url = text;
    } catch {
      error = "Failed to read clipboard";
    }
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key !== "Enter") return;
    if (downloading) return cancel();
    if (valid) download();
  }
</script>

<div class="min-h-screen flex items-center justify-center p-4 sm:p-6 lg:p-8">
  <div class="w-full max-w-2xl mx-auto space-y-6">
    <div class="text-center">
      <h1 class="text-4xl font-extrabold tracking-tight lg:text-5xl">
        YouTube Downloader
      </h1>
    </div>

    <div class="space-y-4">
      <div class="flex gap-2">
        <Button
          variant="outline"
          onclick={paste}
          aria-label="Paste from clipboard"
          disabled={downloading}
          class="px-3"
        >
          <Clipboard class="h-4 w-4" />
        </Button>

        <Input
          bind:value={url}
          onkeypress={handleKeyPress}
          placeholder="Paste YouTube link here..."
          disabled={downloading}
        />
      </div>

      <div class="flex justify-center">
        <ButtonGroup.Root>
          <Button
            variant={type === "video" ? "default" : "secondary"}
            onclick={() => (type = "video")}
            disabled={downloading}
          >
            Video
          </Button>

          <Button
            variant={type === "audio" ? "default" : "secondary"}
            onclick={() => (type = "audio")}
            disabled={downloading}
          >
            Audio
          </Button>
        </ButtonGroup.Root>
      </div>

      <div class="flex justify-center">
        <Button
          onclick={downloading ? cancel : download}
          variant={finished
            ? "default"
            : downloading
              ? "destructive"
              : "default"}
          disabled={(!valid && !downloading) || finished}
          class="w-full sm:w-auto sm:min-w-[200px]"
        >
          {finished ? "Finished" : downloading ? "Cancel" : "Download"}
        </Button>
      </div>
    </div>

    {#if showPreview}
      <div
        class="rounded-lg border bg-card text-card-foreground p-4"
        transition:slide={{ duration: 300 }}
      >
        {#key showSkeleton}
          {#if showSkeleton}
            <div class="flex gap-4" in:fade out:fade>
              <Skeleton class="w-40 h-24 rounded-md shrink-0" />

              <div class="flex flex-col justify-between flex-1 min-w-0">
                <Skeleton class="h-6 w-3/4 mb-2" />

                <div class="flex gap-2 flex-wrap">
                  <Skeleton class="h-6 w-20" />
                  <Skeleton class="h-6 w-20" />
                </div>
              </div>
            </div>
          {:else}
            <div class="flex gap-4" in:fade out:fade>
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/1280px-Image_created_with_a_mobile_phone.png"
                alt="Preview thumbnail"
                class="w-40 h-24 object-cover rounded-md shrink-0"
              />

              <div class="flex flex-col justify-between flex-1 min-w-0">
                <h3 class="text-2xl font-semibold truncate">Title</h3>

                <div class="flex gap-2 flex-wrap">
                  <Badge variant="secondary">Uploader</Badge>
                  <Badge variant="secondary">Duration</Badge>
                </div>
              </div>
            </div>
          {/if}
        {/key}
      </div>
    {/if}

    {#if showProgress}
      {#key hasProgress}
        <div in:fade out:fade>
          <Progress
            value={progress}
            class={failed
              ? "[&>div]:bg-red-600"
              : finished
                ? "[&>div]:bg-green-600"
                : ""}
          />
        </div>
      {/key}
    {/if}

    {#if showError}
      <div transition:slide={{ duration: 300 }}>
        <Alert.Root
          variant="destructive"
          class="flex items-center justify-between gap-4"
        >
          <div class="flex-1">
            <Alert.Title>Error</Alert.Title>
            <Alert.Description>{error}</Alert.Description>
          </div>
          <Button
            variant="outline"
            size="sm"
            class="text-foreground"
            onclick={dismiss}
          >
            OK
          </Button>
        </Alert.Root>
      </div>
    {/if}
  </div>
</div>

<div class="fixed bottom-3 right-3">
  <Button onclick={toggleMode} variant="outline" size="icon">
    <SunIcon
      class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all! dark:-rotate-90 dark:scale-0"
    />
    <MoonIcon
      class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all! dark:rotate-0 dark:scale-100"
    />
    <span class="sr-only">Toggle theme</span>
  </Button>
</div>
