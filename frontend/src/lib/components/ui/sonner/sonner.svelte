<script lang="ts">
  import {
    Toaster as Sonner,
    type ToasterProps as SonnerProps,
  } from "svelte-sonner";
  import { mode } from "mode-watcher";

  let { ...restProps }: SonnerProps = $props();
</script>

<Sonner
  theme={mode.current}
  class="toaster group"
  style="--normal-bg: var(--color-popover); --normal-text: var(--color-popover-foreground); --normal-border: var(--color-border);"
  {...restProps}
/>

<style>
  /* Ensure error toasts use the project's destructive color */
  :global(.toaster [data-type="error"]) {
    background: var(--color-destructive) !important;
    color: white !important;
    border-color: var(--color-destructive) !important;
  }

  :global(.toaster [data-type="error"] svg) {
    color: white !important;
  }
</style>
