<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import { Skeleton } from "$lib/components/ui/skeleton/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import * as ButtonGroup from "$lib/components/ui/button-group/index.js";
  import * as Popover from "$lib/components/ui/popover/index.js";
  import Clipboard from "@lucide/svelte/icons/clipboard-paste";
  import SunIcon from "@lucide/svelte/icons/sun";
  import MoonIcon from "@lucide/svelte/icons/moon";
  import Info from "@lucide/svelte/icons/info";
  import { slide, fade } from "svelte/transition";
  import { toggleMode } from "mode-watcher";

  type Status = "idle" | "preparing" | "downloading" | "finished" | "error";
  type ErrorType =
    | "fetch_failed"
    | "download_failed"
    | "user_cancelled"
    | "user_cancelled_preparing"
    | "clipboard_denied"
    | null;

  let url = $state("");
  let type = $state<"video" | "audio">("video");
  let progress = $state(0);
  let status = $state<Status>("idle");
  let errorType = $state<ErrorType>(null);
  let errorMessage = $state("");

  let timers = $state<{
    download: ReturnType<typeof setInterval> | null;
    skeleton: ReturnType<typeof setTimeout> | null;
    finished: ReturnType<typeof setTimeout> | null;
  }>({ download: null, skeleton: null, finished: null });

  const isValidUrl = $derived(
    url.trim().length > 0 &&
      (url.includes("youtube.com") || url.includes("youtu.be"))
  );
  const isActive = $derived(status === "preparing" || status === "downloading");
  const canInteract = $derived(status === "idle" || status === "error");

  const buttonLabel = $derived(
    status === "finished" ? "Finished" : isActive ? "Cancel" : "Download"
  );

  const showPreview = $derived(
    status !== "idle" &&
      !(
        status === "error" &&
        [
          "fetch_failed",
          "user_cancelled_preparing",
          "clipboard_denied",
        ].includes(errorType!)
      )
  );

  const showProgress = $derived(
    status !== "idle" &&
      !(status === "error" && errorType === "clipboard_denied")
  );

  const progressClass = $derived(
    status === "error"
      ? "[&>div]:bg-red-600"
      : status === "finished"
        ? "[&>div]:bg-green-600"
        : ""
  );

  function clearTimers() {
    if (timers.download) clearInterval(timers.download);
    if (timers.skeleton) clearTimeout(timers.skeleton);
    if (timers.finished) clearTimeout(timers.finished);
    timers = { download: null, skeleton: null, finished: null };
  }

  function reset(clearInput = false) {
    clearTimers();
    status = "idle";
    progress = 0;
    errorType = null;
    errorMessage = "";
    if (clearInput) url = "";
  }

  function setError(type: ErrorType, message: string) {
    clearTimers();
    status = "error";
    errorType = type;
    errorMessage = message;
  }

  function startDownload() {
    if (!isValidUrl) return;

    clearTimers();
    status = "preparing";
    progress = 0;
    errorType = null;
    errorMessage = "";

    timers.skeleton = setTimeout(() => {
      if (Math.random() < 0.1) {
        progress = 100;
        setError("fetch_failed", "Error occured while fetching content.");
        return;
      }

      status = "downloading";

      timers.download = setInterval(() => {
        progress += Math.random() * 10 + 2;

        if (progress >= 100) {
          progress = 100;
          clearInterval(timers.download!);

          setTimeout(() => {
            if (Math.random() > 0.2) {
              status = "finished";
              timers.finished = setTimeout(() => reset(true), 3000);
            } else {
              setError("download_failed", "Error while downloading content.");
            }
          }, 500);
        }
      }, 200);
    }, 1500);
  }

  function cancel() {
    const error =
      status === "preparing" ? "user_cancelled_preparing" : "user_cancelled";
    if (status === "preparing") progress = 100;
    setError(error, "Download cancelled.");
  }

  async function paste() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) url = text;
    } catch {
      setError("clipboard_denied", "Clipboard access denied.");
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Enter") {
      if (isActive) cancel();
      else if (canInteract && isValidUrl) startDownload();
    }
  }
</script>

<div
  class="min-h-screen flex items-center justify-center p-4 pb-32 sm:p-6 lg:p-8"
>
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
          size="icon"
          onclick={paste}
          aria-label="Paste from clipboard"
          disabled={!canInteract}
        >
          <Clipboard class="h-4 w-4" />
        </Button>

        <Input
          bind:value={url}
          onkeydown={handleKeydown}
          placeholder="Paste YouTube link here..."
          disabled={!canInteract}
        />
      </div>

      <div class="flex justify-center">
        <ButtonGroup.Root>
          <Button
            variant={type === "video" ? "default" : "secondary"}
            onclick={() => (type = "video")}
            disabled={!canInteract}
          >
            Video
          </Button>

          <Button
            variant={type === "audio" ? "default" : "secondary"}
            onclick={() => (type = "audio")}
            disabled={!canInteract}
          >
            Audio
          </Button>
        </ButtonGroup.Root>
      </div>

      <div class="flex justify-center">
        <Button
          onclick={isActive ? cancel : startDownload}
          variant={status === "finished"
            ? "default"
            : isActive
              ? "destructive"
              : "default"}
          disabled={status === "finished" || (canInteract && !isValidUrl)}
          class="w-full sm:w-auto sm:min-w-[200px]"
        >
          {buttonLabel}
        </Button>
      </div>
    </div>

    {#if showPreview}
      <div
        class="rounded-lg border bg-card text-card-foreground p-4"
        transition:slide
      >
        {#if status === "preparing"}
          <div class="flex gap-4" in:fade>
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
          <div class="flex gap-4" in:fade>
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
      </div>
    {/if}

    {#if showProgress}
      <div transition:fade>
        <Progress value={progress} class={progressClass} />
      </div>
    {/if}

    {#if status === "error"}
      <div transition:slide>
        <Alert.Root
          variant="destructive"
          class="flex items-center justify-between gap-4"
        >
          <div class="flex-1">
            <Alert.Title>Error</Alert.Title>
            <Alert.Description>{errorMessage}</Alert.Description>
          </div>
          <Button
            variant="secondary"
            size="sm"
            class="text-foreground"
            onclick={() => reset()}
          >
            OK
          </Button>
        </Alert.Root>
      </div>
    {/if}
  </div>
</div>

<div class="fixed bottom-3 right-3 flex gap-2">
  <Popover.Root>
    <Popover.Trigger
      class="inline-flex size-9 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium bg-secondary text-secondary-foreground shadow-xs hover:bg-secondary/80"
    >
      <Info class="h-4 w-4" />
      <span class="sr-only">Information</span>
    </Popover.Trigger>
    <Popover.Content class="text-sm" side="top" align="end">
      <p class="text-muted-foreground">
        Only download content you have permission to access. This FOSS project
        is licensed under
        <a
          href="https://www.gnu.org/licenses/gpl-3.0.en.html"
          target="_blank"
          rel="noopener noreferrer"
          class="underline hover:text-foreground">GPLv3</a
        >
        and provides no warranty. You can view the source code on
        <a
          href="https://github.com/mdonmez/ytw"
          target="_blank"
          rel="noopener noreferrer"
          class="underline hover:text-foreground">GitHub</a
        >. We do not collect any data.
      </p>
    </Popover.Content>
  </Popover.Root>

  <Button onclick={toggleMode} variant="secondary" size="icon">
    <SunIcon
      class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all! dark:-rotate-90 dark:scale-0"
    />
    <MoonIcon
      class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all! dark:rotate-0 dark:scale-100"
    />
    <span class="sr-only">Toggle theme</span>
  </Button>
</div>
