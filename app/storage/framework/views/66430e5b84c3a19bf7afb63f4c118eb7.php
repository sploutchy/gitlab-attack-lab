<?php $__env->startSection('title', 'GitLab Attack Lab - Home'); ?>

<?php $__env->startSection('content'); ?>
<div class="container mx-auto px-4 py-12">
    <!-- Welcome Section -->
    <div class="text-center mb-12">
        <h1 class="text-5xl font-bold mb-4">GitLab Attack Lab</h1>
        <p class="text-lg text-base-content/70 mb-6">
            Learn and practice GitLab CI/CD security misconfigurations through interactive scenarios
        </p>
        <div class="stats shadow">
            <div class="stat">
                <div class="stat-title">Total Scenarios</div>
                <div class="stat-value text-primary"><?php echo e(count($scenarios)); ?></div>
            </div>
            <div class="stat">
                <div class="stat-title">Difficulty Levels</div>
                <div class="stat-value text-secondary">3</div>
            </div>
        </div>
    </div>

    <!-- Scenarios Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <?php $__empty_1 = true; $__currentLoopData = $scenarios; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $scenario): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); $__empty_1 = false; ?>
            <a href="/scenarios/<?php echo e($scenario['slug']); ?>" class="card bg-base-200 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200">
                <div class="card-body">
                    <div class="flex items-start justify-between mb-2">
                        <h2 class="card-title text-lg"><?php echo e($scenario['title']); ?></h2>
                        <span class="badge <?php if($scenario['difficulty'] === 'beginner'): ?> badge-success <?php elseif($scenario['difficulty'] === 'intermediate'): ?> badge-warning <?php else: ?> badge-error <?php endif; ?>">
                            <?php echo e(ucfirst($scenario['difficulty'])); ?>

                        </span>
                    </div>
                    
                    <p class="text-sm text-base-content/70 mb-4">
                        <?php if(isset($scenario['flags'])): ?>
                            <strong><?php echo e(count($scenario['flags'])); ?></strong> flag<?php echo e(count($scenario['flags']) !== 1 ? 's' : ''); ?> to find
                        <?php else: ?>
                            No flags defined
                        <?php endif; ?>
                    </p>

                    <div class="card-actions justify-end">
                        <button class="btn btn-primary btn-sm">
                            Start Scenario →
                        </button>
                    </div>
                </div>
            </a>
        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); if ($__empty_1): ?>
            <div class="alert alert-info col-span-full">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <div>
                    <h3 class="font-bold">No scenarios available</h3>
                    <div class="text-sm">Please check your scenario files in <code>lab-config/scenarios/</code></div>
                </div>
            </div>
        <?php endif; ?>
    </div>

    <!-- Getting Started -->
    <div class="divider my-12"></div>
    
    <div class="bg-base-200 rounded-lg p-8">
        <h2 class="text-2xl font-bold mb-4">🎯 How to Use</h2>
        <ol class="list-decimal list-inside space-y-3">
            <li>Select a scenario from the list above</li>
            <li>Read the scenario description and objectives</li>
            <li>Follow the steps to find flags in the GitLab instance</li>
            <li>Submit flags using the form at the bottom of the scenario page</li>
            <li>Verify your flags and progress</li>
        </ol>
    </div>
</div>
<?php $__env->stopSection(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH /workspaces/gitlab-attack-lab/app/resources/views/index.blade.php ENDPATH**/ ?>