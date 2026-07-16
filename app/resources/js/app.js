import Alpine from 'alpinejs';
import hljs from 'highlight.js/lib/core';
import bash from 'highlight.js/lib/languages/bash';
import shell from 'highlight.js/lib/languages/shell';
import yaml from 'highlight.js/lib/languages/yaml';
import json from 'highlight.js/lib/languages/json';

window.Alpine = Alpine;

hljs.registerLanguage('bash', bash);
hljs.registerLanguage('shell', shell);
hljs.registerLanguage('sh', shell);
hljs.registerLanguage('yaml', yaml);
hljs.registerLanguage('yml', yaml);
hljs.registerLanguage('json', json);

function wrapAndEnhanceCodeBlocks() {
    document.querySelectorAll('.markdown-content pre').forEach((pre) => {
        if (pre.dataset.enhanced === 'true') {
            return;
        }

        const block = pre.querySelector('code');
        if (!block) {
            return;
        }

        const classList = Array.from(block.classList);
        const languageClass = classList.find((className) => className.startsWith('language-'));
        let language = 'plaintext';

        if (languageClass) {
            language = languageClass.replace('language-', '') || 'plaintext';
            hljs.highlightElement(block);
        } else {
            const result = hljs.highlightAuto(block.textContent || '', ['bash', 'shell', 'yaml', 'json']);
            block.innerHTML = result.value;
            block.classList.add('hljs');
            if (result.language) {
                language = result.language;
                block.classList.add(`language-${result.language}`);
            }
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper relative bg-base-200 border border-base-300 rounded-lg overflow-hidden shadow-md my-4';

        const header = document.createElement('div');
        header.className = 'flex items-center justify-between bg-base-300 px-4 py-2';

        const langLabel = document.createElement('span');
        langLabel.className = 'text-xs font-mono font-semibold text-base-content/60';
        langLabel.textContent = language;

        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-code-btn btn btn-xs btn-ghost gap-1 hover:bg-base-100 transition-all';
        copyBtn.title = 'Copy code to clipboard';
        copyBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span class="copy-text text-xs">Copy</span>
        `;

        copyBtn.addEventListener('click', async function (e) {
            e.preventDefault();
            const code = block.textContent || '';

            try {
                await navigator.clipboard.writeText(code);
                const text = this.querySelector('.copy-text');
                const originalText = text.textContent;
                text.textContent = 'Copied!';
                this.classList.add('btn-success');
                setTimeout(() => {
                    text.textContent = originalText;
                    this.classList.remove('btn-success');
                }, 1800);
            } catch (error) {
                console.error('Failed to copy:', error);
            }
        });

        header.appendChild(langLabel);
        header.appendChild(copyBtn);

        pre.className = 'm-0 bg-transparent overflow-x-auto';
        pre.dataset.enhanced = 'true';

        const parent = pre.parentNode;
        if (!parent) {
            return;
        }

        parent.insertBefore(wrapper, pre);
        wrapper.appendChild(header);
        wrapper.appendChild(pre);
    });
}

function highlightMarkdownCodeBlocks() {
    wrapAndEnhanceCodeBlocks();
}

// Register Alpine component BEFORE starting
Alpine.data('flagSubmissionForm', () => ({
    flag: '',
    loading: false,
    message: '',
    messageType: 'info',
    scenarioSlug: '',

    async submitFlag() {
        if (!this.flag.trim()) {
            this.showMessage('Please enter a flag', 'error');
            return;
        }

        this.loading = true;
        this.message = '';

        try {
            const response = await fetch(`/scenarios/${this.scenarioSlug}/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
                },
                body: JSON.stringify({ flag: this.flag }),
            });

            const data = await response.json();

            if (data.success) {
                this.showMessage(data.message, 'success');
                this.flag = '';

                // Draw attention to the Next button
                const nextBtn = document.getElementById('next-scenario-btn');
                if (nextBtn) {
                    nextBtn.classList.remove('next-btn-pop');
                    void nextBtn.offsetWidth; // restart the animation if triggered again
                    nextBtn.classList.add('next-btn-pop');
                }

                // Reload to show updated flag count
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Flag submission error:', error);
            this.showMessage('An error occurred. Please try again.', 'error');
        } finally {
            this.loading = false;
        }
    },

    showMessage(msg, type = 'info') {
        this.message = msg;
        this.messageType = type;
        
        if (type === 'success') {
            setTimeout(() => {
                this.message = '';
            }, 3000);
        }
    },
}));

// Start Alpine
Alpine.start();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', highlightMarkdownCodeBlocks);
} else {
    highlightMarkdownCodeBlocks();
}
