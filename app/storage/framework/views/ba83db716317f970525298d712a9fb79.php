<?php $__env->startSection('title', $scenario['title'] . ' - GitLab Attack Lab'); ?>

<?php $__env->startSection('content'); ?>
<div class="container mx-auto px-4 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Content -->
        <div class="lg:col-span-2">
            <!-- Header -->
            <div class="mb-8">
                <div class="flex items-center gap-4 mb-4">
                    <h1 class="text-4xl font-bold"><?php echo e($scenario['title']); ?></h1>
                    <span class="badge <?php echo e($difficultyColor); ?> badge-lg">
                        <?php echo e(ucfirst($scenario['difficulty'])); ?>

                    </span>
                </div>
                <a href="/" class="link link-primary text-sm">← Back to Scenarios</a>
            </div>

            <!-- Scenario Content (Markdown) -->
            <div class="prose prose-invert max-w-none bg-base-200 rounded-lg p-8 mb-8">
                <div class="markdown-content">
                    <?php echo $htmlContent; ?>

                </div>
            </div>

            <!-- Hints Accordion -->
            <?php if(isset($scenario['hints']) && count($scenario['hints']) > 0): ?>
            <div class="card bg-base-200 shadow-xl mb-8">
                <div class="card-body">
                    <h2 class="card-title mb-4">💡 Hints</h2>
                    <div class="space-y-2">
                        <?php $__currentLoopData = $scenario['hints']; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $index => $hint): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                        <div class="collapse collapse-arrow border border-base-300 bg-base-100">
                            <input type="checkbox" id="hint-<?php echo e($index); ?>" class="peer" />
                            <label for="hint-<?php echo e($index); ?>" class="collapse-title cursor-pointer font-medium text-sm">
                                <?php echo e($hint['title'] ?? "Hint " . ($index + 1)); ?>

                            </label>
                            <div class="collapse-content peer-checked:block hidden">
                                <div class="prose prose-invert max-w-none text-base-content/80 pt-2">
                                    <style>
                                        .solution-content ol, .hint-content ol { list-style-type: decimal !important; margin-left: 1.5rem !important; }
                                        .solution-content ol li, .hint-content ol li { margin-left: 0.5rem !important; }
                                        .solution-content ul, .hint-content ul { list-style-type: disc !important; margin-left: 1.5rem !important; }
                                        .solution-content ul li, .hint-content ul li { margin-left: 0.5rem !important; }
                                    </style>
                                    <div class="hint-content">
                                        <?php echo $hint['content']; ?>

                                    </div>
                                </div>
                            </div>
                        </div>
                        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
                    </div>
                </div>
            </div>
            <?php endif; ?>

            <!-- Flag Submission Form -->
            <div class="card bg-base-200 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title flex items-center gap-2">
                        🚩 Submit Flag
                        <span class="badge badge-primary">
                            <?php echo e(count($foundFlags)); ?>/<?php echo e(count($scenario['flags'])); ?> Found
                        </span>
                    </h2>

                    <div x-data="flagSubmissionForm()" 
                         x-init="scenarioSlug = '<?php echo e($scenario['slug']); ?>'"
                         class="mt-6 space-y-4">

                        <!-- Message Alert -->
                        <div x-show="message" 
                             :class="messageType === 'success' ? 'alert-success' : messageType === 'error' ? 'alert-error' : 'alert-info'"
                             class="alert flag-success">
                            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <span x-text="message"></span>
                        </div>

                        <!-- Flag Input -->
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Enter the flag you found:</span>
                            </label>
                            <input 
                                type="text" 
                                placeholder="flag{...}"
                                x-model="flag"
                                @keydown.enter="submitFlag()"
                                :disabled="loading"
                                class="input input-bordered w-full"
                            />
                            <label class="label">
                                <span class="label-text-alt text-xs text-base-content/50">
                                    The flag format is usually <code>flag{...}</code>
                                </span>
                            </label>
                        </div>

                        <!-- Submit Button -->
                        <button 
                            @click="submitFlag()"
                            :disabled="loading"
                            class="btn btn-primary w-full"
                        >
                            <span x-show="!loading">Submit Flag</span>
                            <span x-show="loading" class="loading loading-spinner loading-sm"></span>
                        </button>
                    </div>

                    <!-- Found Flags List -->
                    <?php if(count($foundFlags) > 0): ?>
                        <div class="mt-8 pt-8 border-t">
                            <h3 class="font-bold mb-4">✓ Flags Found</h3>
                            <div class="space-y-2">
                                <?php $__currentLoopData = $foundFlags; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $foundFlag): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                                    <div class="badge badge-success gap-2">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline w-4 h-4 stroke-current"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                        <?php echo e($foundFlag); ?>

                                    </div>
                                <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
                            </div>
                        </div>
                    <?php endif; ?>
                </div>
            </div>

            <!-- Solution Accordion -->
            <?php if(isset($scenario['solution'])): ?>
            <div class="card bg-base-200 shadow-xl mt-8">
                <div class="card-body">
                    <div class="collapse collapse-arrow border border-base-300 bg-base-100">
                        <input type="checkbox" id="solution-accordion" class="peer" />
                        <label for="solution-accordion" class="collapse-title cursor-pointer font-medium text-lg flex items-center gap-2">
                            💡 <?php echo e($scenario['solution']['title'] ?? 'Solution'); ?>

                        </label>
                        <div class="collapse-content peer-checked:block hidden">
                            <div class="prose prose-invert max-w-none text-base-content/80 pt-4">
                                <style>
                                    .solution-content ol, .hint-content ol { list-style-type: decimal !important; margin-left: 1.5rem !important; }
                                    .solution-content ol li, .hint-content ol li { margin-left: 0.5rem !important; }
                                    .solution-content ul, .hint-content ul { list-style-type: disc !important; margin-left: 1.5rem !important; }
                                    .solution-content ul li, .hint-content ul li { margin-left: 0.5rem !important; }
                                </style>
                                <div class="solution-content">
                                    <?php echo $scenario['solution']['content']; ?>

                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <?php endif; ?>
        </div>

        <!-- Sidebar -->
        <div class="lg:col-span-1 space-y-6">
            <!-- Flag List -->
            <div class="card bg-base-200 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-lg">Flags to Find</h2>
                    <div class="space-y-2 mt-4">
                        <?php $__empty_1 = true; $__currentLoopData = $scenario['flags']; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $index => $flag): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); $__empty_1 = false; ?>
                            <div class="flex items-center gap-2 p-2 bg-base-100 rounded">
                                <?php if(in_array($flag['name'] ?? "Flag {$index}", $foundFlags)): ?>
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-5 h-5 text-success"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                                <?php else: ?>
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 text-base-content/30 stroke-current"><circle cx="12" cy="12" r="10" stroke-width="2"/></svg>
                                <?php endif; ?>
                                <span class="text-sm">
                                    <?php echo e($flag['name'] ?? "Flag " . ($index + 1)); ?>

                                </span>
                            </div>
                        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); if ($__empty_1): ?>
                            <p class="text-sm text-base-content/50">No flags defined</p>
                        <?php endif; ?>
                    </div>
                </div>
            </div>

            <!-- Progress -->
            <div class="card bg-base-200 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-lg">Progress</h2>
                    <progress class="progress progress-primary w-full" value="<?php echo e(count($foundFlags)); ?>" max="<?php echo e(count($scenario['flags'])); ?>"></progress>
                    <p class="text-sm text-base-content/70 mt-2">
                        <?php echo e(count($foundFlags)); ?> of <?php echo e(count($scenario['flags'])); ?> flags found
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Update flag counter on flag found event
    window.addEventListener('flag-found', (event) => {
        location.reload();
    });
</script>
<?php $__env->stopSection(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH /workspaces/gitlab-attack-lab/app/resources/views/scenario.blade.php ENDPATH**/ ?>