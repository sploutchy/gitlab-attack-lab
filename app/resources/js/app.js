import Alpine from 'alpinejs';

window.Alpine = Alpine;

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
