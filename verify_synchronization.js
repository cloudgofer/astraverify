#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');

// Colors for output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
    magenta: '\x1b[35m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function logHeader(message) {
    console.log('\n' + '='.repeat(60));
    log(message, 'bright');
    console.log('='.repeat(60));
}

function logSection(message) {
    console.log('\n' + '-'.repeat(40));
    log(message, 'blue');
    console.log('-'.repeat(40));
}

function executeCommand(command) {
    try {
        return execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    } catch (error) {
        return error.stdout || error.message;
    }
}

function checkBranchStatus(branchName) {
    logSection(`Checking ${branchName} branch`);
    
    // Get current branch
    const currentBranch = executeCommand('git branch --show-current').trim();
    
    // Switch to the branch
    if (currentBranch !== branchName) {
        executeCommand(`git checkout ${branchName}`);
    }
    
    // Get latest commit
    const latestCommit = executeCommand('git log --oneline -1').trim();
    
    // Check if branch is up to date with origin
    const status = executeCommand('git status --porcelain');
    const isClean = status.trim() === '';
    
    // Get branch ahead/behind status
    const branchStatus = executeCommand(`git status --porcelain --branch`);
    const aheadMatch = branchStatus.match(/ahead (\d+)/);
    const behindMatch = branchStatus.match(/behind (\d+)/);
    
    const ahead = aheadMatch ? parseInt(aheadMatch[1]) : 0;
    const behind = behindMatch ? parseInt(behindMatch[1]) : 0;
    
    log(`Branch: ${branchName}`, 'cyan');
    log(`Latest Commit: ${latestCommit}`, 'cyan');
    log(`Working Directory Clean: ${isClean ? '✅ Yes' : '❌ No'}`, isClean ? 'green' : 'red');
    log(`Ahead of origin: ${ahead}`, ahead > 0 ? 'yellow' : 'green');
    log(`Behind origin: ${behind}`, behind > 0 ? 'red' : 'green');
    
    return {
        branch: branchName,
        latestCommit,
        isClean,
        ahead,
        behind,
        status: isClean && ahead === 0 && behind === 0 ? '✅ Synchronized' : '❌ Needs Attention'
    };
}

function checkConfigFiles() {
    logSection('Checking Configuration Files');
    
    const configFiles = [
        'frontend/src/config.local.js',
        'frontend/src/config.staging.js',
        'frontend/src/config.production.js',
        'frontend/src/config.js'
    ];
    
    const results = [];
    
    for (const file of configFiles) {
        if (fs.existsSync(file)) {
            const content = fs.readFileSync(file, 'utf8');
            const apiUrlMatch = content.match(/API_BASE_URL:\s*['"`]([^'"`]+)['"`]/);
            const appNameMatch = content.match(/APP_NAME:\s*['"`]([^'"`]+)['"`]/);
            
            results.push({
                file,
                exists: true,
                apiUrl: apiUrlMatch ? apiUrlMatch[1] : 'Not found',
                appName: appNameMatch ? appNameMatch[1] : 'Not found'
            });
            
            log(`✅ ${file}`, 'green');
            log(`   API URL: ${apiUrlMatch ? apiUrlMatch[1] : 'Not found'}`, 'cyan');
            log(`   App Name: ${appNameMatch ? appNameMatch[1] : 'Not found'}`, 'cyan');
        } else {
            results.push({
                file,
                exists: false,
                apiUrl: 'File not found',
                appName: 'File not found'
            });
            
            log(`❌ ${file} - File not found`, 'red');
        }
    }
    
    return results;
}

function checkVersionFile() {
    logSection('Checking Version Information');
    
    if (fs.existsSync('VERSION')) {
        const version = fs.readFileSync('VERSION', 'utf8').trim();
        log(`✅ VERSION file exists: ${version}`, 'green');
        return version;
    } else {
        log(`❌ VERSION file not found`, 'red');
        return null;
    }
}

function checkDeploymentScripts() {
    logSection('Checking Deployment Scripts');
    
    const scripts = [
        'deploy/deploy_local.sh',
        'deploy/deploy_staging.sh',
        'deploy/deploy_production.sh',
        'deploy/check_environment_status.sh',
        'deploy/sync_prod_with_stage.sh',
        'run_local.sh',
        'switch_config.sh'
    ];
    
    const results = [];
    
    for (const script of scripts) {
        if (fs.existsSync(script)) {
            const stats = fs.statSync(script);
            const isExecutable = (stats.mode & fs.constants.S_IXUSR) !== 0;
            
            results.push({
                script,
                exists: true,
                executable: isExecutable
            });
            
            log(`✅ ${script} ${isExecutable ? '(executable)' : '(not executable)'}`, isExecutable ? 'green' : 'yellow');
        } else {
            results.push({
                script,
                exists: false,
                executable: false
            });
            
            log(`❌ ${script} - Not found`, 'red');
        }
    }
    
    return results;
}

function checkTestFiles() {
    logSection('Checking Test Files');
    
    const testFiles = [
        'test_environment_differences.js',
        'test_production_environment.js',
        'test_stage_environment.js',
        'test_security_features.js',
        'verify_production_deployment.js'
    ];
    
    const results = [];
    
    for (const file of testFiles) {
        if (fs.existsSync(file)) {
            const stats = fs.statSync(file);
            results.push({
                file,
                exists: true,
                size: stats.size
            });
            
            log(`✅ ${file} (${stats.size} bytes)`, 'green');
        } else {
            results.push({
                file,
                exists: false,
                size: 0
            });
            
            log(`❌ ${file} - Not found`, 'red');
        }
    }
    
    return results;
}

function main() {
    logHeader('AstraVerify Environment Synchronization Verification');
    
    // Check all branches
    const branches = ['main', 'staging', 'develop'];
    const branchResults = [];
    
    for (const branch of branches) {
        const result = checkBranchStatus(branch);
        branchResults.push(result);
    }
    
    // Check configuration files
    const configResults = checkConfigFiles();
    
    // Check version file
    const version = checkVersionFile();
    
    // Check deployment scripts
    const scriptResults = checkDeploymentScripts();
    
    // Check test files
    const testResults = checkTestFiles();
    
    // Summary
    logHeader('Synchronization Summary');
    
    const allBranchesSynced = branchResults.every(r => r.status === '✅ Synchronized');
    const allConfigsExist = configResults.every(r => r.exists);
    const allScriptsExist = scriptResults.every(r => r.exists);
    const allTestsExist = testResults.every(r => r.exists);
    const versionExists = version !== null;
    
    log(`Branch Synchronization: ${allBranchesSynced ? '✅ Complete' : '❌ Incomplete'}`, allBranchesSynced ? 'green' : 'red');
    log(`Configuration Files: ${allConfigsExist ? '✅ Complete' : '❌ Incomplete'}`, allConfigsExist ? 'green' : 'red');
    log(`Deployment Scripts: ${allScriptsExist ? '✅ Complete' : '❌ Incomplete'}`, allScriptsExist ? 'green' : 'red');
    log(`Test Files: ${allTestsExist ? '✅ Complete' : '❌ Incomplete'}`, allTestsExist ? 'green' : 'red');
    log(`Version File: ${versionExists ? '✅ Complete' : '❌ Incomplete'}`, versionExists ? 'green' : 'red');
    
    const overallStatus = allBranchesSynced && allConfigsExist && allScriptsExist && allTestsExist && versionExists;
    
    console.log('\n' + '='.repeat(60));
    log(`OVERALL STATUS: ${overallStatus ? '✅ ALL ENVIRONMENTS SYNCHRONIZED' : '❌ SYNCHRONIZATION INCOMPLETE'}`, overallStatus ? 'green' : 'red');
    console.log('='.repeat(60));
    
    if (!overallStatus) {
        log('\nIssues to address:', 'yellow');
        
        if (!allBranchesSynced) {
            log('- Some branches are not synchronized with origin', 'red');
        }
        
        if (!allConfigsExist) {
            log('- Some configuration files are missing', 'red');
        }
        
        if (!allScriptsExist) {
            log('- Some deployment scripts are missing', 'red');
        }
        
        if (!allTestsExist) {
            log('- Some test files are missing', 'red');
        }
        
        if (!versionExists) {
            log('- Version file is missing', 'red');
        }
    } else {
        log('\n🎉 All environments are properly synchronized!', 'green');
        log('Ready for new development work.', 'green');
    }
    
    // Switch back to main branch
    executeCommand('git checkout main');
}

if (require.main === module) {
    main();
}

module.exports = {
    checkBranchStatus,
    checkConfigFiles,
    checkVersionFile,
    checkDeploymentScripts,
    checkTestFiles
};
