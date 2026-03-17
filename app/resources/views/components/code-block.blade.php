@props(['language' => 'plaintext', 'code' => ''])

<div class="code-block-wrapper relative bg-base-200 border border-base-300 rounded-lg overflow-hidden shadow-md my-4" 
     data-code="{{ base64_encode($code) }}"
     data-language="{{ $language }}">
    <!-- Header with language label and copy button -->
    <div class="flex items-center justify-between bg-base-300 px-4 py-2">
        <span class="text-xs font-mono font-semibold text-base-content/60">{{ $language }}</span>
        <button class="copy-code-btn btn btn-xs btn-ghost gap-1" 
                title="Copy code to clipboard"
                data-code="{{ base64_encode($code) }}">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current copy-icon">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span class="copy-text text-xs">Copy</span>
        </button>
    </div>
    <!-- Code content -->
    <pre class="!m-0 !bg-transparent overflow-x-auto"><code class="language-{{ $language }}">{{ $code }}</code></pre>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.copy-code-btn');
    buttons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const encoded = this.getAttribute('data-code');
            const code = atob(encoded);
            
            try {
                await navigator.clipboard.writeText(code);
                const text = this.querySelector('.copy-text');
                const originalText = text.textContent;
                text.textContent = 'Copied!';
                
                setTimeout(() => {
                    text.textContent = originalText;
                }, 2000);
            } catch (error) {
                console.error('Failed to copy:', error);
            }
        });
    });
});
</script>

<style scoped>
.code-block-wrapper {
    font-size: 0.875rem;
}

.code-block-wrapper pre {
    padding: 1rem;
}

.code-block-wrapper code {
    line-height: 1.5;
}

.copy-code-btn {
    transition: all 0.2s ease;
}

.copy-code-btn:hover {
    @apply bg-base-100;
}
</style>
