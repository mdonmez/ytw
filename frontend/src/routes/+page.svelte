<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";

  import * as ButtonGroup from "$lib/components/ui/button-group/index.js";

  import Clipboard from "@lucide/svelte/icons/clipboard";
  import ImageIcon from "@lucide/svelte/icons/image";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { fade, slide } from "svelte/transition";
  import SunIcon from "@lucide/svelte/icons/sun";
  import MoonIcon from "@lucide/svelte/icons/moon";
  import { toggleMode } from "mode-watcher";

  // State variables
  let url = $state("");
  let downloadType = $state("video");
  let progress = $state(0);
  let isDownloading = $state(false);
  let isFinished = $state(false);
  let showPreview = $state(false);
  let isFailed = $state(false);
  let showError = $state(false);
  let errorMessage = $state("");
  // Derived validation state that updates in real time based on the `url` value
  // Derived validation state that updates in real time based on the `url` value
  let isValid = $state(false);
  $effect(() => {
    isValid =
      url.trim().length > 0 &&
      (url.includes("youtube.com") || url.includes("youtu.be"));
  });
  let downloadInterval: ReturnType<typeof setInterval> | null = null;

  // Mock preview data
  let previewData = $state({
    title: "Amazing Video Title - Full Tutorial",
    uploader: "TechChannel",
    duration: "15:30",
    thumbnail: "https://via.placeholder.com/300x200",
  });

  // Mock download function
  function handleDownload() {
    // Reset states
    // (clear previous failures)
    isFailed = false;
    showError = false;
    errorMessage = "";
    progress = 0;

    // Guard: do not proceed if URL isn't valid. Validation should be handled
    // in real-time and the button will be disabled until this returns true.
    if (!isValid) return;

    // Show preview
    showPreview = true;
    isDownloading = true;

    // Simulate progress
    downloadInterval = setInterval(() => {
      progress += Math.random() * 15 + 5; // Random increment between 5-20

      if (progress >= 100) {
        progress = 100;
        clearInterval(downloadInterval!);

        // Simulate download completion
        setTimeout(() => {
          isDownloading = false;

          // Random success/error for testing
          const success = Math.random() > 0.8; // 80% success rate

          if (!success) {
            isFailed = true;
            showError = true;
            errorMessage =
              "Error downloading content, check your input and try again.";
            progress = 0;
          } else {
            // Show finished state
            isFinished = true;

            // Reset after successful download
            setTimeout(() => {
              progress = 0;
              showPreview = false;
              url = "";
              isFinished = false;
            }, 2000);
          }
        }, 500);
      }
    }, 300);
  }

  // Handle Enter key in input
  function handleKeyPress(event: KeyboardEvent) {
    if (event.key !== "Enter") return;

    // When downloading, allow Enter to act as Cancel to match the button.
    if (isDownloading) return handleCancel();

    // Otherwise, only allow starting a download if the input is valid
    if (isValid) handleDownload();
  }

  // Handle cancel
  function handleCancel() {
    if (downloadInterval) {
      clearInterval(downloadInterval);
      downloadInterval = null;
    }
    isDownloading = false;
    progress = 0;
    showPreview = false;
    isFailed = true;
    showError = true;
    errorMessage = "Download cancelled by user";
  }

  async function handlePaste() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) url = text;
    } catch (e) {
      showError = true;
      errorMessage = "Failed to read clipboard";
    }
  }
</script>

<div
  class="min-h-screen w-full flex items-center justify-center p-4 sm:p-6 lg:p-8"
>
  <div class="w-full max-w-2xl mx-auto space-y-6">
    <!-- Header Section -->
    <div class="text-center space-y-2">
      <h1
        class="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl"
      >
        YouTube Downloader
      </h1>
    </div>

    <!-- Input Section -->
    <div class="space-y-4">
      <div class="w-full flex items-center gap-2">
        <Button
          variant="outline"
          size="default"
          onclick={handlePaste}
          aria-label="Paste from clipboard"
          disabled={isDownloading}
          class="h-9 px-3"
        >
          <Clipboard class="h-4 w-4" />
        </Button>

        <Input
          bind:value={url}
          onkeypress={handleKeyPress}
          placeholder="Paste YouTube link here..."
          class="flex-1"
          disabled={isDownloading}
        />
      </div>

      <!-- Download Type Selection -->
      <div class="flex justify-center">
        <ButtonGroup.Root>
          <Button
            variant={downloadType === "video" ? "default" : "secondary"}
            onclick={() => (downloadType = "video")}
            disabled={isDownloading}
          >
            Video
          </Button>

          <Button
            variant={downloadType === "audio" ? "default" : "secondary"}
            onclick={() => (downloadType = "audio")}
            disabled={isDownloading}
          >
            Audio
          </Button>
        </ButtonGroup.Root>
      </div>

      <!-- Unified Download/Cancel Button -->
      <div class="flex justify-center">
        <Button
          onclick={isDownloading ? handleCancel : handleDownload}
          variant={isFinished
            ? "default"
            : isDownloading
              ? "destructive"
              : "default"}
          disabled={(!isValid && !isDownloading) || isFinished}
          class="{isFinished
            ? 'bg-green-600 hover:bg-green-600 text-white'
            : ''} w-full sm:w-auto sm:min-w-[200px]"
        >
          {isFinished ? "Finished" : isDownloading ? "Cancel" : "Download"}
        </Button>
      </div>
    </div>

    <!-- removed standalone progress bar (now inside preview) -->

    {#if showPreview}
      <!-- Preview Section -->
      <div class="w-full" transition:slide={{ duration: 300 }}>
        <!-- Separator removed; keeping only the preview card to avoid line artifacts -->
        <div
          class="w-full rounded-lg border border-border bg-card min-h-[180px] flex flex-col p-4 gap-4 overflow-hidden"
        >
          <div class="w-1/3 flex items-center justify-center">
            {#if previewData.thumbnail}
              <img
                src={previewData.thumbnail}
                alt="Thumbnail"
                class="rounded max-h-[120px] w-full object-cover"
              />
            {:else}
              <div
                class="rounded bg-slate-900 w-full h-[120px] flex items-center justify-center text-muted-foreground"
              >
                <ImageIcon class="h-6 w-6" />
              </div>
            {/if}
          </div>
          <div class="flex-1 flex flex-col justify-center">
            <div class="flex items-center justify-between w-full">
              <span class="font-semibold text-lg truncate"
                >{previewData.title}</span
              >
              <div class="flex items-center gap-2 ml-4">
                <Badge variant="secondary">{previewData.uploader}</Badge>
                <Badge variant="secondary">{previewData.duration}</Badge>
              </div>
            </div>
          </div>

          {#if progress > 0}
            <div class="mt-auto w-full pt-2 pb-0">
              <div class="w-full rounded-b-md overflow-hidden">
                <Progress
                  value={progress}
                  variant={isFailed ? "destructive" : "primary"}
                  class="w-full"
                />
              </div>
            </div>
          {/if}
        </div>
      </div>
    {/if}
    {#if showError}
      <!-- Error Alert -->
      <div class="w-full" transition:slide={{ duration: 300 }}>
        <Alert.Root variant="destructive">
          <Alert.Title>Error</Alert.Title>
          <Alert.Description>
            {errorMessage}
          </Alert.Description>
        </Alert.Root>
      </div>
    {/if}
  </div>
</div>

<!-- Theme Toggle Button - Fixed Bottom Right -->
<div class="fixed bottom-6 right-6">
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
