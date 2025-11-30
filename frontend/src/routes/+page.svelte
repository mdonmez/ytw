<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import * as ButtonGroup from "$lib/components/ui/button-group/index.js";
  import * as Popover from "$lib/components/ui/popover/index.js";
  import Clipboard from "@lucide/svelte/icons/clipboard-paste";
  import SunIcon from "@lucide/svelte/icons/sun";
  import MoonIcon from "@lucide/svelte/icons/moon";
  import Info from "@lucide/svelte/icons/info";
  import autoAnimate from "@formkit/auto-animate";
  import { toggleMode } from "mode-watcher";
  import { fade } from "svelte/transition";

  type Status = "idle" | "loading" | "started" | "error";

  // State
  let url = $state("");
  let type = $state<"video" | "audio">("video");
  let status = $state<Status>("idle");
  let errorMessage = $state("");
  let inputInvalid = $state(false);

  // Derived state
  const isValidUrl = $derived(
    url.trim() && (url.includes("youtube.com") || url.includes("youtu.be"))
  );
  const isProcessing = $derived(status === "loading" || status === "started");
  const buttonLabel = $derived(
    status === "loading"
      ? "Preparing"
      : status === "started"
        ? "Download Started"
        : "Download"
  );

  // Actions
  const resetState = (clearInput = false) => {
    status = "idle";
    errorMessage = "";
    inputInvalid = false;
    if (clearInput) url = "";
  };

  const handleDownload = () => {
    if (!isValidUrl) {
      inputInvalid = true;
      return;
    }

    status = "loading";
    errorMessage = "";
    inputInvalid = false;

    // Simulate download preparation (2 seconds)
    setTimeout(() => {
      status = "started";
      // Auto-reset after 3 seconds
      setTimeout(() => resetState(true), 3000);
    }, 2000);
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        url = text;
        if (url.trim()) {
          inputInvalid = false;
          if (isValidUrl) handleDownload();
        }
      }
    } catch {
      status = "error";
      errorMessage = "Clipboard access denied.";
    }
  };

  const handleInput = () => {
    if (inputInvalid) inputInvalid = false;
    if (status === "error") resetState();
  };

  const handleKeydown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !isProcessing && isValidUrl) handleDownload();
  };
</script>

<div
  class="min-h-screen flex items-center justify-center p-4 pb-32 sm:p-6 lg:p-8"
>
  <div
    class="w-full max-w-2xl mx-auto space-y-6"
    use:autoAnimate={{ easing: "ease-out" }}
  >
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-4xl font-extrabold tracking-tight lg:text-5xl">
        YouTube Downloader
      </h1>
    </div>

    <!-- Input Controls -->
    <div class="space-y-4">
      <div class="flex gap-2">
        <Button
          variant="outline"
          size="icon"
          onclick={handlePaste}
          aria-label="Paste from clipboard"
          disabled={isProcessing}
        >
          <Clipboard class="h-4 w-4" />
        </Button>
        <Input
          bind:value={url}
          oninput={handleInput}
          onkeydown={handleKeydown}
          placeholder="Paste YouTube link here..."
          disabled={isProcessing}
          aria-invalid={inputInvalid || undefined}
        />
      </div>

      <!-- Type Selection -->
      <div class="flex justify-center">
        <ButtonGroup.Root>
          <Button
            variant={type === "video" ? "default" : "secondary"}
            onclick={() => (type = "video")}
            disabled={isProcessing}
          >
            Video
          </Button>
          <Button
            variant={type === "audio" ? "default" : "secondary"}
            onclick={() => (type = "audio")}
            disabled={isProcessing}
          >
            Audio
          </Button>
        </ButtonGroup.Root>
      </div>

      <!-- Download Button -->
      <div class="flex justify-center">
        <Button
          onclick={handleDownload}
          disabled={isProcessing || !url.trim()}
          class="w-full sm:w-auto sm:min-w-[200px]"
        >
          {#key buttonLabel}
            <span in:fade={{ duration: 200 }}>{buttonLabel}</span>
          {/key}
        </Button>
      </div>
    </div>

    <!-- Error Alert: Rendered when status === "error" -->
    {#if status === "error"}
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
          onclick={() => resetState()}
        >
          OK
        </Button>
      </Alert.Root>
    {/if}
  </div>
</div>

<!-- Bottom Right Controls: Info & Theme Toggle -->
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
        Only download content you have permission to. This FOSS project is
        licensed under
        <a
          href="https://www.gnu.org/licenses/gpl-3.0.en.html"
          target="_blank"
          rel="noopener noreferrer"
          class="underline hover:text-foreground"
        >
          GPLv3
        </a>
        and provides no warranty. You can view the source code on
        <a
          href="https://github.com/mdonmez/ytw"
          target="_blank"
          rel="noopener noreferrer"
          class="underline hover:text-foreground"
        >
          GitHub
        </a>. We do not collect any data.
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
